from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO

SCHEMAS_SOURCE = "table_schemas.csv"


@dataclass
class ColumnDef:
    name: str
    xdr_type: str
    description: str


@dataclass
class TableDef:
    model_name: str
    source_filename: str
    columns: list[ColumnDef] = field(default_factory=list)


def parse_xdr_table_names(reference_csvs: list[str]) -> set[str]:
    """Union of table names whose `category` marks them as Defender XDR / MDE.

    Accepts multiple CSV texts so the catalogue can be assembled from several
    overlapping reference files.
    """
    names: set[str] = set()
    for text in reference_csvs:
        for row in csv.DictReader(StringIO(text)):
            category = row.get("category", "").lower()
            if "xdr" in category or "mde" in category or "defender" in category:
                names.add(row["table_name"])
    return names


def parse_xdr_tables(schemas_csv: str, xdr_table_names: set[str]) -> list[TableDef]:
    """Group rows of table_schemas.csv into TableDef objects, keeping only XDR tables."""
    reader = csv.DictReader(StringIO(schemas_csv))
    tables: dict[str, TableDef] = {}
    for row in reader:
        name = row["table_name"]
        if name not in xdr_table_names:
            continue
        table = tables.get(name)
        if table is None:
            table = TableDef(model_name=name, source_filename=SCHEMAS_SOURCE)
            tables[name] = table
        table.columns.append(
            ColumnDef(
                name=row["column_name"],
                xdr_type=row["column_type"],
                description=row.get("description") or "",
            )
        )
    return list(tables.values())
