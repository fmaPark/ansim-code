"""verification/ 스크립트의 순수 함수 검증 (계획 Task 26 Step 3·4).

측정 스크립트는 저장소 루트의 `verification/`에 있고 API 이미지에는 굽지 않는다.
컨테이너 안에서 `-v "$PWD:/work"` 없이 pytest를 돌리면 경로가 없으므로 그때는 skip한다.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_VERIFICATION_DIR = Path(__file__).resolve().parents[2] / "verification"


def _load(module_name: str):
    path = _VERIFICATION_DIR / f"{module_name}.py"
    if not path.is_file():
        pytest.skip(f"{path}가 마운트되지 않았다 (호스트 또는 -v \"$PWD:/work\" 필요)")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def md():
    return _load("measure_detection")


@pytest.fixture(scope="module")
def ci():
    return _load("check_invariants")


# ── 오라클 키 (명세 §1.1) ────────────────────────────────────────────────────
def test_component_key_rules_use_package_not_file(md):
    """SCA-01~09는 file=None이라 (rule_id, file)로 매칭하면 전부 미검출로 집계된다."""
    entry = {"rule_id": "SCA-02", "package": "Django", "verdict": "confirmed"}
    finding = {"rule_id": "SCA-02", "file_path": None,
               "evidence": "Django 3.2.12 — 알려진 취약점 CVE-2022-28346 (CVSS Base 9.8)"}
    assert md.oracle_key(entry) == md.finding_key(finding)


def test_component_name_parsed_from_evidence(md):
    assert md.package_of({"rule_id": "SCA-09", "evidence": "flask-cors (버전 미상) — lock 파일이 없거나"}) \
        == "flask-cors"
    assert md.package_of({"rule_id": "SCA-01",
                          "evidence": "미선언 의존성: 코드가 `left-pad`을(를) import 하지만"}) == "left-pad"
    assert md.package_of({"rule_id": "SCA-02", "evidence": "형식이 다른 문자열"}) is None


def test_declared_in_rules_key_on_manifest_path(md):
    entry = {"rule_id": "SCA-12", "file": "vulnerable/package.json"}
    finding = {"rule_id": "SCA-12", "file_path": "vulnerable/package.json", "evidence": "mysql2 —"}
    assert md.oracle_key(entry) == md.finding_key(finding)


def test_repo_wide_rules_key_on_rule_id_only(md):
    entry = {"rule_id": "P8", "file": None}
    finding = {"rule_id": "P8", "file_path": None, "evidence": "로깅 설정 전무"}
    assert md.oracle_key(entry) == md.finding_key(finding) == ("P8",)


def test_scope_filter_keeps_fileless_findings(md):
    """사후 필터가 repo-wide·컴포넌트 키 룰을 걸러내면 그 룰이 전부 미검출이 된다."""
    assert md.in_benchmark_scope({"rule_id": "SCA-02", "file_path": None})
    assert md.in_benchmark_scope({"rule_id": "P8", "file_path": None})
    assert md.in_benchmark_scope({"rule_id": "SEC-01", "file_path": "vulnerable/a.py"})
    assert not md.in_benchmark_scope({"rule_id": "SEC-01", "file_path": "tools/other.py"})


# ── fail-closed (명세 §5.1 B6 · 계획 Step 4) ──────────────────────────────────
def test_sentinel_blocks_measurement(md):
    oracle = {"positives": [
        {"rule_id": "SCA-08", "package": "TBD", "verdict": "confirmed"},
        {"rule_id": "SEC-01", "file": "vulnerable/x.py", "line": "<기입>", "verdict": "confirmed"},
    ]}
    problems = md.sentinel_violations(oracle)
    assert len(problems) == 2
    assert any("SCA-08" in p for p in problems)


def test_missing_line_field_blocks_measurement(md):
    oracle = {"positives": [{"rule_id": "SEC-01", "file": "vulnerable/x.py", "verdict": "confirmed"}]}
    assert md.sentinel_violations(oracle)


def test_declared_in_rules_need_no_line(md):
    oracle = {"positives": [{"rule_id": "SCA-10", "file": "vulnerable/requirements.txt",
                             "verdict": "confirmed"}]}
    assert md.sentinel_violations(oracle) == []


def test_complete_oracle_passes(md):
    oracle = {"positives": [
        {"rule_id": "SEC-01", "file": "vulnerable/x.py", "line": 7, "verdict": "confirmed"},
        {"rule_id": "P7", "file": "vulnerable/admin.js", "line": None, "verdict": "confirmed"},
        {"rule_id": "P8", "file": None, "verdict": "confirmed"},
        {"rule_id": "SCA-08", "package": "somelib", "verdict": "confirmed"},
    ]}
    assert md.sentinel_violations(oracle) == []


# ── 집계 (명세 §5.1) ─────────────────────────────────────────────────────────
def _oracle():
    return {"positives": [
        {"rule_id": "SEC-01", "file": "vulnerable/secrets.py", "line": 3, "verdict": "confirmed"},
        {"rule_id": "AUX-03", "file": "vulnerable/server.js", "line": 6, "verdict": "confirmed"},
        {"rule_id": "SCA-09", "package": "django", "verdict": "confirmed"},
        {"rule_id": "P8", "file": None, "verdict": "confirmed"},
    ]}


def test_measure_counts_hits_and_misses(md):
    findings = [
        {"rule_id": "SEC-01", "file_path": "vulnerable/secrets.py", "status": "confirmed",
         "evidence": "****"},
        {"rule_id": "SCA-09", "file_path": None, "status": "confirmed",
         "evidence": "Django 3.2.12 — lock 파일이 없거나"},
        {"rule_id": "P8", "file_path": None, "status": "confirmed", "evidence": "로깅 전무"},
    ]
    result = md.measure(_oracle(), findings, clean_file_count=10)
    assert result["per_rule"]["SEC-01"]["hit"] == 1
    assert result["per_rule"]["SCA-09"]["hit"] == 1
    assert result["per_rule"]["AUX-03"] == {"expected": 1, "hit": 0,
                                            "missed": ["vulnerable/server.js"]}


def test_bundle_firing_is_not_a_false_positive(md):
    """대표 키잉 + 다발 허용 — 같은 룰의 추가 발화는 부가 발견이지 오탐이 아니다(§5.1)."""
    findings = [
        {"rule_id": "SCA-09", "file_path": None, "status": "confirmed",
         "evidence": "Django 3.2.12 — lock 파일이 없거나"},
        {"rule_id": "SCA-09", "file_path": None, "status": "confirmed",
         "evidence": "six 1.10.0 — lock 파일이 없거나"},
    ]
    result = md.measure(_oracle(), findings, clean_file_count=10)
    assert result["per_rule"]["SCA-09"]["hit"] == 1
    assert result["false_positives"] == []
    assert [e["where"] for e in result["extras"]] == ["six"]


def test_clean_confirmed_is_a_false_positive(md):
    findings = [{"rule_id": "SEC-01", "file_path": "clean/config_example.py",
                 "status": "confirmed", "evidence": "****"}]
    result = md.measure(_oracle(), findings, clean_file_count=10)
    assert len(result["false_positives"]) == 1
    assert result["extras"] == []


def test_repo_wide_rules_excluded_from_fpr(md):
    """P8·P9·P10은 clean/에 음성을 둘 수 없어 FPR 분자에서 빠진다(§1.2)."""
    findings = [{"rule_id": "P10", "file_path": "clean/models_ok.py", "status": "confirmed",
                 "evidence": "모델 존재 & 삭제 로직 전무"}]
    assert md.measure(_oracle(), findings, clean_file_count=10)["false_positives"] == []


def test_review_needed_is_not_a_false_positive(md):
    findings = [{"rule_id": "P2", "file_path": "clean/x.py", "status": "review_needed",
                 "evidence": "…"}]
    assert md.measure(_oracle(), findings, clean_file_count=10)["false_positives"] == []


# ── 불변식 검사 (명세 §1.3) ──────────────────────────────────────────────────
def _benchmark(tmp_path: Path) -> Path:
    root = tmp_path / "bench"
    (root / "vulnerable").mkdir(parents=True)
    (root / "clean").mkdir()
    (root / "vulnerable/requirements.txt").write_text("flask-login==0.6.2\nrequests==2.28.0\n",
                                                      encoding="utf-8")
    (root / "vulnerable/admin_routes.py").write_text(
        '@app.route("/admin/users")\ndef admin_users():\n    return []\n', encoding="utf-8")
    (root / "vulnerable/admin.js").write_text(
        'app.get("/admin", (req, res) => res.json([]));\n', encoding="utf-8")
    (root / "vulnerable/third_party.py").write_text(
        'import requests\nrequests.post("https://x", json={"phone": 1})\n', encoding="utf-8")
    (root / "clean/admin_ok.py").write_text(
        'from flask_login import login_required\n\n@login_required\ndef ok():\n    return []\n',
        encoding="utf-8")
    return root


def test_clean_benchmark_passes_invariants(ci, tmp_path):
    assert ci.check(_benchmark(tmp_path)) == []


@pytest.mark.parametrize("rel,content,expected", [
    ("vulnerable/logger.py", "import logging\n", "P8"),
    ("vulnerable/route.py", 'app.route("/privacy")\n', "P9"),
    ("vulnerable/cleanup.py", "# purge old rows\n", "P10"),
    ("vulnerable/undeclared.py", "import numpy\n", "SCA-01"),
    ("clean/leak.py", 'import requests\nrequests.post("u", json={"email": 1})\n', "P4"),
])
def test_invariant_violations_are_caught(ci, tmp_path, rel, content, expected):
    root = _benchmark(tmp_path)
    (root / rel).write_text(content, encoding="utf-8")
    violations = ci.check(root)
    assert violations, f"{rel}의 {expected} 마스킹을 잡지 못했다"
    assert any(expected in v for v in violations)


def test_auth_word_in_vulnerable_admin_is_caught(ci, tmp_path):
    root = _benchmark(tmp_path)
    (root / "vulnerable/admin_routes.py").write_text(
        'from flask_login import login_required\n@app.route("/admin/users")\ndef a(): return []\n',
        encoding="utf-8")
    assert any("P7 마스킹" in v for v in ci.check(root))


def test_clean_admin_without_auth_is_caught(ci, tmp_path):
    """clean/admin_ok.py는 인증 단어가 있어야 P7 음성이 된다 — 없으면 오탐 케이스로 뒤집힌다."""
    root = _benchmark(tmp_path)
    (root / "clean/admin_ok.py").write_text('@app.route("/admin/reports")\ndef r(): return []\n',
                                            encoding="utf-8")
    assert any("P7 음성 무효" in v for v in ci.check(root))


def test_intended_undeclared_imports_are_allowed(ci, tmp_path):
    root = _benchmark(tmp_path)
    (root / "vulnerable/undeclared_py.py").write_text("import redis\n", encoding="utf-8")
    (root / "vulnerable/undeclared_import.js").write_text(
        'const leftPad = require("left-pad");\n', encoding="utf-8")
    assert ci.check(root) == []
