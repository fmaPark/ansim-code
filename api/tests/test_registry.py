"""레지스트리 클라이언트 — 전부 httpx.MockTransport로 모킹한다(외부 호출 없음).

실호출 스모크는 docker compose 환경에서 별도로 수행한다(네트워크 필요).
"""

import httpx
import pytest

from app.engine.registry import RegistryQuery, query_registry
from app.engine.sbom import normalize_license

AGPL_TEXT = ("GNU AFFERO GENERAL PUBLIC LICENSE\nVersion 3, 19 November 2007\n"
             + "본문 " * 100)   # 128자 초과 전문 blob

SIX_PINNED = RegistryQuery(key="pkg:pypi/six@1.10.0", ecosystem="pypi",
                           name="six", version="1.10.0")
PYMUPDF_LATEST = RegistryQuery(key="pkg:pypi/pymupdf", ecosystem="pypi",
                               name="PyMuPDF", version=None)


def _pypi_body(*, license_expression=None, license=None, classifiers=None, uploads=None):
    return {
        "info": {"license_expression": license_expression, "license": license,
                 "classifiers": classifiers or []},
        "urls": [{"upload_time_iso_8601": u} for u in (uploads or [])],
    }


def _handler(routes: dict, *, calls=None, exc_paths=()):
    """routes: {url.path: json body}. exc_paths의 경로는 타임아웃을 일으킨다."""
    def handle(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        if request.url.path in exc_paths:
            raise httpx.ReadTimeout("timeout")
        body = routes.get(request.url.path)
        if body is None:
            return httpx.Response(404, json={"message": "Not Found"})
        return httpx.Response(200, json=body)
    return httpx.MockTransport(handle)


@pytest.mark.asyncio
async def test_pypi_pinned_license_expression_and_date_normalized():
    routes = {"/pypi/six/1.10.0/json": _pypi_body(
        license_expression="MIT",
        uploads=["2015-10-05T13:19:47.712263Z", "2015-10-06T00:00:00.000000Z"])}
    res = await query_registry([SIX_PINNED], transport=_handler(routes))
    meta = res.metadata[SIX_PINNED.key]
    assert meta.license_name == "MIT"
    assert meta.release_date == "2015-10-05"        # 최소 업로드 시각 → YYYY-MM-DD 정규화
    assert res.incomplete is False


@pytest.mark.asyncio
async def test_pypi_license_text_blob_normalized_to_spdx():
    routes = {"/pypi/pymupdf/json": _pypi_body(license=AGPL_TEXT)}
    res = await query_registry([PYMUPDF_LATEST], transport=_handler(routes))
    meta = res.metadata[PYMUPDF_LATEST.key]
    assert meta.license_name == "AGPL-3.0"          # 전문 blob → SPDX id
    assert len(meta.license_name) <= 128


@pytest.mark.asyncio
async def test_pypi_classifier_fallback():
    routes = {"/pypi/pymupdf/json": _pypi_body(classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
    ])}
    res = await query_registry([PYMUPDF_LATEST], transport=_handler(routes))
    assert res.metadata[PYMUPDF_LATEST.key].license_name == "AGPL-3.0"


@pytest.mark.asyncio
async def test_pypi_unpinned_queries_latest_path():
    calls: list[str] = []
    routes = {"/pypi/pymupdf/json": _pypi_body(license="AGPL-3.0")}
    await query_registry([PYMUPDF_LATEST], transport=_handler(routes, calls=calls))
    assert calls == ["https://pypi.org/pypi/pymupdf/json"]


