"""Task 21 — 재진단 rescan + 발견 diff 3분류 (TDD §4.7 유스케이스 3)."""
import io
import uuid
import zipfile
from types import SimpleNamespace

import pytest

from app.engine.diff import diff_findings


def f(rule_id, file_path, line, fid=None):
    return SimpleNamespace(id=fid, rule_id=rule_id, file_path=file_path, line=line,
                           severity="medium", status="confirmed")


def keys(rows):
    return {(r["rule_id"], r["file_path"], r["line"]) for r in rows}


def test_diff_three_way():
    prev = [f("SEC-01", "a.py", 3), f("AUX-01", "b.py", 9)]
    curr = [f("AUX-01", "b.py", 9), f("P9", None, None)]
    d = diff_findings(prev, curr)
    assert keys(d["resolved"]) == {("SEC-01", "a.py", 3)}
    assert keys(d["remaining"]) == {("AUX-01", "b.py", 9)}
    assert keys(d["new"]) == {("P9", None, None)}


def test_diff_empty_previous_makes_everything_new():
    d = diff_findings([], [f("AUX-02", "s.py", 1)])
    assert not d["resolved"] and not d["remaining"] and len(d["new"]) == 1


def test_diff_identical_scans_are_all_remaining():
    rows = [f("AUX-02", "s.py", 1), f("P9", None, None)]
    d = diff_findings(rows, rows)
    assert len(d["remaining"]) == 2 and not d["resolved"] and not d["new"]


# ── rescan API 통합 ──────────────────────────────────────────────────────────

# v1은 클라우드 자격증명(SEC-04 critical) 포함 → 위험. v2는 그것만 제거한다.
# 어떤 저장소든 P8(접속기록)·P9(처리방침)이 confirmed로 남으므로 v2의 도달 등급은 주의다.
_WITH_SECRET = 'AWS_KEY = "AKIA2E0QW3RTYU7BNMZX"\nDEBUG = False\n'
_WITHOUT_SECRET = 'AWS_KEY = os.environ["AWS_KEY"]\nDEBUG = False\n'


def _zip_of(source: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/settings.py", source)
    return buf.getvalue()


@pytest.fixture
def zip_v1():
    return _zip_of(_WITH_SECRET)


@pytest.fixture
def zip_v2():
    return _zip_of(_WITHOUT_SECRET)


async def _scan_state(client, scan_id):
    r = await client.get(f"/api/scans/{scan_id}")
    assert r.status_code == 200
    return r.json()


@pytest.mark.asyncio
async def test_rescan_links_previous_and_reports_grade_change(client, zip_v1, zip_v2):
    first = await client.post("/api/scans",
                              files={"file": ("v1.zip", zip_v1, "application/zip")})
    first_id = first.json()["scan_id"]
    assert (await _scan_state(client, first_id))["grade"] == "위험"   # SEC-04 confirmed

    second = await client.post(f"/api/scans/{first_id}/rescan",
                               files={"file": ("v2.zip", zip_v2, "application/zip")})
    assert second.status_code == 202
    second_id = second.json()["scan_id"]

    state = await _scan_state(client, second_id)
    assert state["grade"] == "주의"                        # 시크릿 제거 반영
    cmp_ = state["previous_comparison"]
    assert cmp_["previous_grade"] == "위험" and cmp_["grade"] == "주의"
    assert cmp_["fingerprint_changed"] is True             # 지문 변경 = 실제 수정 증명
    assert cmp_["diff"]["resolved_count"] >= 1
    assert any(r["rule_id"].startswith("SEC-") for r in cmp_["diff"]["resolved"])
    assert cmp_["diff"]["new_count"] == 0

    from app.db import SessionLocal
    from app.models import Scan
    with SessionLocal() as db:
        assert str(db.get(Scan, uuid.UUID(second_id)).previous_scan_id) == first_id


@pytest.mark.asyncio
async def test_rescan_same_zip_reports_fingerprint_unchanged(client, zip_v1):
    first = await client.post("/api/scans",
                              files={"file": ("v1.zip", zip_v1, "application/zip")})
    first_id = first.json()["scan_id"]

    again = await client.post(f"/api/scans/{first_id}/rescan",
                              files={"file": ("v1.zip", zip_v1, "application/zip")})
    state = await _scan_state(client, again.json()["scan_id"])

    assert state["previous_comparison"]["fingerprint_changed"] is False   # 코드 미변경
    assert state["previous_comparison"]["diff"]["remaining_count"] >= 1
    # #13 회귀: 동일 zip 재진단에서 해결·신규가 생기면 diff 키가 흔들린 것이다
    assert state["previous_comparison"]["diff"]["resolved_count"] == 0
    assert state["previous_comparison"]["diff"]["new_count"] == 0
    assert state["grade"] == state["previous_comparison"]["previous_grade"]


@pytest.mark.asyncio
async def test_rescan_zip_requires_reupload(client, zip_v1):
    first = await client.post("/api/scans",
                              files={"file": ("v1.zip", zip_v1, "application/zip")})
    first_id = first.json()["scan_id"]

    r = await client.post(f"/api/scans/{first_id}/rescan")
    assert r.status_code == 422                            # zip은 재업로드 필수


@pytest.mark.asyncio
async def test_rescan_git_needs_no_body(client, monkeypatch, database):
    """git은 body 없이 동일 source_ref로 재clone한다."""
    monkeypatch.setattr("app.routes.scans.run_scan", lambda scan_id: None)
    from app.db import SessionLocal
    from app.models import Scan

    origin = Scan(source_type="git", source_ref="https://example.com/a.git",
                  status="done", grade="안심", content_fingerprint="c1",
                  fingerprint_type="git_commit")
    with SessionLocal() as db:
        db.add(origin)
        db.commit()
        origin_id = origin.id

    r = await client.post(f"/api/scans/{origin_id}/rescan")
    assert r.status_code == 202
    with SessionLocal() as db:
        new = db.get(Scan, uuid.UUID(r.json()["scan_id"]))
        assert new.source_type == "git"
        assert new.source_ref == "https://example.com/a.git"
        assert new.previous_scan_id == origin_id


@pytest.mark.asyncio
async def test_rescan_404_for_unknown_scan(client, database):
    r = await client.post(f"/api/scans/{uuid.uuid4()}/rescan")
    assert r.status_code == 404
