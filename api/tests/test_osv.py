"""OSV 클라이언트 — 전부 httpx.MockTransport로 모킹한다(외부 호출 없음).

실호출 스모크는 docker compose 환경에서 별도로 수행한다(네트워크 필요).
"""

import httpx
import pytest

from app.engine.osv import OSV_BATCH_SIZE, query_osv

FLASK = "pkg:pypi/flask@0.12"
REQUESTS = "pkg:pypi/requests@2.31.0"

VULN_DETAIL = {
    "id": "GHSA-562c-5r94-xh97",
    "aliases": ["CVE-2018-1000656", "SNYK-PYTHON-FLASK-451637"],
    "severity": [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}],
    "affected": [{"package": {"ecosystem": "PyPI", "name": "flask"},
                  "ranges": [{"type": "ECOSYSTEM",
                              "events": [{"introduced": "0"}, {"fixed": "0.12.3"}]}]}],
}


def _handler(*, batch_status=200, detail_exc=None, batch_exc=None, calls=None):
    def handle(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        if request.url.path == "/v1/querybatch":
            if batch_exc:
                raise batch_exc
            return httpx.Response(batch_status, json={"results": [
                {"vulns": [{"id": "GHSA-562c-5r94-xh97"}]},
                {},
            ]})
        if detail_exc:
            raise detail_exc
        return httpx.Response(200, json=VULN_DETAIL)
    return httpx.MockTransport(handle)


@pytest.mark.asyncio
async def test_query_osv_maps_vulns_cve_and_fixed_version():
    res = await query_osv([FLASK, REQUESTS], transport=_handler())
    assert res.incomplete is False
    assert REQUESTS not in res.vulns                      # 취약점 없는 컴포넌트는 키 없음
    v = res.vulns[FLASK][0]
    assert v.id == "GHSA-562c-5r94-xh97"
    assert v.cve_ids == ["CVE-2018-1000656"]              # CVE- 프리픽스만 (aliases 필터)
    assert v.cvss_vector.startswith("CVSS:3.1/")
    assert v.severity == "critical"
    assert v.fixed_version == "0.12.3"
    assert v.source == "OSV"


@pytest.mark.asyncio
async def test_detail_timeout_keeps_partial_result():
    res = await query_osv([FLASK], transport=_handler(detail_exc=httpx.ReadTimeout("timeout")))
    assert res.incomplete is True                          # "일부 미대조" 표시 (TDD §6)
    v = res.vulns[FLASK][0]                                # 부분 결과는 유지된다
    assert v.id == "GHSA-562c-5r94-xh97" and v.cvss_vector is None
    assert v.severity == "unknown"


@pytest.mark.asyncio
async def test_querybatch_failure_marks_incomplete():
    res = await query_osv([FLASK], transport=_handler(batch_exc=httpx.ConnectTimeout("down")))
    assert res.incomplete is True and res.vulns == {}


@pytest.mark.asyncio
async def test_batch_is_split_by_1000():
    calls: list[str] = []
    purls = [f"pkg:pypi/p{i}@1.0" for i in range(OSV_BATCH_SIZE + 5)]
    await query_osv(purls, transport=_handler(calls=calls))
    assert sum(1 for u in calls if u.endswith("/v1/querybatch")) == 2


@pytest.mark.asyncio
async def test_empty_input_does_not_call_api():
    calls: list[str] = []
    res = await query_osv([], transport=_handler(calls=calls))
    assert res.vulns == {} and res.incomplete is False and calls == []
