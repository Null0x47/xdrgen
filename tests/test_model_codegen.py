from __future__ import annotations

from model_codegen import (
    generate_init_file,
    generate_model_file,
    model_name_to_filename,
)
from parser import ColumnDef, TableDef


def _table(columns: list[ColumnDef]) -> TableDef:
    return TableDef(
        model_name="DeviceEvents",
        source_filename="table_schemas.csv",
        columns=columns,
    )


def test_model_name_to_filename_simple():
    assert model_name_to_filename("DeviceEvents") == "device_events.py"


def test_model_name_to_filename_consecutive_capitals():
    # SPN must not collapse into one word.
    assert (
        model_name_to_filename("EntraIdSpnSignInEvents")
        == "entra_id_spn_sign_in_events.py"
    )


def test_generate_model_file_skips_underscore_columns():
    table = _table(
        [
            ColumnDef(name="Timestamp", xdr_type="datetime", description="ts"),
            ColumnDef(name="_BilledSize", xdr_type="real", description="billing"),
            ColumnDef(name="_IsBillable", xdr_type="bool", description="billable"),
        ]
    )

    _, content = generate_model_file(table)

    assert "Timestamp" in content
    assert "_BilledSize" not in content
    assert "_IsBillable" not in content


def test_generate_model_file_aliases_python_keyword():
    table = _table(
        [
            ColumnDef(name="class", xdr_type="string", description="kind"),
        ]
    )

    _, content = generate_model_file(table)

    assert "_class: Optional[str]" in content
    assert 'alias="class"' in content


def test_generate_model_file_aliases_digit_starting_field():
    table = _table(
        [
            ColumnDef(name="3rdPartyId", xdr_type="string", description="vendor id"),
        ]
    )

    _, content = generate_model_file(table)

    assert "_3rdPartyId: Optional[str]" in content
    assert 'alias="3rdPartyId"' in content


def test_generate_model_file_includes_required_imports():
    table = _table(
        [
            ColumnDef(name="Timestamp", xdr_type="datetime", description="ts"),
            ColumnDef(name="Extra", xdr_type="dynamic", description="payload"),
        ]
    )

    _, content = generate_model_file(table)

    assert "from datetime import datetime" in content
    assert "from typing import Any" in content
    assert "from typing import Optional" in content
    assert "from pydantic import BaseModel, Field" in content


def test_generate_model_file_escapes_quotes_in_description():
    table = _table(
        [
            ColumnDef(name="X", xdr_type="string", description='Quoted "value" here'),
        ]
    )

    _, content = generate_model_file(table)

    assert 'Quoted \\"value\\" here' in content


def test_generate_model_file_unknown_type_falls_back_to_str(capsys):
    table = _table(
        [
            ColumnDef(name="Weird", xdr_type="madeup", description="x"),
        ]
    )

    _, content = generate_model_file(table)

    assert "Weird: Optional[str]" in content
    err = capsys.readouterr().err
    assert "unknown type 'madeup'" in err


def test_generate_model_file_returns_correct_filename():
    table = _table([ColumnDef(name="X", xdr_type="string", description="")])

    filename, _ = generate_model_file(table)

    assert filename == "device_events.py"


def test_generate_init_file_sorts_imports_alphabetically():
    tables = [
        TableDef(model_name="DeviceEvents", source_filename="x"),
        TableDef(model_name="AlertInfo", source_filename="x"),
        TableDef(model_name="CloudAppEvents", source_filename="x"),
    ]

    content = generate_init_file(tables)

    lines = [line for line in content.splitlines() if line.startswith("from .")]
    assert lines == [
        "from .alert_info import AlertInfo",
        "from .cloud_app_events import CloudAppEvents",
        "from .device_events import DeviceEvents",
    ]
    assert content.index('"AlertInfo"') < content.index('"CloudAppEvents"')
    assert content.index('"CloudAppEvents"') < content.index('"DeviceEvents"')