@pytest.mark.asyncio
async def test_npm_full_doc_license_and_time():
    q = RegistryQuery(key="pkg:npm/leftpad@1.2.3", ecosystem="npm",
                      name="leftpad", version="1.2.3")
    routes = {"/leftpad": {
        "dist-tags": {"latest": "2.0.0"},
        "versions": {"1.2.3": {"license": {"type": "MIT"}}, "2.0.0": {"license": "ISC"}},
        "time": {"1.2.3": "2016-03-22T12:00:00.000Z", "2.0.0": "2020-01-01T00:00:00.000Z"},
    }}
    res = await query_registry([q], transport=_handler(routes))
    meta = res.metadata[q.key]
    assert meta.license_name == "MIT"               # 레거시 dict 형식도 읽는다
    assert meta.release_date == "2016-03-22"


@pytest.mark.asyncio
async def test_npm_scoped_package_url_encoding_and_latest_fallback():
    calls: list[str] = []
    q = RegistryQuery(key="pkg:npm/%40scope/pkg", ecosystem="npm",
                      name="@scope/pkg", version="9.9.9")     # versions에 없는 버전
    # httpx의 url.path는 퍼센트 디코딩된 값이다 — 전송 인코딩은 아래 calls로 검증한다.
    routes = {"/@scope/pkg": {
        "dist-tags": {"latest": "1.0.0"},
        "versions": {"1.0.0": {"license": "Apache-2.0"}},
        "time": {"1.0.0": "2024-05-01T00:00:00.000Z"},
    }}
    res = await query_registry([q], transport=_handler(routes, calls=calls))
    assert calls == ["https://registry.npmjs.org/@scope%2Fpkg"]
    assert res.metadata[q.key].license_name == "Apache-2.0"   # latest 폴백


@pytest.mark.asyncio
async def test_404_is_deterministic_negative_not_incomplete():
    res = await query_registry([SIX_PINNED], transport=_handler({}))
    assert res.metadata == {}                       # 메타데이터 없음
    assert res.incomplete is False                  # 장애가 아니다


@pytest.mark.asyncio
async def test_timeout_keeps_partial_result_and_sets_incomplete():
    routes = {"/pypi/pymupdf/json": _pypi_body(license="AGPL-3.0")}
    res = await query_registry(
        [SIX_PINNED, PYMUPDF_LATEST],
        transport=_handler(routes, exc_paths=("/pypi/six/1.10.0/json",)))
    assert res.incomplete is True
    assert SIX_PINNED.key not in res.metadata
    assert res.metadata[PYMUPDF_LATEST.key].license_name == "AGPL-3.0"   # 부분 결과 유지


@pytest.mark.asyncio
async def test_duplicate_queries_fetch_once_map_to_all_keys():
    calls: list[str] = []
    dup = RegistryQuery(key="pkg:pypi/six@1.10.0?src=lock", ecosystem="pypi",
                        name="Six", version="1.10.0")         # 이름 대소문자만 다름
    routes = {"/pypi/six/1.10.0/json": _pypi_body(license="MIT")}
    res = await query_registry([SIX_PINNED, dup], transport=_handler(routes, calls=calls))
    assert len(calls) == 1
    assert res.metadata[SIX_PINNED.key].license_name == "MIT"
    assert res.metadata[dup.key].license_name == "MIT"


@pytest.mark.asyncio
async def test_empty_input_does_not_call_api():
    calls: list[str] = []
    res = await query_registry([], transport=_handler({}, calls=calls))
    assert res.metadata == {} and res.incomplete is False and calls == []


def test_normalize_license_pymupdf_real_pypi_string_is_agpl():
    # PyPI 실측 원문 — "GNU AFFERO GPL 3.0"은 축약 표기라 GPL 패턴에 오인되기 쉽다.
    assert normalize_license(
        "Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License") == "AGPL-3.0"


def test_normalize_license_short_token_kept_long_text_dropped():
    assert normalize_license("(MIT OR AGPL-3.0)") == "AGPL-3.0"   # 패턴 우선
    assert normalize_license("Custom-License-1.0") == "Custom-License-1.0"
    assert normalize_license("있지도 않은 라이선스 " * 20) is None   # 장문 보호
    assert normalize_license("") is None and normalize_license(None) is None
