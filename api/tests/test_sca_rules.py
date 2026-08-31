"""SCA 룰 12종 + Semgrep 러너 + 0322 표 5-1 매트릭스."""

import io
import json
import shutil
import zipfile
from pathlib import Path

import pytest

from app.engine.deps_npm import parse_npm_deps
from app.engine.deps_python import parse_python_deps
from app.engine.deps_types import Dependency
from app.engine.imports_py import extract_python_imports
from app.engine.sbom import build_sbom
from app.engine.sca_rules import evaluate_sca_rules, matrix_0322
from app.engine.semgrep_runner import extract_js_imports, run_semgrep, semgrep_available

semgrep_required = pytest.mark.skipif(
    not semgrep_available(), reason="semgrep 바이너리 없음 — 이미지 안에서 실행할 것")


def _row(**kw) -> dict:
    base = dict(validation_tool="AnsimCode", supplier="PyPI", author=None,
                component_name="flask", version="2.0.1", unique_id="pkg:pypi/flask@2.0.1",
                component_hash="sha256:aaa", license_name="BSD-3-Clause",
                license_usage="동적 참조", vulnerability_db=None, relationship="direct",
                release_date=None, cve_ids=None, cvss_base=None, cvss_impact=None,
                cvss_exploitability=None, cvss_null_reason=None, cvss_severity=None,
                ecosystem="pypi")
    return {**base, **kw}


def _dep(**kw) -> Dependency:
    base = dict(ecosystem="pypi", name="flask", version="2.0.1", declared_in="requirements.txt",
                is_pinned=True, integrity=None, relationship="direct",
                registry_source=True, vendored_path=None, in_lock=True)
    return Dependency(**{**base, **kw})


def _ids(findings) -> set[str]:
    return {f.rule_id for f in findings}


# ── SCA-01 미선언 의존성 ─────────────────────────────────────────────────────

def test_undeclared_dependency_py(tmp_path):
    (tmp_path / "requirements.txt").write_text("flask==2.0.1\n")
    (tmp_path / "main.py").write_text("import flask\nimport requests\nimport os\n")
    deps = parse_python_deps(tmp_path)
    findings = evaluate_sca_rules(deps, build_sbom(deps, tmp_path),
                                  extract_python_imports(tmp_path), set(), tmp_path)
    sca01 = [f for f in findings if f.rule_id == "SCA-01"]
    assert any("requests" in f.evidence for f in sca01)
    assert not any("flask" in f.evidence for f in sca01)     # 선언된 것은 갭이 아니다
    assert all(f.status == "confirmed" for f in findings)    # G3: SCA는 전부 confirmed


# ── SCA-02·04: OSV 결과 기반 ────────────────────────────────────────────────

def test_known_cve_and_unpatched(tmp_path):
    row = _row(version="0.12", unique_id="pkg:pypi/flask@0.12",
               cve_ids=["CVE-2018-1000656"], cvss_base=9.8, cvss_severity="critical",
               vulnerability_db=[{"id": "GHSA-562c-5r94-xh97", "source": "OSV", "fixed": "0.12.3"}])
    findings = evaluate_sca_rules([], [row], set(), set(), tmp_path)
    sca02 = next(f for f in findings if f.rule_id == "SCA-02")
    assert sca02.severity == "critical" and "CVE-2018-1000656" in sca02.evidence
    sca04 = next(f for f in findings if f.rule_id == "SCA-04")
    assert "0.12.3" in sca04.evidence


def test_patched_version_produces_no_sca04(tmp_path):
    row = _row(version="0.12.5", cve_ids=["CVE-2018-1000656"],
               vulnerability_db=[{"id": "GHSA-x", "source": "OSV", "fixed": "0.12.3"}])
    assert "SCA-04" not in _ids(evaluate_sca_rules([], [row], set(), set(), tmp_path))


# ── SCA-05 장기 미갱신 ──────────────────────────────────────────────────────

def test_stale_component(tmp_path):
    findings = evaluate_sca_rules([], [_row(release_date="2015-01-01")], set(), set(), tmp_path)
    sca05 = next(f for f in findings if f.rule_id == "SCA-05")
    assert sca05.severity == "low"


