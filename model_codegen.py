from __future__ import annotations

import keyword
import re
import sys

from parser import ColumnDef, TableDef

XDR_TYPE_MAP: dict[str, str] = {
    "datetime": "datetime",
    "string": "str",
    "long": "int",
    "int": "int",
    "integer": "int",
    "bool": "bool",
    "boolean": "bool",
    "nullable bool": "bool",
    "real": "float",
    "dynamic": "Any",
    "object": "dict[str, Any]",
    "guid": "str",
    "enum": "str",
}

_SNAKE_RE_1 = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_SNAKE_RE_2 = re.compile(r"(?<=[A-Z])(?=[A-Z][a-z])")


def model_name_to_filename(model_name: str) -> str:
    s = _SNAKE_RE_1.sub("_", model_name)
    s = _SNAKE_RE_2.sub("_", s)
    return s.lower() + ".py"


def _resolve_type(xdr_type: str, source_filename: str) -> str:
    py_type = XDR_TYPE_MAP.get(xdr_type.lower())
    if py_type is None:
        print(
            f"WARNING: unknown type '{xdr_type}' in {source_filename}, defaulting to str",
            file=sys.stderr,
        )
        return "str"
    return py_type


def _safe_field_name(name: str) -> str:
    if keyword.iskeyword(name) or (name and name[0].isdigit()):
        return f"_{name}"
    return name


def _build_imports(columns: list[ColumnDef], source_filename: str) -> str:
    types = {_resolve_type(c.xdr_type, source_filename) for c in columns}
    lines = []
    if "datetime" in types:
        lines.append("from datetime import datetime")
    if "Any" in types or any("Any" in t for t in types):
        lines.append("from typing import Any")
    lines.append("from typing import Optional")
    lines.append("")
    lines.append("from pydantic import BaseModel, Field")
    return "\n".join(lines)


def generate_model_file(table: TableDef) -> tuple[str, str]:
    filename = model_name_to_filename(table.model_name)
    columns = [c for c in table.columns if not c.name.startswith("_")]
    imports = _build_imports(columns, table.source_filename)

    field_lines: list[str] = []
    for col in columns:
        py_type = _resolve_type(col.xdr_type, table.source_filename)
        safe_name = _safe_field_name(col.name)
        desc = col.description.replace("\\", "\\\\").replace('"', '\\"')

        if safe_name != col.name:
            field_lines.append(
                f"    {safe_name}: Optional[{py_type}] = "
                f'Field(None, alias="{col.name}", description="{desc}")'
            )
        else:
            field_lines.append(
                f'    {col.name}: Optional[{py_type}] = Field(None, description="{desc}")'
            )

    fields_block = "\n".join(field_lines) if field_lines else "    pass"

    content = f"""{imports}


class {table.model_name}(BaseModel):
{fields_block}
"""
    return filename, content


def generate_init_file(tables: list[TableDef]) -> str:
    sorted_tables = sorted(tables, key=lambda t: t.model_name)
    lines: list[str] = []
    for table in sorted_tables:
        module = model_name_to_filename(table.model_name)[:-3]
        lines.append(f"from .{module} import {table.model_name}")
    lines.append("")
    lines.append("__all__ = [")
    for table in sorted_tables:
        lines.append(f'    "{table.model_name}",')
    lines.append("]")
    return "\n".join(lines) + "\n"
