from __future__ import annotations

import asyncio

import httpx

TABLES_URL = (
    "https://raw.githubusercontent.com/Azure/Azure-Sentinel/master"
    "/Tools/Solutions%20Analyzer/tables.csv"
)
TABLES_REFERENCE_URL = (
    "https://raw.githubusercontent.com/Azure/Azure-Sentinel/master"
    "/Tools/Solutions%20Analyzer/tables_reference.csv"
)
TABLE_SCHEMAS_URL = (
    "https://raw.githubusercontent.com/Azure/Azure-Sentinel/master"
    "/Tools/Solutions%20Analyzer/table_schemas.csv"
)


async def _fetch_text(client: httpx.AsyncClient, url: str) -> str:
    response = await client.get(url, timeout=60.0)
    response.raise_for_status()
    return response.text


async def fetch_schema_sources() -> tuple[list[str], str]:
    """Fetch both reference CSVs and the schemas CSV concurrently.

    Returns ([tables.csv text, tables_reference.csv text], table_schemas.csv text).
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tables_csv, reference_csv, schemas_csv = await asyncio.gather(
            _fetch_text(client, TABLES_URL),
            _fetch_text(client, TABLES_REFERENCE_URL),
            _fetch_text(client, TABLE_SCHEMAS_URL),
        )
    return [tables_csv, reference_csv], schemas_csv
