"""Create one Kustainer table per Pydantic model via idempotent `.create-merge`."""

from __future__ import annotations

import argparse
import inspect
import sys

from pydantic import BaseModel

import models
from sinks.kustainer import columns_for_model


def _iter_model_classes() -> list[type[BaseModel]]:
    classes: list[type[BaseModel]] = []
    for _name, obj in inspect.getmembers(models, inspect.isclass):
        if obj is BaseModel:
            continue
        if issubclass(obj, BaseModel) and obj.__module__.startswith("models."):
            classes.append(obj)
    classes.sort(key=lambda c: c.__name__)
    return classes


def _create_table_command(cls: type[BaseModel], table_prefix: str) -> str:
    columns = columns_for_model(cls)
    column_decls = ", ".join(f"{name}:{kusto_type}" for name, kusto_type in columns)
    table_name = f"{table_prefix}{cls.__name__}"
    return f".create-merge table {table_name} ({column_decls})"


def _build_client(cluster_uri: str):
    from azure.kusto.data import KustoClient, KustoConnectionStringBuilder

    kcsb = KustoConnectionStringBuilder.with_no_authentication(cluster_uri)
    return KustoClient(kcsb)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cluster",
        default="http://localhost:8080",
        help="Kustainer HTTP endpoint (default: http://localhost:8080).",
    )
    parser.add_argument(
        "--database",
        default="NetDefaultDB",
        help="Database to create tables in (default: NetDefaultDB).",
    )
    parser.add_argument(
        "--table-prefix",
        default="",
        help="Optional prefix prepended to every table name.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the control commands without executing them.",
    )
    args = parser.parse_args()

    classes = _iter_model_classes()
    if not classes:
        print(
            "No models found — run `uv run xdrgen update-models` first.",
            file=sys.stderr,
        )
        return 1

    commands = [_create_table_command(cls, args.table_prefix) for cls in classes]

    if args.dry_run:
        for command in commands:
            print(command)
        return 0

    client = _build_client(args.cluster)
    try:
        for cls, command in zip(classes, commands):
            client.execute_mgmt(args.database, command)
            print(f"created table {args.table_prefix}{cls.__name__}")
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()

    print(f"Done. {len(classes)} tables ensured in {args.database}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
