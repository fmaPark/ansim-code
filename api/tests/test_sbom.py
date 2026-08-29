import io
import json
import zipfile
from pathlib import Path

import pytest

from app.engine.deps_types import Dependency
from app.engine.sbom import build_sbom, classify_supply_chain, detect_vendored


def _zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


async def _scan_zip(client, payload: bytes) -> tuple[str, dict]:
    r = await client.post("/api/scans", files={"file": ("a.zip", payload, "application/zip")})
    assert r.status_code == 202
    sid = r.json()["scan_id"]
    return sid, (await client.get(f"/api/scans/{sid}")).json()


def _dep(**kw):
    base = dict(ecosystem="pypi", name="flask", version="2.0.1", declared_in="requirements.txt",
                is_pinned=True, integrity=None, relationship="direct",
                registry_source=True, vendored_path=None)
    return Dependency(**{**base, **kw})


def test_15_attributes_all_present(tmp_path):
    comp = build_sbom([_dep()], tmp_path)[0]
    for key in ["validation_tool", "supplier", "author", "component_name", "version", "unique_id",
                "component_hash", "license_name", "license_usage", "vulnerability_db", "relationship",
                "release_date", "cve_ids", "cvss_base", "cvss_severity"]:
        assert key in comp                       # 0309 §5.2 15속성 키 전수
    assert comp["unique_id"] == "pkg:pypi/flask@2.0.1"
    assert comp["license_usage"] == "동적 참조"   # 매니페스트 선언 (§6.9)


def test_vendored_without_license_is_no_notice(tmp_path):
    v = tmp_path / "vendor" / "leftpad"
    v.mkdir(parents=True)
    (v / "index.js").write_text("x")
    comp = build_sbom([_dep(ecosystem="npm", name="leftpad", version=None,
                            declared_in="vendor", vendored_path="vendor/leftpad")], tmp_path)[0]
    assert comp["license_usage"] == "복제·고지 없음"   # §6.8·§6.9 — vendored & LICENSE 부재


def test_vendored_with_license_is_file_copy(tmp_path):
    v = tmp_path / "vendor" / "leftpad"
    v.mkdir(parents=True)
    (v / "index.js").write_text("x")
    (v / "LICENSE").write_text("MIT License\n")
    assert detect_vendored(tmp_path) == {"vendor/leftpad": True}
    comp = build_sbom([_dep(ecosystem="npm", name="leftpad", version=None,
                            declared_in="vendor", vendored_path="vendor/leftpad")], tmp_path)[0]
    assert comp["license_usage"] == "파일단위 복제"
    assert comp["license_name"] == "MIT"


def test_supply_chain_classification(tmp_path):
    assert classify_supply_chain([], tmp_path) == "자체개발"
    assert classify_supply_chain([_dep()], tmp_path) == "오픈소스"
    (tmp_path / "native.so").write_bytes(b"\x7fELF")
    assert classify_supply_chain([_dep()], tmp_path) == "바이너리"


def test_scoped_npm_purl(tmp_path):
    comp = build_sbom([_dep(ecosystem="npm", name="@scope/pkg", version="1.2.3")], Path(tmp_path))[0]
    assert comp["unique_id"] == "pkg:npm/%40scope/pkg@1.2.3"


# ── M2 게이트: fixture 저장소 → GET /sbom 통합 ────────────────────────────────

@pytest.mark.asyncio
async def test_sbom_endpoint_covers_both_ecosystems(client):
    payload = _zip({
        "app/requirements.txt": "flask==2.0.1\nrequests>=2.0\n",
        "app/main.py": "import flask\n",
        "app/package.json": json.dumps({"dependencies": {"express": "^4.18.0"}}),
        "app/package-lock.json": json.dumps({
            "lockfileVersion": 3,
            "packages": {"node_modules/express": {"version": "4.18.2", "integrity": "sha512-AAA"}}}),
    })
    sid, status = await _scan_zip(client, payload)
    assert status["status"] == "done"

    body = (await client.get(f"/api/scans/{sid}/sbom")).json()
    assert body["generated_by"] == "AnsimCode"
    assert body["supply_chain_class"] == "오픈소스"
    names = {c["component_name"] for c in body["components"]}
    assert {"flask", "requests", "express"} <= names
    ecosystems = {c["ecosystem"] for c in body["components"]}
    assert ecosystems == {"pypi", "npm"}
    express = next(c for c in body["components"] if c["component_name"] == "express")
    assert express["unique_id"] == "pkg:npm/express@4.18.2"
    assert express["component_hash"] == "sha512-AAA"
    for c in body["components"]:                      # 15속성 키는 언제나 전부 출력
        for key in ["validation_tool", "supplier", "author", "component_name", "version",
                    "unique_id", "component_hash", "license_name", "license_usage",
                    "vulnerability_db", "relationship", "release_date", "cve_ids",
                    "cvss_base", "cvss_severity"]:
            assert key in c


@pytest.mark.asyncio
async def test_broken_package_json_still_completes_with_marker(client):
    payload = _zip({"app/package.json": "{not valid json",
                    "app/requirements.txt": "flask==2.0.1\n"})
    sid, status = await _scan_zip(client, payload)
    assert status["status"] == "done"                 # 파서 하나가 스캔을 죽이지 않는다
    body = (await client.get(f"/api/scans/{sid}/sbom")).json()
    assert any(m["kind"] == "npm_manifest_unparsable" for m in body["parse_markers"])
    assert {c["component_name"] for c in body["components"]} == {"flask"}


@pytest.mark.asyncio
async def test_empty_repo_is_self_developed(client):
    sid, status = await _scan_zip(client, _zip({"app/README.md": "hello\n"}))
    assert status["status"] == "done"
    body = (await client.get(f"/api/scans/{sid}/sbom")).json()
    assert body["components"] == [] and body["supply_chain_class"] == "자체개발"
