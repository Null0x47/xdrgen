"""Stubs for Defender-XDR-exclusive Advanced Hunting functions on Kustainer.

The stubs return empty / pass-through results — they exist so pasted hunting
queries parse and `.show schema as json` lists them (Monaco-Kusto in
`examples/kustainer-frontend/` picks them up for completion).

Caveat: real `FileProfile` is an engine plugin that accepts a column ref
(`invoke FileProfile(SHA1, ...)`). User-defined functions can't, so at
runtime use a literal string: `invoke FileProfile("SHA1", ...)`.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass


@dataclass
class FunctionStub:
    name: str
    body: str


# Tabular: pass-through with empty reputation columns.
FILE_PROFILE = FunctionStub(
    name="FileProfile",
    body=r"""
.create-or-alter function with (folder='Defender stubs', docstring='Stub: passes input through with empty file-reputation columns.')
FileProfile(T:(*), FileIdColumnName:string="SHA1", MaxNumberOfFileIds:int=1000) {
    T
    | extend
        GlobalPrevalence = tolong(0),
        GlobalFirstSeen = datetime(null),
        GlobalLastSeen = datetime(null),
        Signer = tostring(""),
        Issuer = tostring(""),
        SignerHash = tostring(""),
        IsCertificateValid = false,
        IsRootSignerMicrosoft = false,
        IsExecutable = false,
        ThreatName = tostring(""),
        Size = tolong(0),
        FileType = tostring(""),
        IsPeFile = false,
        FileNames = dynamic([]),
        ProfileAvailability = tostring("Not available")
}
""".strip(),
)


ASSIGNED_IP_ADDRESSES = FunctionStub(
    name="AssignedIPAddresses",
    body=r"""
.create-or-alter function with (folder='Defender stubs', docstring='Stub: returns an empty rowset matching the real AssignedIPAddresses schema.')
AssignedIPAddresses(DeviceName:string="", Timestamp:datetime=datetime(null)) {
    datatable(
        IPAddress:string,
        IPType:string,
        MacAddress:string,
        NetworkAdapterName:string,
        ConnectedNetworks:dynamic
    ) []
}
""".strip(),
)


SEEN_BY = FunctionStub(
    name="SeenBy",
    body=r"""
.create-or-alter function with (folder='Defender stubs', docstring='Stub: returns an empty rowset matching the real SeenBy schema.')
SeenBy(DeviceId:string) {
    datatable(
        DeviceId:string,
        DeviceName:string,
        ReportTime:datetime
    ) []
}
""".strip(),
)


DEVICE_FROM_IP = FunctionStub(
    name="DeviceFromIP",
    body=r"""
.create-or-alter function with (folder='Defender stubs', docstring='Stub: returns an empty rowset matching the real DeviceFromIP schema.')
DeviceFromIP(IP:string, Timestamp:datetime=datetime(null)) {
    datatable(
        DeviceId:string,
        DeviceName:string,
        Timestamp:datetime
    ) []
}
""".strip(),
)


STUBS: list[FunctionStub] = [
    FILE_PROFILE,
    ASSIGNED_IP_ADDRESSES,
    SEEN_BY,
    DEVICE_FROM_IP,
]


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
        help="Database to create functions in (default: NetDefaultDB).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the control commands without executing them.",
    )
    args = parser.parse_args()

    if args.dry_run:
        for stub in STUBS:
            print(stub.body)
            print()
        return 0

    client = _build_client(args.cluster)
    try:
        for stub in STUBS:
            client.execute_mgmt(args.database, stub.body)
            print(f"created function {stub.name}")
    except Exception as exc:
        print(f"failed: {exc}", file=sys.stderr)
        return 1
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()

    print(f"Done. {len(STUBS)} function(s) ensured in {args.database}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
