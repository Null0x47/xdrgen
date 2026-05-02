from __future__ import annotations

from parser import parse_xdr_table_names, parse_xdr_tables


def test_parse_xdr_table_names_filters_by_category():
    csv_text = (
        "table_name,category\n"
        "DeviceEvents,MDE\n"
        "CloudAppEvents,XDR\n"
        "AzureActivity,Azure\n"
        "OfficeActivity,Office 365\n"
    )

    names = parse_xdr_table_names([csv_text])

    assert names == {"DeviceEvents", "CloudAppEvents"}


def test_parse_xdr_table_names_is_case_insensitive():
    csv_text = (
        "table_name,category\n"
        "Lower,xdr\n"
        "Upper,XDR\n"
        "Mixed,Xdr\n"
        "MdeLower,mde\n"
        "MdeMixed,Mde\n"
    )

    names = parse_xdr_table_names([csv_text])

    assert names == {"Lower", "Upper", "Mixed", "MdeLower", "MdeMixed"}


def test_parse_xdr_table_names_unions_multiple_csvs():
    a = "table_name,category\nA,XDR\nShared,XDR\n"
    b = "table_name,category\nB,MDE\nShared,XDR\n"

    names = parse_xdr_table_names([a, b])

    assert names == {"A", "B", "Shared"}


def test_parse_xdr_table_names_substring_match():
    # category strings in the source data are sometimes phrases like
    # "Microsoft 365 Defender (XDR)" — substring match, not exact equality.
    csv_text = (
        "table_name,category\n"
        "Phrase,Microsoft 365 Defender (XDR)\n"
        "OtherPhrase,MDE table\n"
    )

    names = parse_xdr_table_names([csv_text])

    assert names == {"Phrase", "OtherPhrase"}


def test_parse_xdr_tables_groups_columns_by_table():
    schemas = (
        "table_name,column_name,column_type,description\n"
        "DeviceEvents,Timestamp,datetime,When the event was generated\n"
        "DeviceEvents,DeviceId,string,Device identifier\n"
        "CloudAppEvents,ActionType,string,Action type\n"
    )

    tables = parse_xdr_tables(schemas, {"DeviceEvents", "CloudAppEvents"})

    by_name = {t.model_name: t for t in tables}
    assert set(by_name) == {"DeviceEvents", "CloudAppEvents"}
    assert [c.name for c in by_name["DeviceEvents"].columns] == [
        "Timestamp",
        "DeviceId",
    ]
    assert by_name["DeviceEvents"].columns[0].xdr_type == "datetime"
    assert (
        by_name["DeviceEvents"].columns[0].description == "When the event was generated"
    )


def test_parse_xdr_tables_skips_tables_not_in_set():
    schemas = (
        "table_name,column_name,column_type,description\n"
        "DeviceEvents,Timestamp,datetime,desc\n"
        "AzureActivity,Caller,string,desc\n"
    )

    tables = parse_xdr_tables(schemas, {"DeviceEvents"})

    assert len(tables) == 1
    assert tables[0].model_name == "DeviceEvents"


def test_parse_xdr_tables_handles_missing_description():
    schemas = (
        "table_name,column_name,column_type,description\n"
        "DeviceEvents,Timestamp,datetime,\n"
    )

    tables = parse_xdr_tables(schemas, {"DeviceEvents"})

    assert tables[0].columns[0].description == ""