# ── SCA-06·07·08·09 ────────────────────────────────────────────────────────

def test_vendored_without_notice(tmp_path):
    findings = evaluate_sca_rules([], [_row(license_usage="복제·고지 없음")], set(), set(), tmp_path)
    assert "SCA-06" in _ids(findings)


def test_agpl_service_warning(tmp_path):
    row = _row(component_name="mongo-tools", license_name="AGPL-3.0")
    findings = evaluate_sca_rules([], [row], set(), set(), tmp_path)
    f = next(f for f in findings if f.rule_id == "SCA-07")
    assert "서비스" in f.evidence and f.status == "confirmed"


def test_unknown_license_and_missing_hash(tmp_path):
    findings = evaluate_sca_rules([], [_row(license_name=None, component_hash=None)],
                                  set(), set(), tmp_path)
    assert {"SCA-08", "SCA-09"} <= _ids(findings)


# ── SCA-10·11·12: 선언 기반 ─────────────────────────────────────────────────

def test_nonregistry_source(tmp_path):
    findings = evaluate_sca_rules([_dep(registry_source=False, name="leftpad")], [],
                                  set(), set(), tmp_path)
    assert "SCA-10" in _ids(findings)


def test_unpinned_without_lock(tmp_path):
    (tmp_path / "requirements.txt").write_text("requests>=2.0\n")
    deps = parse_python_deps(tmp_path)
    findings = evaluate_sca_rules(deps, build_sbom(deps, tmp_path), set(), set(), tmp_path)
    sca11 = next(f for f in findings if f.rule_id == "SCA-11")
    assert sca11.status == "confirmed" and "requests" in sca11.evidence


def test_pinned_or_locked_has_no_sca11(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"express": "^4.18.0"}}))
    (tmp_path / "package-lock.json").write_text(json.dumps({
        "lockfileVersion": 3,
        "packages": {"node_modules/express": {"version": "4.18.2", "integrity": "sha512-A"}}}))
    deps = parse_npm_deps(tmp_path)
    findings = evaluate_sca_rules(deps, build_sbom(deps, tmp_path), set(), set(), tmp_path)
    assert "SCA-11" not in _ids(findings) and "SCA-12" not in _ids(findings)


def test_vendored_component_is_not_lock_mismatch(tmp_path):
    """vendored 복제본은 lock 대상이 아니다 — SCA-06·10만 나오고 11·12는 나오지 않는다."""
    vendored = _dep(ecosystem="npm", name="leftpad", version=None, declared_in="app/vendor",
                    is_pinned=False, registry_source=False, vendored_path="app/vendor/leftpad",
                    in_lock=False)
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {}}))
    (tmp_path / "package-lock.json").write_text(json.dumps({"lockfileVersion": 3, "packages": {}}))
    ids = _ids(evaluate_sca_rules([vendored], [], set(), set(), tmp_path))
    assert "SCA-10" in ids and "SCA-11" not in ids and "SCA-12" not in ids


def test_manifest_lock_mismatch(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps(
        {"dependencies": {"express": "^4.18.0", "ghost-pkg": "^1.0.0"}}))
    (tmp_path / "package-lock.json").write_text(json.dumps({
        "lockfileVersion": 3,
        "packages": {"node_modules/express": {"version": "4.18.2", "integrity": "sha512-A"}}}))
    deps = parse_npm_deps(tmp_path)
    findings = evaluate_sca_rules(deps, build_sbom(deps, tmp_path), set(), set(), tmp_path)
    sca12 = [f for f in findings if f.rule_id == "SCA-12"]
    assert len(sca12) == 1 and "ghost-pkg" in sca12[0].evidence


# ── 0322 §5.1.2 표 5-1 매트릭스 ──────────────────────────────────────────────

def test_matrix_0322_open_source():
    rows = [_row(cve_ids=["CVE-2018-1000656"]), _row(component_name="x", license_name="AGPL-3.0")]
    m = matrix_0322("오픈소스", rows)
    assert m["standard_ref"].startswith("TTAK.KO-11.0322")
    names = {f["name"]: f["component_count"] for f in m["risk_factors"]}
    assert set(names) == {"라이선스 위반", "취약점 전파", "업데이트 중단"}
    assert names["취약점 전파"] == 1 and names["라이선스 위반"] == 1


