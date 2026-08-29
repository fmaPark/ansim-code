"""Task 12 — gitleaks 통합 (SEC-01~05 매핑·allowlist·exit 코드 규약).

실바이너리 테스트는 gitleaks가 있을 때만 돈다(이미지에는 동봉 — Task 1 Dockerfile).
바이너리가 없는 환경에서도 러너 로직(명령 조립·exit 코드·리포트 파싱·rule_id 매핑)은
subprocess 경계를 스텁해 전부 검증한다.
"""
import json
import shutil
import subprocess

import pytest

from app.engine.gitleaks_runner import RawSecret, _map_rule_id, _parse_report, run_gitleaks

HAS_GITLEAKS = shutil.which("gitleaks") is not None


# ── 실바이너리 (docker 이미지 안에서 검증) ──────────────────────────────────

@pytest.mark.skipif(not HAS_GITLEAKS, reason="gitleaks 바이너리 없음 — docker compose run api pytest로 검증")
def test_hardcoded_key_detected_placeholder_ignored(tmp_path):
    (tmp_path / "config.py").write_text(
        'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'          # 탐지 대상(기본 룰) — EXAMPLE이지만 형식 유효
        'API_KEY = "your-api-key-here"\n')            # allowlist 제외 대상
    hits = run_gitleaks(tmp_path)
    assert any(h.rule_id == "SEC-04" for h in hits)
    assert not any("your-api-key" in h.match for h in hits)


@pytest.mark.skipif(not HAS_GITLEAKS, reason="gitleaks 바이너리 없음 — docker compose run api pytest로 검증")
def test_comment_secret_detected(tmp_path):
    (tmp_path / "db.py").write_text("# prod db password = Sup3rSecret99\nx=1\n")
    assert any(h.rule_id == "SEC-02" for h in run_gitleaks(tmp_path))


# ── rule_id 매핑 (계획 Task 12 Interfaces 표 그대로) ─────────────────────────

def test_rule_id_mapping():
    assert _map_rule_id("aws-access-token") == "SEC-04"
    assert _map_rule_id("gcp-service-account") == "SEC-04"
    assert _map_rule_id("azure-connection-string") == "SEC-04"
    assert _map_rule_id("ansim-comment-secret") == "SEC-02"
    assert _map_rule_id("ansim-envfile") == "SEC-03"
    assert _map_rule_id("ansim-kr-rrn") == "SEC-05"
    assert _map_rule_id("ansim-kr-phone") == "SEC-05"
    assert _map_rule_id("ansim-kr-account") == "SEC-05"
    assert _map_rule_id("generic-api-key") == "SEC-01"   # 기본 룰 나머지 → SEC-01


def test_parse_report_entries():
    entries = [{"RuleID": "ansim-kr-rrn", "File": "a.py", "StartLine": 3,
                "Secret": "9001011234567", "Match": "rrn = 9001011234567"}]
    hits = _parse_report(entries)
    assert hits == [RawSecret("SEC-05", "a.py", 3, "9001011234567", "rrn = 9001011234567")]


# ── subprocess 경계 스텁 (exit 0/1 정상 · 그 외 예외 — G2: 원문 비로깅) ──────

def _stub_gitleaks(monkeypatch, returncode, findings):
    calls = {}

    def fake_run(cmd, **kw):
        calls["cmd"] = cmd
        report = cmd[cmd.index("-r") + 1]
        with open(report, "w") as f:
            json.dump(findings, f)
        return subprocess.CompletedProcess(cmd, returncode, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


def test_exit_1_means_findings(tmp_path, monkeypatch):
    calls = _stub_gitleaks(monkeypatch, 1, [
        {"RuleID": "aws-access-token", "File": "c.py", "StartLine": 1,
         "Secret": "AKIAIOSFODNN7EXAMPLE", "Match": 'AWS_KEY = "AKIA..."'}])
    hits = run_gitleaks(tmp_path)
    assert [h.rule_id for h in hits] == ["SEC-04"]
    # 명령 규약: detect --no-git -s {root} -c {toml} -f json -r {out}
    cmd = calls["cmd"]
    assert cmd[0] == "gitleaks" and "detect" in cmd and "--no-git" in cmd
    assert str(tmp_path) in cmd and any(str(c).endswith("ansim.toml") for c in cmd)


def test_exit_0_means_clean(tmp_path, monkeypatch):
    _stub_gitleaks(monkeypatch, 0, [])
    assert run_gitleaks(tmp_path) == []


def test_other_exit_raises_without_secret_leak(tmp_path, monkeypatch, caplog):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 2, stdout=b"", stderr=b"config parse error")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError):
        run_gitleaks(tmp_path)
    assert "Sup3rSecret" not in caplog.text   # G2: 어떤 경로에서도 시크릿 원문 비로깅
