"""Task 20 — 조직 요구사항 통합 체크리스트 (0414 §7.1~7.3 조직·물리 + 0259 §10)."""
import uuid

import pytest

from app.report.checklist import CHECKLIST


def test_checklist_has_at_least_12_items_with_refs():
    assert len(CHECKLIST) >= 12
    assert all(item["standard_ref"] for item in CHECKLIST)
    assert all(item["question"] and item["category"] for item in CHECKLIST)
    assert len({item["id"] for item in CHECKLIST}) == len(CHECKLIST)


def test_checklist_covers_both_standards():
    refs = " ".join(item["standard_ref"] for item in CHECKLIST)
    assert "TTAK.KO-12.0414" in refs      # §7.1 관리적·§7.2 접근통제·§7.3 조직·물리
    assert "TTAK.KO-11.0259" in refs      # §10 취약점 관리 조직
    assert all(section in refs for section in ("§7.1", "§7.2", "§7.3", "§10"))


@pytest.mark.asyncio
async def test_checklist_endpoint(client, small_zip):
    r = await client.post("/api/scans",
                          files={"file": ("app.zip", small_zip, "application/zip")})
    scan_id = r.json()["scan_id"]

    res = await client.get(f"/api/scans/{scan_id}/checklist")
    assert res.status_code == 200
    body = res.json()
    assert len(body["items"]) >= 12
    assert body["disclaimer"]


@pytest.mark.asyncio
async def test_checklist_404_for_unknown_scan(client, database):
    res = await client.get(f"/api/scans/{uuid.uuid4()}/checklist")
    assert res.status_code == 404