def test_matrix_0322_binary_and_self_developed():
    assert {f["name"] for f in matrix_0322("바이너리", [])["risk_factors"]} == {"출처 불명", "검증 불가"}
    assert {f["name"] for f in matrix_0322("자체개발", [])["risk_factors"]} == {"자체 결함 관리"}


# ── Semgrep 러너 ────────────────────────────────────────────────────────────

@semgrep_required
def test_semgrep_js_import_collection(tmp_path):
    (tmp_path / "a.js").write_text(
        'import express from "express";\n'
        'import "./local.js";\n'
        'const _ = require("lodash");\n'
        'const fs = require("fs");\n'
        'import { x } from "@scope/pkg/sub";\n')
    assert extract_js_imports(tmp_path) == {"express", "lodash", "@scope/pkg"}


@semgrep_required
def test_semgrep_handles_empty_and_broken_sources(tmp_path):
    (tmp_path / "empty.js").write_text("")
    (tmp_path / "broken.js").write_text("function ( { unbalanced\n")
    from app.engine.semgrep_runner import js_imports_rule_path
    assert run_semgrep(tmp_path, [str(js_imports_rule_path())]) == []      # 예외 없이 빈 결과
    assert extract_js_imports(tmp_path) == set()


def test_run_semgrep_without_config_is_noop(tmp_path):
    assert run_semgrep(tmp_path, [str(tmp_path / "nope.yaml")]) == []


# ── M3 게이트 E2E: 취약 버전 fixture → SCA-02 + KISA 교차(SCA-03) ─────────────

def _vulnerable_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        # Django 핀은 KISA 제품명 교차(SCA-03)를 태우기 위한 것이다 — 실데이터 스냅샷의
        # 보안공지 제목에 Django가 있고, flask·lodash CVE는 배포본에 없다.
        z.writestr("app/requirements.txt", "flask==0.12\nrequests>=2.0\nDjango==3.2.12\n")
        z.writestr("app/main.py", "import flask\nimport boto3\n")
        z.writestr("app/package.json", json.dumps({"dependencies": {"lodash": "4.17.15"}}))
        z.writestr("app/vendor/leftpad/index.js", "module.exports = 1;\n")
    return buf.getvalue()


def _osv_stub():
    from app.engine.osv import OsvResult, VulnInfo

    async def _stub(purls, transport=None):
        vulns = {}
        for purl in purls:
            if purl.lower().startswith("pkg:pypi/django"):
                vulns[purl] = [VulnInfo(
                    id="GHSA-2gwj-7jmv-h26r", cve_ids=["CVE-2022-28346"],
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    severity="critical", fixed_version="3.2.13")]
            elif purl.startswith("pkg:pypi/flask"):
                vulns[purl] = [VulnInfo(
                    id="GHSA-562c-5r94-xh97", cve_ids=["CVE-2018-1000656"],
                    cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    severity="critical", fixed_version="0.12.3")]
            elif purl.startswith("pkg:npm/lodash"):
                vulns[purl] = [VulnInfo(
                    id="GHSA-p6mc-m468-83gg", cve_ids=["CVE-2020-8203"],
                    cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:H/A:N",
                    severity="high", fixed_version="4.17.19")]
        return OsvResult(vulns=vulns, incomplete=False)

    return _stub


