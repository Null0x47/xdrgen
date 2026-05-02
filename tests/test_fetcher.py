from __future__ import annotations

import httpx
import pytest
import respx

from fetcher import (
    TABLE_SCHEMAS_URL,
    TABLES_REFERENCE_URL,
    TABLES_URL,
    fetch_schema_sources,
)


@respx.mock
async def test_fetch_schema_sources_returns_all_three_csvs():
    respx.get(TABLES_URL).mock(return_value=httpx.Response(200, text="tables-csv"))
    respx.get(TABLES_REFERENCE_URL).mock(
        return_value=httpx.Response(200, text="tables-reference-csv")
    )
    respx.get(TABLE_SCHEMAS_URL).mock(
        return_value=httpx.Response(200, text="schemas-csv")
    )

    reference_csvs, schemas_csv = await fetch_schema_sources()

    assert reference_csvs == ["tables-csv", "tables-reference-csv"]
    assert schemas_csv == "schemas-csv"


@respx.mock
async def test_fetch_schema_sources_raises_on_http_error():
    respx.get(TABLES_URL).mock(return_value=httpx.Response(404))
    respx.get(TABLES_REFERENCE_URL).mock(return_value=httpx.Response(200, text=""))
    respx.get(TABLE_SCHEMAS_URL).mock(return_value=httpx.Response(200, text=""))

    with pytest.raises(httpx.HTTPStatusError):
        await fetch_schema_sources()