@pytest.mark.asyncio
async def test_pipeline_produces_expected_sca_findings(client, monkeypatch):
    from app.db import SessionLocal
    from app.models import Finding, Scan

    monkeypatch.setattr("app.engine.pipeline.query_osv", _osv_stub())
    r = await client.post("/api/scans", files={"file": ("v.zip", _vulnerable_zip(), "application/zip")})
    sid = r.json()["scan_id"]
    assert (await client.get(f"/api/scans/{sid}")).json()["status"] == "done"

    with SessionLocal() as db:
        rules = {f.rule_id for f in db.query(Finding).filter(Finding.scan_id == sid).all()}
        scan = db.get(Scan, sid)
    # SCA-02(CVE)·03(국내 보안공지)·04(패치 미적용)·06(vendored 고지 없음)
    # ·08(라이선스 불명)·09(해시 부재)·10(vendored 비레지스트리)·11(버전 미고정)
    assert {"SCA-02", "SCA-03", "SCA-04", "SCA-06", "SCA-08", "SCA-09", "SCA-10", "SCA-11"} <= rules
    if shutil.which("semgrep"):
        assert "SCA-01" in rules                       # boto3 미선언 (Python ast 경로)
    assert scan.report_json["matrix_0322"]["supply_chain_class"] == "오픈소스"


@pytest.mark.asyncio
async def test_report_json_matrix_present_for_empty_repo(client, monkeypatch):
    from app.db import SessionLocal
    from app.models import Scan
    from app.engine.osv import OsvResult

    async def _empty(purls, transport=None):
        return OsvResult(vulns={}, incomplete=False)

    monkeypatch.setattr("app.engine.pipeline.query_osv", _empty)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/README.md", "hi\n")
    r = await client.post("/api/scans", files={"file": ("e.zip", buf.getvalue(), "application/zip")})
    sid = r.json()["scan_id"]
    assert (await client.get(f"/api/scans/{sid}")).json()["status"] == "done"
    with SessionLocal() as db:
        matrix = db.get(Scan, sid).report_json["matrix_0322"]
    assert matrix["supply_chain_class"] == "자체개발"
    assert [f["name"] for f in matrix["risk_factors"]] == ["자체 결함 관리"]


def test_repo_rules_dir_has_js_import_rule():
    from app.engine.semgrep_runner import js_imports_rule_path
    assert Path(js_imports_rule_path()).is_file()


# ── 레지스트리 보강 → SCA-05·SCA-07 (이슈 #33) ──────────────────────────────

def _issue33_zip() -> bytes:
    """벤치마크 §3.1과 같은 형태 — 선언형 PyPI 의존성만으로 SCA-05·07을 태운다."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/requirements.txt", "six==1.10.0\nPyMuPDF\n")
        z.writestr("app/main.py", "import six\n")
    return buf.getvalue()


def _registry_stub(metadata_by_name: dict, incomplete: bool = False):
    from app.engine.registry import RegistryResult

    async def _stub(queries, transport=None):
        return RegistryResult(
            metadata={q.key: metadata_by_name[q.name.lower()]
                      for q in queries if q.name.lower() in metadata_by_name},
            incomplete=incomplete)

    return _stub


async def _empty_osv(purls, transport=None):
    from app.engine.osv import OsvResult
    return OsvResult(vulns={}, incomplete=False)


@pytest.mark.asyncio
async def test_pipeline_registry_metadata_fires_sca05_and_sca07(client, monkeypatch):
    from app.db import SessionLocal
    from app.engine.registry import ComponentMetadata
    from app.models import Finding, Scan

    monkeypatch.setattr("app.engine.pipeline.query_osv", _empty_osv)
    monkeypatch.setattr("app.engine.pipeline.query_registry", _registry_stub({
        "six": ComponentMetadata(license_name=None, release_date="2015-10-05"),
        "pymupdf": ComponentMetadata(license_name="AGPL-3.0", release_date="2026-06-01"),
    }))
    r = await client.post("/api/scans", files={"file": ("i33.zip", _issue33_zip(), "application/zip")})
    sid = r.json()["scan_id"]
    assert (await client.get(f"/api/scans/{sid}")).json()["status"] == "done"

    with SessionLocal() as db:
        findings = db.query(Finding).filter(Finding.scan_id == sid).all()
        scan = db.get(Scan, sid)
    by_rule = {}
    for f in findings:
        by_rule.setdefault(f.rule_id, []).append(f.evidence)
    assert any("2015-10-05" in e for e in by_rule.get("SCA-05", []))       # six 장기 미갱신
    assert any("AGPL-3.0" in e for e in by_rule.get("SCA-07", []))         # PyMuPDF 서비스 카피레프트
    sca08 = " / ".join(by_rule.get("SCA-08", []))
    assert "PyMuPDF" not in sca08                   # 라이선스가 채워졌으니 SCA-08 억제
    assert "six" in sca08                           # 라이선스 없는 six는 여전히 SCA-08
    factors = {f["name"]: f["component_count"]
               for f in scan.report_json["matrix_0322"]["risk_factors"]}
    assert factors["업데이트 중단"] >= 1 and factors["라이선스 위반"] >= 1
    assert scan.report_json["registry_incomplete"] is False
    assert "registry@" in scan.vuln_db_snapshot_date


@pytest.mark.asyncio
async def test_pipeline_registry_does_not_overwrite_local_license(client, monkeypatch):
    from app.db import SessionLocal
    from app.engine.registry import ComponentMetadata
    from app.models import SbomComponent

    monkeypatch.setattr("app.engine.pipeline.query_osv", _empty_osv)
    monkeypatch.setattr("app.engine.pipeline.query_registry", _registry_stub({
        "lodash": ComponentMetadata(license_name="Apache-2.0", release_date="2020-01-01"),
        "leftpad": ComponentMetadata(license_name="SSPL-1.0", release_date="2019-01-01"),
    }))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/package.json", json.dumps({"dependencies": {"lodash": "4.17.15"}}))
        z.writestr("app/vendor/leftpad/package.json", json.dumps({"name": "leftpad", "license": "MIT"}))
        z.writestr("app/vendor/leftpad/LICENSE", "MIT License\n")
    r = await client.post("/api/scans", files={"file": ("l.zip", buf.getvalue(), "application/zip")})
    sid = r.json()["scan_id"]
    assert (await client.get(f"/api/scans/{sid}")).json()["status"] == "done"

    with SessionLocal() as db:
        rows = db.query(SbomComponent).filter(SbomComponent.scan_id == sid).all()
        licenses = {c.component_name: c.license_name for c in rows}
    # vendored 승격분은 조회 대상이 아니다 — 로컬 판정(MIT)이 스텁 값(SSPL-1.0)으로 덮이지 않는다.
    assert licenses["leftpad"] == "MIT"
    # 선언형(레지스트리 실체 있음)은 레지스트리 값으로 채워진다.
    assert licenses["lodash"] == "Apache-2.0"


@pytest.mark.asyncio
async def test_pipeline_registry_incomplete_flag_reaches_report(client, monkeypatch):
    from app.db import SessionLocal
    from app.models import Scan

    monkeypatch.setattr("app.engine.pipeline.query_osv", _empty_osv)
    monkeypatch.setattr("app.engine.pipeline.query_registry", _registry_stub({}, incomplete=True))
    r = await client.post("/api/scans", files={"file": ("d.zip", _issue33_zip(), "application/zip")})
    sid = r.json()["scan_id"]
    assert (await client.get(f"/api/scans/{sid}")).json()["status"] == "done"   # 장애≠실패
    with SessionLocal() as db:
        report = db.get(Scan, sid).report_json
    assert report["registry_incomplete"] is True
    assert report["provenance"]["registry_lookup_incomplete"] is True


@pytest.mark.asyncio
async def test_pipeline_registry_disabled_skips_lookup(client, monkeypatch):
    from app.config import settings
    from app.db import SessionLocal
    from app.models import Scan

    async def _boom(queries, transport=None):
        raise AssertionError("registry_lookup_enabled=False인데 조회가 호출됐다")

    monkeypatch.setattr(settings, "registry_lookup_enabled", False)
    monkeypatch.setattr("app.engine.pipeline.query_osv", _empty_osv)
    monkeypatch.setattr("app.engine.pipeline.query_registry", _boom)
    r = await client.post("/api/scans", files={"file": ("o.zip", _issue33_zip(), "application/zip")})
    sid = r.json()["scan_id"]
    assert (await client.get(f"/api/scans/{sid}")).json()["status"] == "done"
    with SessionLocal() as db:
        report = db.get(Scan, sid).report_json
    assert "registry_incomplete" not in report
