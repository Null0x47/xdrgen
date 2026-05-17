"""Frozen World fixture + Profile/Overrides YAML models for generators."""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, model_validator

T = TypeVar("T")


class ScalarEntry(BaseModel):
    """Wrapper for plain-string pool entries.

    `value` carries the string; `weight` is required only when the
    enclosing `WeightedPool` is opted into weighted mode with `random=false`.
    YAML string lists are auto-coerced to `{value: <str>}` for these pools."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: str
    weight: Optional[int] = None


class WeightedPool(BaseModel, Generic[T]):
    """Pool of pickable entries with an explicit sampling mode.

    `random=True` (default): generators sample uniformly; any per-entry
    `weight` is ignored. `random=False`: every entry must declare `weight`
    and generators sample weighted. Yaml profiles can omit the wrapper
    entirely and pass a bare list — that is auto-wrapped with `random=True`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    random: bool = True
    entries: tuple[T, ...]

    @model_validator(mode="after")
    def _check_weights(self) -> "WeightedPool[T]":
        if self.random:
            return self
        missing = [
            i for i, e in enumerate(self.entries) if getattr(e, "weight", None) is None
        ]
        if missing:
            raise ValueError(
                "random=false requires `weight` on every entry; "
                f"missing at index/indices {missing}"
            )
        return self

    def __iter__(self):
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, i):
        return self.entries[i]

    def __contains__(self, item) -> bool:
        return item in self.entries


def _pool_target(annotation: Any) -> Optional[Any]:
    """If `annotation` is a (possibly Optional/Union) `WeightedPool[X]`, return it."""
    if isinstance(annotation, type) and issubclass(annotation, WeightedPool):
        return annotation
    if get_origin(annotation) is Union:
        for arg in get_args(annotation):
            sub = _pool_target(arg)
            if sub is not None:
                return sub
    return None


def _is_scalar_pool(target: Any) -> bool:
    meta = getattr(target, "__pydantic_generic_metadata__", None)
    if not meta:
        return False
    args = meta.get("args") or ()
    return bool(args) and isinstance(args[0], type) and issubclass(args[0], ScalarEntry)


def _coerce_entry(entry: Any, scalar: bool) -> Any:
    if scalar and isinstance(entry, str):
        return {"value": entry}
    return entry


def _wrap_pool_input(value: Any, target: Any) -> Any:
    """Normalize a pool override value into a `{random, entries}` dict."""
    if value is None or isinstance(value, WeightedPool):
        return value
    scalar = _is_scalar_pool(target)
    if isinstance(value, (list, tuple)):
        return {"random": True, "entries": [_coerce_entry(e, scalar) for e in value]}
    if isinstance(value, dict) and "entries" in value:
        out = dict(value)
        out["entries"] = [_coerce_entry(e, scalar) for e in out.get("entries", [])]
        return out
    return value


def _auto_wrap_pools(cls: type, data: Any) -> Any:
    """Model-validator (mode=before) shared by World and Overrides.

    Accepts bare lists/tuples for pool fields and wraps them as
    `WeightedPool(random=True, entries=…)`. Also coerces bare strings
    to `{value: <str>}` for scalar-wrapper pools."""
    if not isinstance(data, dict):
        return data
    for name, info in cls.model_fields.items():
        target = _pool_target(info.annotation)
        if target is None:
            continue
        if name not in data:
            continue
        data[name] = _wrap_pool_input(data[name], target)
    return data


def _pool(items: tuple, random: bool = True) -> WeightedPool:
    """Helper to wrap a default tuple into a uniform WeightedPool."""
    return WeightedPool(random=random, entries=items)


def _scalar_pool(values: tuple[str, ...]) -> WeightedPool[ScalarEntry]:
    """Wrap a default `tuple[str, ...]` into a WeightedPool[ScalarEntry]."""
    return WeightedPool(
        random=True, entries=tuple(ScalarEntry(value=v) for v in values)
    )


class User(BaseModel):
    """Tenant user / service account / guest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    display_name: str
    upn: str
    object_id: str
    type: str = "Regular"  # Regular | Admin | Application
    device_name: Optional[str] = None
    device_id: Optional[str] = None
    last_password_change_days_ago: int = 90
    sam_account_name: Optional[str] = None
    sid_rid: Optional[int] = None
    given_name: Optional[str] = None
    surname: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    employee_id: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    weight: Optional[int] = None


class DomainController(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    ip: str
    device_id: str
    weight: Optional[int] = None


class Process(BaseModel):
    """One InitiatingProcess catalogue entry — hashes are derived from
    `file_name` at runtime unless `md5` / `sha1` / `sha256` are pinned here
    (used to seed published IOC hashes into the telemetry)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    file_name: str
    folder_path: str
    company: str
    description: str
    internal_file_name: str
    original_file_name: str
    product_name: str
    product_version: str
    command_lines: tuple[str, ...]
    integrity_level: str = "Medium"
    elevation: str = "Default"
    signature_status: str = "Valid"
    signer_type: str = "OsVendor"
    parent: str = "explorer.exe"
    md5: Optional[str] = None
    sha1: Optional[str] = None
    sha256: Optional[str] = None
    weight: Optional[int] = None


class Device(BaseModel):
    """MDE-managed endpoint — drives every Device* table."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    device_id: str
    device_name: str
    os_platform: str = "Windows10"
    os_version: Optional[str] = None
    public_ip: Optional[str] = None
    local_ip: Optional[str] = None
    mac_address: Optional[str] = None
    machine_group: Optional[str] = None
    primary_user_upn: Optional[str] = None
    weight: Optional[int] = None


class IPEntry(BaseModel):
    """Source IP + geolocation; fields must align per IP."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ip: str
    city: str
    state: str
    country: str
    isp: str
    category: str  # Cloud provider | Corporate | ISP
    latitude: str
    longitude: str
    weight: Optional[int] = None


class UserAgentEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ua: str
    platform: str
    device_type: str  # Workstation | Mobile
    browser: str
    weight: Optional[int] = None


class Resource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    id: str
    weight: Optional[int] = None


class ClientApp(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    app_id: str
    weight: Optional[int] = None


class ServicePrincipal(BaseModel):
    """Workload identity for EntraIdSpnSignInEvents.
    is_managed_identity=True biases source IPs to the cloud-provider pool."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    id: str
    app_id: str
    is_managed_identity: bool = False
    weight: Optional[int] = None


class Group(BaseModel):
    """Entra ID directory group — surfaces in GraphApiAuditEvents.RequestUri."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    id: str
    weight: Optional[int] = None


class GraphApiEndpoint(BaseModel):
    """Graph endpoint emitted by GraphApiAuditEvents. URI may pin
    `/v1.0/` or `/beta/` or template `{ver}` for random selection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    method: str
    uri: str
    workload: str
    scope: str
    weight: Optional[int] = None


class RegistryTarget(BaseModel):
    """One DeviceRegistryEvents target — key + value tuple the generator picks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    value_name: str
    value_data: str
    value_type: str  # REG_SZ | REG_DWORD | REG_BINARY | …
    weight: Optional[int] = None


class CloudApp(BaseModel):
    """One Defender for Cloud Apps connector feeding CloudAppEvents.

    `app_id` / `instance_id` are real DfCA values; `actions` is the
    connector-specific vocabulary the row's ActionType is drawn from."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    app_id: int
    instance_id: int
    audit_source: str
    actions: tuple[str, ...]
    weight: Optional[int] = None


class DeviceNetworkActionType(BaseModel):
    """Weighted DeviceNetworkEvents ActionType."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str
    weight: Optional[int] = None


class NetworkAdapter(BaseModel):
    """One DeviceNetworkInfo adapter — Wi-Fi, wired LAN, VPN tunnel, etc."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    type: str  # Wireless | Ethernet | Tunnel
    vendor: str
    tunnel: Optional[str] = None  # Ssh | Ipsec | None
    network_category: str  # Private | Public | Domain
    network_name: str
    weight: Optional[int] = None


class DeviceRegistryActionType(BaseModel):
    """Weighted DeviceRegistryEvents ActionType."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str
    weight: Optional[int] = None


class EmailPostDeliveryPath(BaseModel):
    """One ZAP / manual / user-reported path feeding EmailPostDeliveryEvents.

    Phish-verdict emails are constrained to ZAP / Admin triggers; user
    reclassifications fire only against clean mail."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str
    action_type: str
    trigger: str  # ZAP | Admin | User
    result: str
    delivery_location: str
    weight: Optional[int] = None


class GraphApiStatusCode(BaseModel):
    """Weighted HTTP status feeding GraphApiAuditEvents.ResponseStatusCode."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    weight: Optional[int] = None


class IdentityRiskLevel(BaseModel):
    """Weighted DefenderRiskLevel for IdentityAccountInfo (0=None .. 3=High)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    level: int
    weight: Optional[int] = None


class IdentityDirectoryActionType(BaseModel):
    """Weighted IdentityDirectoryEvents ActionType."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str
    weight: Optional[int] = None


class IdentityRawAction(BaseModel):
    """One raw source-side action feeding IdentityEvents.

    `application` is the source system (`AzureActiveDirectory`, `Okta`);
    `target_kind` ∈ {user, group, app, policy} drives TargetObjects shape."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str
    application: str
    target_kind: str
    weight: Optional[int] = None


class IdentityLogonType(BaseModel):
    """Weighted LogonType for IdentityLogonEvents."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    logon_type: str
    weight: Optional[int] = None


class IdentityLogonProtocol(BaseModel):
    """Weighted (protocol, port) pair for IdentityLogonEvents.

    Service / Batch logons are routed through Kerberos by the generator
    regardless of weighting."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol: str
    port: int
    weight: Optional[int] = None


class IdentityQueryKind(BaseModel):
    """Weighted (query_type, protocol, port) tuple for IdentityQueryEvents."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    query_type: str
    protocol: str  # Ldap | Samr | Dns
    port: int
    weight: Optional[int] = None


class UrlClickOutcome(BaseModel):
    """Weighted Safe Links click outcome feeding UrlClickEvents.

    A phish-verdict email always routes to a Block* outcome regardless of
    weighting — that override happens in the generator."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action_type: str
    is_clicked_through: bool
    threat_types: Optional[str] = None
    weight: Optional[int] = None


class WeightedWorkload(BaseModel):
    """Weighted source workload feeding UrlClickEvents.Workload."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workload: str
    weight: Optional[int] = None


class DeviceLogonType(BaseModel):
    """Weighted LogonType for DeviceLogonEvents.

    `logon_type` is one of MDE's emitted values (Network, Interactive,
    RemoteInteractive, Service, Batch, Unlock, NetworkCleartext,
    CachedInteractive); `weight` controls sampling probability."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    logon_type: str
    weight: Optional[int] = None


class LoadedLibrary(BaseModel):
    """DLL / managed assembly feeding DeviceImageLoadEvents.

    `folder_path` is the directory the library lives in; the generator
    concatenates it with `file_name` to render `FolderPath`. Hashes are
    derived deterministically from `file_name` so cross-table pivots
    against other Device* tables agree."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    file_name: str
    folder_path: str
    weight: Optional[int] = None


class CodeSigningCertificate(BaseModel):
    """Code-signing cert feeding DeviceFileCertificateInfo.

    `is_root_microsoft` drives `IsRootSignerMicrosoft`; `signature_type`
    matches MDE's column values (`Embedded`, `Catalog`, `None`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject: str
    issuer: str
    serial: str
    is_root_microsoft: bool = False
    signature_type: str = "Embedded"
    weight: Optional[int] = None


class DeviceEventAction(BaseModel):
    """Weighted DeviceEvents ActionType + shape selector.

    `shape` ∈ {file, network, registry, none} drives which auxiliary
    column block the generated row populates (file fields for AV detections,
    network fields for Network Protection / browser launches, registry
    fields for tampering attempts, none for self-contained events)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str
    shape: str  # file | network | registry | none
    weight: Optional[int] = None


class FileTemplate(BaseModel):
    """One file template feeding DeviceFileEvents.

    `folder_template` may include `{user}` — rendered at emit time with the
    picked user's `sam_account_name`. `kind` ∈ {download, doc, temp, share}
    drives row shape: `download` populates `FileOrigin*` fields, `share`
    routes through SMB-share semantics (UNC path, `Request*` block)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    folder_template: str
    file_name: str
    kind: str  # download | doc | temp | share
    weight: Optional[int] = None


class FileActionType(BaseModel):
    """Weighted DeviceFileEvents ActionType.

    `NetworkShare*` actions are routed to UNC `share` templates regardless
    of distribution; other actions land on any template."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str
    weight: Optional[int] = None


class SensitivityLabel(BaseModel):
    """Label / sublabel pair for DeviceFileEvents.SensitivityLabel.

    Generator-level path heuristics (HR / Finance share folders) take
    precedence over this pool; the pool is the fallback for randomly
    labelled local Office documents."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str
    sublabel: Optional[str] = None
    weight: Optional[int] = None


class NetworkDestination(BaseModel):
    """Outbound destination pool for DeviceNetworkEvents.

    `url` is None for ports unrelated to a hostname (DNS, SMB, Kerberos, …)
    so the field stays null in the emitted row, matching real MDE telemetry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    port: int
    url: Optional[str] = None
    weight: Optional[int] = None


class ConditionalAccessPolicy(BaseModel):
    """camelCase to match Graph — serialised into EntraIdSignInEvents.ConditionalAccessPolicies."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    displayName: str
    enforcedGrantControls: tuple[str, ...] = ()
    enforcedSessionControls: tuple[str, ...] = ()
    weight: Optional[int] = None


class WeightedErrorCode(BaseModel):
    """Entra ID ErrorCode with sampling weight; description (optional) feeds
    AuthenticationProcessingDetails on failures."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: int
    weight: Optional[int] = None
    description: Optional[str] = None


class EmailAttachment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    file_name: str
    extension: str
    file_type: str
    file_size: int


class EmailUrl(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    url: str
    domain: str
    location: str  # Body | Subject | Attachment


class EmailTemplate(BaseModel):
    """One pre-built email feeding the Email* / UrlClickEvents generators.
    `recipient_persona` matches a `users[].sam_account_name` (with hash-index
    fallback). NetworkMessageId, InternetMessageId and SHA-256s are minted
    at runtime by `EmailPool`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject: str
    sender_display_name: str
    sender_from_address: str
    sender_from_domain: str
    sender_mail_from_address: str
    sender_mail_from_domain: str
    sender_object_id: Optional[str] = None
    sender_ipv4: Optional[str] = None
    sender_ipv6: Optional[str] = None
    recipient_persona: str
    direction: str  # Inbound | Outbound | Intra-org
    delivery_action: str
    delivery_location: str
    email_action: str
    email_action_policy: Optional[str] = None
    email_action_policy_guid: Optional[str] = None
    email_size: int
    bulk_complaint_level: int
    authentication_details: str
    confidence_level: str
    threat_types: Optional[str] = None
    threat_names: Optional[str] = None
    weight: Optional[int] = None
    threat_classification: Optional[str] = None
    detection_methods: Optional[str] = None
    is_first_contact: bool = False
    language: str = "en"
    attachments: tuple[EmailAttachment, ...] = ()
    urls: tuple[EmailUrl, ...] = ()


_DEFAULT_DOMAIN_CONTROLLERS: tuple[DomainController, ...] = (
    DomainController(
        name="DC01.contoso.local",
        ip="10.0.0.10",
        device_id="11112222-3333-4444-5555-666677778888",
    ),
    DomainController(
        name="DC02.contoso.local",
        ip="10.0.0.11",
        device_id="22223333-4444-5555-6666-777788889999",
    ),
)


_DEFAULT_PROCESSES: tuple[Process, ...] = (
    Process(
        file_name="explorer.exe",
        folder_path=r"C:\Windows",
        company="Microsoft Corporation",
        description="Windows Explorer",
        internal_file_name="explorer",
        original_file_name="EXPLORER.EXE",
        product_name="Microsoft® Windows® Operating System",
        product_version="10.0.19041.4291",
        command_lines=(r"C:\Windows\Explorer.EXE",),
        integrity_level="Medium",
        elevation="Default",
        signature_status="Valid",
        signer_type="OsVendor",
        parent="userinit.exe",
    ),
    Process(
        file_name="cmd.exe",
        folder_path=r"C:\Windows\System32",
        company="Microsoft Corporation",
        description="Windows Command Processor",
        internal_file_name="cmd",
        original_file_name="Cmd.Exe",
        product_name="Microsoft® Windows® Operating System",
        product_version="10.0.19041.3636",
        command_lines=(
            r"cmd.exe /c whoami",
            r"cmd.exe /c ipconfig /all",
            r"cmd.exe /c net localgroup administrators",
        ),
        integrity_level="Medium",
        elevation="Default",
        signature_status="Valid",
        signer_type="OsVendor",
        parent="explorer.exe",
    ),
    Process(
        file_name="powershell.exe",
        folder_path=r"C:\Windows\System32\WindowsPowerShell\v1.0",
        company="Microsoft Corporation",
        description="Windows PowerShell",
        internal_file_name="POWERSHELL",
        original_file_name="PowerShell.EXE.MUI",
        product_name="Microsoft® Windows® Operating System",
        product_version="10.0.19041.3636",
        command_lines=(
            r"powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\ProgramData\Scripts\update.ps1",
            r"powershell.exe -Command Get-ADUser -Filter *",
            r"powershell.exe -Command Invoke-WebRequest -Uri https://internal.contoso.com/feed",
        ),
        integrity_level="High",
        elevation="Full",
        signature_status="Valid",
        signer_type="OsVendor",
        parent="explorer.exe",
    ),
    Process(
        file_name="svchost.exe",
        folder_path=r"C:\Windows\System32",
        company="Microsoft Corporation",
        description="Host Process for Windows Services",
        internal_file_name="svchost.exe",
        original_file_name="svchost.exe",
        product_name="Microsoft® Windows® Operating System",
        product_version="10.0.19041.3636",
        command_lines=(
            r"C:\WINDOWS\system32\svchost.exe -k netsvcs -p",
            r"C:\WINDOWS\system32\svchost.exe -k LocalServiceNetworkRestricted -p",
        ),
        integrity_level="System",
        elevation="Full",
        signature_status="Valid",
        signer_type="OsVendor",
        parent="services.exe",
    ),
    Process(
        file_name="chrome.exe",
        folder_path=r"C:\Program Files\Google\Chrome\Application",
        company="Google LLC",
        description="Google Chrome",
        internal_file_name="chrome_exe",
        original_file_name="chrome.exe",
        product_name="Google Chrome",
        product_version="127.0.6533.100",
        command_lines=(
            r'"C:\Program Files\Google\Chrome\Application\chrome.exe"',
            r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --type=renderer',
        ),
        integrity_level="Low",
        elevation="Default",
        signature_status="Valid",
        signer_type="ThirdParty",
        parent="explorer.exe",
    ),
    Process(
        file_name="msedge.exe",
        folder_path=r"C:\Program Files (x86)\Microsoft\Edge\Application",
        company="Microsoft Corporation",
        description="Microsoft Edge",
        internal_file_name="msedge_exe",
        original_file_name="msedge.exe",
        product_name="Microsoft Edge",
        product_version="126.0.2592.113",
        command_lines=(
            r'"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"',
        ),
        integrity_level="Low",
        elevation="Default",
        signature_status="Valid",
        signer_type="OsVendor",
        parent="explorer.exe",
    ),
    Process(
        file_name="outlook.exe",
        folder_path=r"C:\Program Files\Microsoft Office\root\Office16",
        company="Microsoft Corporation",
        description="Microsoft Outlook",
        internal_file_name="Outlook",
        original_file_name="OUTLOOK.EXE",
        product_name="Microsoft Office",
        product_version="16.0.17328.20184",
        command_lines=(
            r'"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"',
        ),
        integrity_level="Medium",
        elevation="Default",
        signature_status="Valid",
        signer_type="OsVendor",
        parent="explorer.exe",
    ),
    Process(
        file_name="winword.exe",
        folder_path=r"C:\Program Files\Microsoft Office\root\Office16",
        company="Microsoft Corporation",
        description="Microsoft Word",
        internal_file_name="Word",
        original_file_name="WinWord.exe",
        product_name="Microsoft Office",
        product_version="16.0.17328.20184",
        command_lines=(
            r'"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE" /n',
        ),
        integrity_level="Medium",
        elevation="Default",
        signature_status="Valid",
        signer_type="OsVendor",
        parent="explorer.exe",
    ),
    Process(
        file_name="MsMpEng.exe",
        folder_path=r"C:\ProgramData\Microsoft\Windows Defender\Platform\4.18.24050.7-0",
        company="Microsoft Corporation",
        description="Antimalware Service Executable",
        internal_file_name="MsMpEng",
        original_file_name="MsMpEng.exe",
        product_name="Microsoft® Windows® Operating System",
        product_version="4.18.24050.7",
        command_lines=(
            r'"C:\ProgramData\Microsoft\Windows Defender\Platform\4.18.24050.7-0\MsMpEng.exe"',
        ),
        integrity_level="System",
        elevation="Full",
        signature_status="Valid",
        signer_type="OsVendor",
        parent="services.exe",
    ),
    Process(
        file_name="rundll32.exe",
        folder_path=r"C:\Windows\System32",
        company="Microsoft Corporation",
        description="Windows host process (Rundll32)",
        internal_file_name="rundll",
        original_file_name="RUNDLL32.EXE",
        product_name="Microsoft® Windows® Operating System",
        product_version="10.0.19041.3636",
        command_lines=(
            r"rundll32.exe shell32.dll,Control_RunDLL",
            r"rundll32.exe printui.dll,PrintUIEntry /Xg /n \\printsrv\HR-LJ4",
        ),
        integrity_level="Medium",
        elevation="Default",
        signature_status="Valid",
        signer_type="OsVendor",
        parent="explorer.exe",
    ),
)


_DEFAULT_DEVICES: tuple[Device, ...] = (
    Device(
        device_id="7c2bd31c-2102-4ce7-93a0-2cf5e19b5a7d",
        device_name="WIN-AVERY-01.contoso.com",
        os_platform="Windows10",
        os_version="10.0.19045.4291",
        public_ip="20.43.122.12",
        local_ip="10.10.20.41",
        mac_address="00-15-5D-04-12-7A",
        machine_group="Engineering Workstations",
        primary_user_upn="avery.chen@contoso.com",
    ),
    Device(
        device_id="8d3ce42d-3213-4df8-a4b1-3d06f2ac6b8e",
        device_name="MAC-JORDAN-02.contoso.com",
        os_platform="macOS",
        os_version="14.5",
        public_ip="52.114.6.45",
        local_ip="10.10.20.42",
        mac_address="A4-83-E7-2D-9C-11",
        machine_group="Finance Workstations",
        primary_user_upn="jordan.patel@contoso.com",
    ),
    Device(
        device_id="9e4df53e-4324-4e09-b5c2-4e17f3bd7c9f",
        device_name="WIN-SAM-PAW.contoso.com",
        os_platform="Windows11",
        os_version="10.0.22631.3737",
        public_ip="73.62.18.101",
        local_ip="10.10.30.5",
        mac_address="00-15-5D-04-12-7B",
        machine_group="Tier-0 Privileged Access Workstations",
        primary_user_upn="sam.rivera@contoso.com",
    ),
    Device(
        device_id="ad34af50-9012-4cdf-9a3b-1f02bc44ee10",
        device_name="LIN-BUILD-01.contoso.com",
        os_platform="Linux",
        os_version="Ubuntu 22.04.4 LTS",
        public_ip="20.43.122.12",
        local_ip="10.10.40.21",
        mac_address="00-15-5D-99-22-04",
        machine_group="Build Servers",
        primary_user_upn="svc-deploy@contoso.com",
    ),
    Device(
        device_id="be45cd61-1023-4ed0-9b1c-2e13ac55ff21",
        device_name="WIN-FILE-01.contoso.com",
        os_platform="WindowsServer2022",
        os_version="10.0.20348.2402",
        public_ip="20.43.122.12",
        local_ip="10.10.50.10",
        mac_address="00-15-5D-AA-33-15",
        machine_group="File Servers",
        primary_user_upn=None,
    ),
)


_DEFAULT_USERS: tuple[User, ...] = (
    User(
        display_name="Avery Chen",
        upn="avery.chen@contoso.com",
        object_id="8a9b1c2d-3e4f-4061-8283-94a5b6c7d8e9",
        type="Regular",
        device_name="WIN-AVERY-01.contoso.com",
        device_id="7c2bd31c-2102-4ce7-93a0-2cf5e19b5a7d",
        last_password_change_days_ago=47,
        sam_account_name="avery.chen",
        sid_rid=1104,
        given_name="Avery",
        surname="Chen",
        department="Engineering",
        job_title="Senior Software Engineer",
        employee_id="E10042",
        city="Amsterdam",
        country="NL",
    ),
    User(
        display_name="Jordan Patel",
        upn="jordan.patel@contoso.com",
        object_id="1b2c3d4e-5f60-4182-9304-a5b6c7d8e9f0",
        type="Regular",
        device_name="MAC-JORDAN-02.contoso.com",
        device_id="8d3ce42d-3213-4df8-a4b1-3d06f2ac6b8e",
        last_password_change_days_ago=12,
        sam_account_name="jordan.patel",
        sid_rid=1107,
        given_name="Jordan",
        surname="Patel",
        department="Finance",
        job_title="Financial Analyst",
        employee_id="E10118",
        city="Dublin",
        country="IE",
    ),
    User(
        display_name="Sam Rivera",
        upn="sam.rivera@contoso.com",
        object_id="2c3d4e5f-6071-4293-a4b5-c6d7e8f90112",
        type="Admin",
        device_name="WIN-SAM-PAW.contoso.com",
        device_id="9e4df53e-4324-4e09-b5c2-4e17f3bd7c9f",
        last_password_change_days_ago=3,
        sam_account_name="sam.rivera",
        sid_rid=500,
        given_name="Sam",
        surname="Rivera",
        department="IT",
        job_title="Tier 2 Identity Admin",
        employee_id="E10003",
        city="Seattle",
        country="US",
    ),
    User(
        display_name="Priya Iyer",
        upn="priya.iyer@contoso.com",
        object_id="3d4e5f60-7182-4304-b5c6-d7e8f9011223",
        type="Regular",
        last_password_change_days_ago=89,
        sam_account_name="priya.iyer",
        sid_rid=1212,
        given_name="Priya",
        surname="Iyer",
        department="Sales",
        job_title="Account Executive, EMEA",
        employee_id="E10221",
        city="London",
        country="GB",
    ),
    User(
        display_name="svc-deploy",
        upn="svc-deploy@contoso.com",
        object_id="4e5f6071-8293-44b5-86d7-e8f901122334",
        type="Application",
        last_password_change_days_ago=220,
        sam_account_name="svc-deploy",
        sid_rid=1501,
        department="IT",
        job_title="Service Account",
    ),
    User(
        display_name="Robin Park (Guest)",
        upn="robin.park_acme.com#EXT#@contoso.onmicrosoft.com",
        object_id="5f607182-9304-44c6-97e8-f901122334b5",
        type="Regular",
        last_password_change_days_ago=8,
        sam_account_name="robin.park_acme.com#EXT#",
        given_name="Robin",
        surname="Park",
        job_title="Guest Collaborator",
    ),
)


_DEFAULT_IPS: tuple[IPEntry, ...] = (
    IPEntry(
        ip="20.43.122.12",
        city="Amsterdam",
        state="North Holland",
        country="NL",
        isp="Microsoft Corporation",
        category="Cloud provider",
        latitude="52.379189",
        longitude="4.899431",
    ),
    IPEntry(
        ip="52.114.6.45",
        city="Dublin",
        state="Leinster",
        country="IE",
        isp="Microsoft Corporation",
        category="Cloud provider",
        latitude="53.349806",
        longitude="-6.260310",
    ),
    IPEntry(
        ip="104.46.162.224",
        city="San Antonio",
        state="Texas",
        country="US",
        isp="Microsoft Corporation",
        category="Cloud provider",
        latitude="29.424122",
        longitude="-98.493629",
    ),
    IPEntry(
        ip="73.62.18.101",
        city="Seattle",
        state="Washington",
        country="US",
        isp="Comcast Cable",
        category="Corporate",
        latitude="47.606209",
        longitude="-122.332069",
    ),
    IPEntry(
        ip="82.113.106.9",
        city="London",
        state="England",
        country="GB",
        isp="BT Group",
        category="ISP",
        latitude="51.507351",
        longitude="-0.127758",
    ),
    IPEntry(
        ip="203.0.113.45",
        city="Sydney",
        state="New South Wales",
        country="AU",
        isp="Telstra",
        category="ISP",
        latitude="-33.868820",
        longitude="151.209290",
    ),
)


_DEFAULT_USER_AGENTS: tuple[UserAgentEntry, ...] = (
    UserAgentEntry(
        ua=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        ),
        platform="Windows10",
        device_type="Workstation",
        browser="Chrome 127.0.0",
    ),
    UserAgentEntry(
        ua=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
        ),
        platform="Windows10",
        device_type="Workstation",
        browser="Edge 126.0.0",
    ),
    UserAgentEntry(
        ua=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        ),
        platform="macOS",
        device_type="Workstation",
        browser="Safari 17.0",
    ),
    UserAgentEntry(
        ua="Microsoft Office/16.0 (Windows NT 10.0; Microsoft Outlook 16.0.17328; Pro)",
        platform="Windows10",
        device_type="Workstation",
        browser="Outlook 16.0",
    ),
    UserAgentEntry(
        ua=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
        ),
        platform="iOS",
        device_type="Mobile",
        browser="Safari 17.4",
    ),
    UserAgentEntry(
        ua=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        platform="Linux",
        device_type="Workstation",
        browser="Chrome 126.0.0",
    ),
)


_DEFAULT_CLIENT_APPS: tuple[ClientApp, ...] = (
    ClientApp(name="Microsoft Office", app_id="d3590ed6-52b3-4102-aeff-aad2292ab01c"),
    ClientApp(name="Microsoft Teams", app_id="1fec8e78-bce4-4aaf-ab1b-5451cc387264"),
    ClientApp(name="Outlook Mobile", app_id="27922004-5251-4030-b22d-91ecd9a37ea4"),
    ClientApp(
        name="Microsoft Authenticator", app_id="4813382a-8fa7-425e-ab75-3b753aab3abb"
    ),
    ClientApp(name="Microsoft Edge", app_id="ecd6b820-32c2-49b6-98a6-444530e5a77a"),
    ClientApp(
        name="Microsoft Azure CLI", app_id="04b07795-8ddb-461a-bbee-02f9e1bf7b46"
    ),
    ClientApp(
        name="Microsoft Azure PowerShell", app_id="1950a258-227b-4e31-a9cf-717495945fc2"
    ),
    ClientApp(name="Azure Portal", app_id="c44b4083-3bb0-49c1-b47d-974e53cbdf3c"),
)


_DEFAULT_GROUPS: tuple[Group, ...] = (
    Group(name="All Employees", id="aa11bb22-cc33-4dd4-9eef-1011223344aa"),
    Group(name="Engineering", id="bb22cc33-dd44-4ee5-9ff0-2122334455bb"),
    Group(name="Sales Team", id="cc33dd44-ee55-4ff6-9001-3233445566cc"),
    Group(name="Finance", id="dd44ee55-ff66-4007-9112-4344556677dd"),
    Group(name="IT Admins", id="ee55ff66-0077-4118-9223-5455667788ee"),
    Group(name="Sensitive Operations", id="ff660077-1188-4229-9334-5566778899ff"),
)


_DEFAULT_SERVICE_PRINCIPALS: tuple[ServicePrincipal, ...] = (
    ServicePrincipal(
        name="contoso-app-prod",
        id="b7c1f4e2-0d8a-4d7e-9c2b-1a3f5e6c7d8a",
        app_id="f2c5d6e7-8a9b-4c1d-bf2e-3a4b5c6d7e8f",
        is_managed_identity=False,
    ),
    ServicePrincipal(
        name="contoso-functions-mi",
        id="c8d2e5f3-1e9b-4f8e-ad3c-2b4f6e7d8a9b",
        app_id="0a1b2c3d-4e5f-4061-8273-849a5b6c7d8e",
        is_managed_identity=True,
    ),
    ServicePrincipal(
        name="contoso-aks-system-mi",
        id="d9e3f604-2f0c-4a09-be4d-3c5f7a8b9c0d",
        app_id="1b2c3d4e-5f60-4172-9384-95a6b7c8d9ef",
        is_managed_identity=True,
    ),
    ServicePrincipal(
        name="github-actions-deploy",
        id="e0f4a715-3a1d-4b1a-cf5e-4d607b8c9d0e",
        app_id="2c3d4e5f-6071-4283-a495-b6c7d8e9f012",
        is_managed_identity=False,
    ),
    ServicePrincipal(
        name="terraform-cloud-runner",
        id="f105b826-4b2e-4c2b-d06f-5e718c9d0e1f",
        app_id="3d4e5f60-7182-4394-b5a6-c7d8e9f01223",
        is_managed_identity=False,
    ),
)


_DEFAULT_RESOURCES: tuple[Resource, ...] = (
    Resource(name="Microsoft Graph", id="00000003-0000-0000-c000-000000000000"),
    Resource(
        name="Office 365 Exchange Online", id="00000002-0000-0ff1-ce00-000000000000"
    ),
    Resource(
        name="Office 365 SharePoint Online", id="00000003-0000-0ff1-ce00-000000000000"
    ),
    Resource(
        name="Windows Azure Service Management API",
        id="797f4846-ba00-4fd7-ba43-dac1f8f63013",
    ),
    Resource(
        name="Microsoft Teams Services", id="cc15fd57-2c6c-4117-a88c-83b1d56b4bbe"
    ),
    Resource(
        name="Office 365 Management APIs", id="c5393580-f805-4401-95e8-94b7a6ef2fc2"
    ),
)


# Real Entra ErrorCodes; healthy tenant ~80% success.
# https://learn.microsoft.com/azure/active-directory/develop/reference-error-codes
_DEFAULT_ENTRA_SIGN_IN_ERROR_CODES: tuple[WeightedErrorCode, ...] = (
    WeightedErrorCode(code=0, weight=80),
    WeightedErrorCode(
        code=50126,
        weight=5,
        description="InvalidUserNameOrPassword: Error validating credentials due to invalid username or password.",
    ),
    WeightedErrorCode(
        code=50076,
        weight=3,
        description="UserStrongAuthClientAuthNRequired: Multi-factor authentication is required.",
    ),
    WeightedErrorCode(
        code=50074,
        weight=2,
        description="UserStrongAuthClientAuthNRequiredInterrupt: Strong authentication is required and the user did not pass the MFA challenge.",
    ),
    WeightedErrorCode(
        code=50053,
        weight=1,
        description="IdsLocked: Account is locked because the user tried to sign in too many times with an incorrect user ID or password.",
    ),
    WeightedErrorCode(
        code=53003,
        weight=2,
        description="BlockedByConditionalAccess: Access has been blocked by Conditional Access policies.",
    ),
    WeightedErrorCode(
        code=53000,
        weight=1,
        description="DeviceNotCompliant: The device used is not compliant with Conditional Access policy.",
    ),
    WeightedErrorCode(
        code=50158,
        weight=1,
        description="ExternalSecurityChallengeNotSatisfied: External security challenge was not satisfied.",
    ),
    WeightedErrorCode(
        code=50140,
        weight=1,
        description="KeepMeSignedInInterrupt: The user was presented with the Keep Me Signed In (KMSI) interrupt.",
    ),
    WeightedErrorCode(
        code=50057, weight=1, description="UserDisabled: The user account is disabled."
    ),
    WeightedErrorCode(
        code=50055,
        weight=1,
        description="InvalidPasswordExpiredPassword: The password is expired.",
    ),
    WeightedErrorCode(
        code=50034,
        weight=1,
        description="UserAccountNotFound: The user account does not exist in the directory.",
    ),
    WeightedErrorCode(
        code=50173,
        weight=1,
        description="FreshTokenNeeded: The provided grant has expired due to it being revoked, and a fresh auth token is needed.",
    ),
    WeightedErrorCode(
        code=50097,
        weight=1,
        description="DeviceAuthenticationRequired: Device authentication is required.",
    ),
)


# SPN sign-ins skew to success; failures are secret/consent issues.
_DEFAULT_ENTRA_SPN_SIGN_IN_ERROR_CODES: tuple[WeightedErrorCode, ...] = (
    WeightedErrorCode(code=0, weight=92),
    WeightedErrorCode(
        code=7000215,
        weight=2,
        description="InvalidClientSecret: Invalid client secret is provided.",
    ),
    WeightedErrorCode(
        code=7000222,
        weight=1,
        description="InvalidClientSecretExpiredKeysProvided: The provided client secret keys are expired.",
    ),
    WeightedErrorCode(
        code=700016,
        weight=1,
        description="UnauthorizedClient_DoesNotMatchAuthorizedParty: Application not found in the directory.",
    ),
    WeightedErrorCode(
        code=50105,
        weight=1,
        description="EntitlementGrantsNotFound: The signed-in user is not assigned to a role for the application.",
    ),
    WeightedErrorCode(
        code=90094,
        weight=1,
        description="AdminConsentRequired: Administrator consent is required for this application.",
    ),
    WeightedErrorCode(
        code=65001,
        weight=1,
        description="DelegationDoesNotExist: The user or administrator has not consented to use the application.",
    ),
    WeightedErrorCode(
        code=53003,
        weight=1,
        description="BlockedByConditionalAccess: Access has been blocked by Conditional Access policies (workload identity).",
    ),
    WeightedErrorCode(
        code=9002313,
        weight=1,
        description="InvalidGrant: The provided authorization grant has expired or been revoked.",
    ),
)


_DEFAULT_EMAIL_TEMPLATES: tuple[EmailTemplate, ...] = (
    EmailTemplate(
        subject="Invoice 8421 - Q2 services",
        sender_display_name="Acme Billing",
        sender_from_address="billing@acme-corp.com",
        sender_from_domain="acme-corp.com",
        sender_mail_from_address="billing@bounces.acme-corp.com",
        sender_mail_from_domain="bounces.acme-corp.com",
        sender_ipv4="203.0.113.45",
        recipient_persona="jordan.patel",
        direction="Inbound",
        delivery_action="Delivered",
        delivery_location="Inbox",
        email_action="No action taken",
        email_size=28412,
        bulk_complaint_level=4,
        authentication_details="SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        confidence_level='{"Spam":"1"}',
        attachments=(
            EmailAttachment(
                file_name="invoice_8421.pdf",
                extension="pdf",
                file_type="PDF Document",
                file_size=24813,
            ),
        ),
        urls=(
            EmailUrl(
                url="https://billing.acme-corp.com/pay/8421",
                domain="billing.acme-corp.com",
                location="Body",
            ),
            EmailUrl(
                url="https://acme-corp.com/policy",
                domain="acme-corp.com",
                location="Body",
            ),
        ),
    ),
    EmailTemplate(
        subject="[contoso/main] Pull request #482 ready for review",
        sender_display_name="GitHub",
        sender_from_address="noreply@github.com",
        sender_from_domain="github.com",
        sender_mail_from_address="bounces+482@sgmail.github.com",
        sender_mail_from_domain="sgmail.github.com",
        sender_ipv4="140.82.114.10",
        recipient_persona="avery.chen",
        direction="Inbound",
        delivery_action="Delivered",
        delivery_location="Inbox",
        email_action="No action taken",
        email_size=14210,
        bulk_complaint_level=1,
        authentication_details="SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        confidence_level='{"Spam":"1"}',
        urls=(
            EmailUrl(
                url="https://github.com/contoso/main/pull/482",
                domain="github.com",
                location="Body",
            ),
            EmailUrl(
                url="https://github.com/settings/notifications",
                domain="github.com",
                location="Body",
            ),
        ),
    ),
    EmailTemplate(
        subject="Please sign: NDA - Contoso / Northwind",
        sender_display_name="DocuSign EU System",
        sender_from_address="dse@eumail.docusign.net",
        sender_from_domain="eumail.docusign.net",
        sender_mail_from_address="dse@eumail.docusign.net",
        sender_mail_from_domain="eumail.docusign.net",
        sender_ipv4="162.248.184.10",
        recipient_persona="sam.rivera",
        direction="Inbound",
        delivery_action="Delivered",
        delivery_location="Inbox",
        email_action="No action taken",
        email_size=51201,
        bulk_complaint_level=1,
        authentication_details="SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        confidence_level='{"Spam":"1"}',
        is_first_contact=True,
        attachments=(
            EmailAttachment(
                file_name="NDA_Contoso_Northwind.pdf",
                extension="pdf",
                file_type="PDF Document",
                file_size=48201,
            ),
        ),
        urls=(
            EmailUrl(
                url="https://www.docusign.net/Member/EmailStart.aspx?envelopeId=abc123",
                domain="docusign.net",
                location="Body",
            ),
        ),
    ),
    EmailTemplate(
        subject="Action required: Verify your Microsoft account before May 5",
        sender_display_name="Microsoft Security",
        sender_from_address="no-reply@securemail-update.io",
        sender_from_domain="securemail-update.io",
        sender_mail_from_address="bounce@securemail-update.io",
        sender_mail_from_domain="securemail-update.io",
        sender_ipv4="185.244.25.121",
        recipient_persona="priya.iyer",
        direction="Inbound",
        delivery_action="Blocked",
        delivery_location="Quarantine",
        email_action="Send to quarantine",
        email_action_policy="Anti-phishing user impersonation",
        email_action_policy_guid="8d2d8c45-2f9f-4c5e-8b1a-1c12fbb1d9e6",
        email_size=18394,
        bulk_complaint_level=1,
        authentication_details="SPF=fail; DKIM=none; DMARC=fail; CompAuth=fail (reason=000)",
        confidence_level='{"Phish":"High"}',
        threat_types="Phish",
        threat_names="Phish:HTML/Generic.A",
        threat_classification="Credential phishing",
        detection_methods="URL detonation reputation, Heuristic clustering",
        is_first_contact=True,
        attachments=(
            EmailAttachment(
                file_name="password_reset_form.html",
                extension="html",
                file_type="HTML Document",
                file_size=7821,
            ),
        ),
        urls=(
            EmailUrl(
                url="https://securemail-update.io/verify?u=priya.iyer",
                domain="securemail-update.io",
                location="Body",
            ),
            EmailUrl(
                url="http://malicious-redirect.example/track?m=99281",
                domain="malicious-redirect.example",
                location="Body",
            ),
        ),
    ),
    EmailTemplate(
        subject="Re: Q3 forecast — updated numbers",
        sender_display_name="Avery Chen",
        sender_from_address="avery.chen@contoso.com",
        sender_from_domain="contoso.com",
        sender_mail_from_address="avery.chen@contoso.com",
        sender_mail_from_domain="contoso.com",
        sender_object_id="8a9b1c2d-3e4f-4061-8283-94a5b6c7d8e9",
        recipient_persona="jordan.patel",
        direction="Intra-org",
        delivery_action="Delivered",
        delivery_location="Inbox",
        email_action="No action taken",
        email_size=89102,
        bulk_complaint_level=0,
        authentication_details="SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        confidence_level='{"Spam":"-1"}',
        attachments=(
            EmailAttachment(
                file_name="Q3_forecast_v3.xlsx",
                extension="xlsx",
                file_type="Excel Workbook",
                file_size=64218,
            ),
        ),
        urls=(
            EmailUrl(
                url="https://contoso-my.sharepoint.com/personal/avery_chen/Q3_forecast_v3.xlsx",
                domain="contoso-my.sharepoint.com",
                location="Body",
            ),
        ),
    ),
    EmailTemplate(
        subject="Avery Chen mentioned you in #engineering",
        sender_display_name="Microsoft Teams",
        sender_from_address="noreply@email.teams.microsoft.com",
        sender_from_domain="email.teams.microsoft.com",
        sender_mail_from_address="noreply@email.teams.microsoft.com",
        sender_mail_from_domain="email.teams.microsoft.com",
        sender_ipv4="52.114.6.45",
        recipient_persona="sam.rivera",
        direction="Inbound",
        delivery_action="Delivered",
        delivery_location="Inbox",
        email_action="No action taken",
        email_size=9412,
        bulk_complaint_level=1,
        authentication_details="SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        confidence_level='{"Spam":"1"}',
        urls=(
            EmailUrl(
                url="https://teams.microsoft.com/l/message/19:abc/1715000000000",
                domain="teams.microsoft.com",
                location="Body",
            ),
        ),
    ),
    EmailTemplate(
        subject="Industry watch: 5 trends shaping Q3",
        sender_display_name="Contoso Marketing",
        sender_from_address="newsletter@mc.contoso-marketing.io",
        sender_from_domain="mc.contoso-marketing.io",
        sender_mail_from_address="bounce-mc@mc.contoso-marketing.io",
        sender_mail_from_domain="mc.contoso-marketing.io",
        sender_ipv4="198.2.180.45",
        recipient_persona="avery.chen",
        direction="Inbound",
        delivery_action="Junked",
        delivery_location="JunkFolder",
        email_action="Move message to junk mail folder",
        email_action_policy="Antispam bulk mail",
        email_action_policy_guid="7e1c8a3b-9d2f-4d3e-b8a2-9c4e9b3d1f6a",
        email_size=31415,
        bulk_complaint_level=7,
        authentication_details="SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        confidence_level='{"Spam":"5"}',
        detection_methods="Bulk mail",
        urls=(
            EmailUrl(
                url="https://mc.contoso-marketing.io/track?c=12345",
                domain="mc.contoso-marketing.io",
                location="Body",
            ),
            EmailUrl(
                url="https://contoso-marketing.io/unsubscribe",
                domain="contoso-marketing.io",
                location="Body",
            ),
        ),
    ),
    EmailTemplate(
        subject="Quarterly SOC update for Northwind",
        sender_display_name="Sam Rivera",
        sender_from_address="sam.rivera@contoso.com",
        sender_from_domain="contoso.com",
        sender_mail_from_address="sam.rivera@contoso.com",
        sender_mail_from_domain="contoso.com",
        sender_object_id="2c3d4e5f-6071-4293-a4b5-c6d7e8f90112",
        sender_ipv4="73.62.18.101",
        recipient_persona="robin.park_acme.com#EXT#",
        direction="Outbound",
        delivery_action="Delivered",
        delivery_location="On-premises/External",
        email_action="No action taken",
        email_size=102488,
        bulk_complaint_level=0,
        authentication_details="SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        confidence_level='{"Spam":"-1"}',
        attachments=(
            EmailAttachment(
                file_name="soc_update_northwind.pdf",
                extension="pdf",
                file_type="PDF Document",
                file_size=91204,
            ),
        ),
        urls=(
            EmailUrl(
                url="https://contoso.com/security/disclosures",
                domain="contoso.com",
                location="Body",
            ),
        ),
    ),
)


_DEFAULT_GRAPH_API_ENDPOINTS: tuple[GraphApiEndpoint, ...] = (
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/users",
        workload="Microsoft.DirectoryServices",
        scope="User.Read.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/users/{user_id}",
        workload="Microsoft.DirectoryServices",
        scope="User.Read.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/users/{user_id}/manager",
        workload="Microsoft.DirectoryServices",
        scope="User.Read.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/users/{user_id}/memberOf",
        workload="Microsoft.DirectoryServices",
        scope="GroupMember.Read.All",
    ),
    GraphApiEndpoint(
        method="PATCH",
        uri="/{ver}/users/{user_id}",
        workload="Microsoft.DirectoryServices",
        scope="User.ReadWrite.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/groups",
        workload="Microsoft.DirectoryServices",
        scope="Group.Read.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/groups/{group_id}/members",
        workload="Microsoft.DirectoryServices",
        scope="GroupMember.Read.All",
    ),
    GraphApiEndpoint(
        method="POST",
        uri="/{ver}/groups/{group_id}/members/$ref",
        workload="Microsoft.DirectoryServices",
        scope="GroupMember.ReadWrite.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/applications",
        workload="Microsoft.DirectoryServices",
        scope="Application.Read.All",
    ),
    GraphApiEndpoint(
        method="POST",
        uri="/{ver}/applications",
        workload="Microsoft.DirectoryServices",
        scope="Application.ReadWrite.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/servicePrincipals",
        workload="Microsoft.DirectoryServices",
        scope="Application.Read.All",
    ),
    GraphApiEndpoint(
        method="POST",
        uri="/{ver}/servicePrincipals/{sp_id}/addPassword",
        workload="Microsoft.DirectoryServices",
        scope="Application.ReadWrite.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/directoryRoles",
        workload="Microsoft.DirectoryServices",
        scope="RoleManagement.Read.Directory",
    ),
    GraphApiEndpoint(
        method="POST",
        uri="/{ver}/directoryRoles/{role_id}/members/$ref",
        workload="Microsoft.DirectoryServices",
        scope="RoleManagement.ReadWrite.Directory",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/identity/conditionalAccess/policies",
        workload="Microsoft.DirectoryServices",
        scope="Policy.Read.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/me/messages",
        workload="Microsoft.Exchange",
        scope="Mail.Read",
    ),
    GraphApiEndpoint(
        method="POST",
        uri="/{ver}/me/sendMail",
        workload="Microsoft.Exchange",
        scope="Mail.Send",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/me/calendar/events",
        workload="Microsoft.Exchange",
        scope="Calendars.Read",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/sites/root/drives",
        workload="Microsoft.SharePoint",
        scope="Files.Read.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/drives/{drive_id}/root/children",
        workload="Microsoft.SharePoint",
        scope="Files.Read.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/teams/{team_id}/channels",
        workload="Microsoft.Teams",
        scope="Channel.ReadBasic.All",
    ),
    GraphApiEndpoint(
        method="POST",
        uri="/{ver}/chats/{chat_id}/messages",
        workload="Microsoft.Teams",
        scope="Chat.ReadWrite",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/auditLogs/signIns",
        workload="Microsoft.Reports",
        scope="AuditLog.Read.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/auditLogs/directoryAudits",
        workload="Microsoft.Reports",
        scope="AuditLog.Read.All",
    ),
    GraphApiEndpoint(
        method="GET",
        uri="/{ver}/security/alerts_v2",
        workload="Microsoft.Security",
        scope="SecurityAlert.Read.All",
    ),
    GraphApiEndpoint(
        method="POST",
        uri="/{ver}/security/runHuntingQuery",
        workload="Microsoft.Security",
        scope="ThreatHunting.Read.All",
    ),
)


# Registry targets feeding DeviceRegistryEvents — Run / IFEO / policy keys
# real hunters watch.
_DEFAULT_REGISTRY_TARGETS: tuple[RegistryTarget, ...] = (
    RegistryTarget(
        key=r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        value_name="OneDrive",
        value_data=r"C:\Users\Avery\AppData\Local\Microsoft\OneDrive\OneDrive.exe /background",
        value_type="REG_SZ",
    ),
    RegistryTarget(
        key=r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
        value_name="Teams",
        value_data=r'"C:\Users\Avery\AppData\Local\Microsoft\Teams\Update.exe" --processStart "Teams.exe"',
        value_type="REG_SZ",
    ),
    RegistryTarget(
        key=r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\sethc.exe",
        value_name="Debugger",
        value_data=r"cmd.exe",
        value_type="REG_SZ",
    ),
    RegistryTarget(
        key=r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\WinDefend",
        value_name="Start",
        value_data="2",
        value_type="REG_DWORD",
    ),
    RegistryTarget(
        key=r"HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows Defender",
        value_name="DisableAntiSpyware",
        value_data="0",
        value_type="REG_DWORD",
    ),
    RegistryTarget(
        key=r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa",
        value_name="RunAsPPL",
        value_data="1",
        value_type="REG_DWORD",
    ),
    RegistryTarget(
        key=r"HKEY_CURRENT_USER\Software\Microsoft\Office\16.0\Word\Security",
        value_name="VBAWarnings",
        value_data="2",
        value_type="REG_DWORD",
    ),
    RegistryTarget(
        key=r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{A4B3C5D6-7890-1234-5678-9ABCDEF01234}",
        value_name="DisplayName",
        value_data="Internal Helper Tool",
        value_type="REG_SZ",
    ),
)


# Defender for Cloud Apps connectors feeding CloudAppEvents.
_DEFAULT_CLOUD_APPS: tuple[CloudApp, ...] = (
    CloudApp(
        name="Microsoft 365",
        app_id=11161,
        instance_id=1001,
        audit_source="Office 365",
        actions=(
            "FileAccessed",
            "FileDownloaded",
            "FileUploaded",
            "FileModified",
            "FileDeleted",
            "FileSyncDownloadedFull",
            "FileSyncUploadedFull",
            "SharingSet",
            "AnonymousLinkCreated",
        ),
    ),
    CloudApp(
        name="Microsoft Exchange Online",
        app_id=20893,
        instance_id=1002,
        audit_source="Office 365",
        actions=(
            "MailItemsAccessed",
            "Send",
            "Update",
            "MoveToDeletedItems",
            "SoftDelete",
            "HardDelete",
            "New-InboxRule",
            "Set-Mailbox",
        ),
    ),
    CloudApp(
        name="Microsoft Teams",
        app_id=28375,
        instance_id=1003,
        audit_source="Office 365",
        actions=(
            "MessageSent",
            "MemberAdded",
            "MemberRemoved",
            "TeamCreated",
            "ChannelAdded",
            "MeetingDetail",
        ),
    ),
    CloudApp(
        name="Salesforce",
        app_id=11114,
        instance_id=1004,
        audit_source="Salesforce",
        actions=(
            "Login",
            "Logout",
            "ReportRun",
            "RecordExported",
            "ApiCall",
            "PasswordChange",
        ),
    ),
    CloudApp(
        name="Box",
        app_id=10489,
        instance_id=1005,
        audit_source="Box",
        actions=(
            "FILE_PREVIEW",
            "DOWNLOAD",
            "UPLOAD",
            "DELETE",
            "SHARE",
            "COLLABORATION_INVITE",
        ),
    ),
    CloudApp(
        name="GitHub",
        app_id=15760,
        instance_id=1006,
        audit_source="GitHub",
        actions=(
            "git.clone",
            "git.push",
            "repo.access",
            "repo.create",
            "oauth_authorization.create",
            "personal_access_token.create",
        ),
    ),
)


# Filenames feeding CloudAppEvents.ObjectName for File-shaped actions.
_DEFAULT_CLOUD_APP_FILE_NAMES: tuple[str, ...] = (
    "Q3_forecast.xlsx",
    "design-spec.docx",
    "customer_list.csv",
    "demo-deck.pptx",
    "build_logs.txt",
    "release-notes.md",
    "contract_v3.pdf",
    "audit_export.zip",
)


# Mail subjects feeding CloudAppEvents.ObjectName for Email-shaped actions.
_DEFAULT_CLOUD_APP_MAIL_SUBJECTS: tuple[str, ...] = (
    "Re: Q3 numbers",
    "FW: NDA draft",
    "Weekly status",
    "Action required: account review",
    "Calendar invite: planning sync",
)


# Group names feeding CloudAppEvents.ActivityObjects for Group-shaped actions.
_DEFAULT_CLOUD_APP_GROUP_NAMES: tuple[str, ...] = (
    "Engineering",
    "Finance",
    "Sales-EMEA",
    "All Hands",
)


# DeviceNetworkEvents ActionType distribution — outbound success dominates.
_DEFAULT_DEVICE_NETWORK_ACTIONS: tuple[DeviceNetworkActionType, ...] = (
    DeviceNetworkActionType(action="ConnectionSuccess", weight=60),
    DeviceNetworkActionType(action="ConnectionFailed", weight=8),
    DeviceNetworkActionType(action="ConnectionAttempt", weight=6),
    DeviceNetworkActionType(action="ConnectionRequest", weight=4),
    DeviceNetworkActionType(action="InboundConnectionAccepted", weight=6),
    DeviceNetworkActionType(action="ListeningConnectionCreated", weight=4),
    DeviceNetworkActionType(action="DnsConnectionInspected", weight=8),
    DeviceNetworkActionType(action="ConnectionFound", weight=4),
)


# Network adapters feeding DeviceNetworkInfo.
_DEFAULT_NETWORK_ADAPTERS: tuple[NetworkAdapter, ...] = (
    NetworkAdapter(
        name="Wi-Fi",
        type="Wireless",
        vendor="Intel Corporation",
        tunnel=None,
        network_category="Private",
        network_name="CONTOSO-CORP",
    ),
    NetworkAdapter(
        name="Ethernet",
        type="Ethernet",
        vendor="Realtek Semiconductor",
        tunnel=None,
        network_category="Domain",
        network_name="contoso.local",
    ),
    NetworkAdapter(
        name="vEthernet (WSL)",
        type="Ethernet",
        vendor="Microsoft Corporation",
        tunnel=None,
        network_category="Private",
        network_name="WSL Internal",
    ),
    NetworkAdapter(
        name="Cisco AnyConnect VPN",
        type="Tunnel",
        vendor="Cisco Systems, Inc.",
        tunnel="Ssh",
        network_category="Domain",
        network_name="contoso-vpn",
    ),
)


# DNS resolvers + default gateways feeding DeviceNetworkInfo.
_DEFAULT_LOCAL_DNS_SERVERS: tuple[str, ...] = (
    "10.0.0.10",
    "10.0.0.11",
    "8.8.8.8",
    "1.1.1.1",
)
_DEFAULT_LOCAL_DEFAULT_GATEWAYS: tuple[str, ...] = (
    "10.10.20.1",
    "10.10.30.1",
    "10.10.40.1",
)


# DeviceRegistryEvents ActionType distribution.
_DEFAULT_DEVICE_REGISTRY_ACTIONS: tuple[DeviceRegistryActionType, ...] = (
    DeviceRegistryActionType(action="RegistryValueSet", weight=60),
    DeviceRegistryActionType(action="RegistryKeyCreated", weight=12),
    DeviceRegistryActionType(action="RegistryValueDeleted", weight=10),
    DeviceRegistryActionType(action="RegistryKeyDeleted", weight=8),
    DeviceRegistryActionType(action="RegistryKeyRenamed", weight=4),
    DeviceRegistryActionType(action="RegistryValueRenamed", weight=4),
    DeviceRegistryActionType(action="RegistryKeyAndValueDeleted", weight=2),
)


# Post-delivery paths feeding EmailPostDeliveryEvents.
_DEFAULT_EMAIL_POST_DELIVERY_PATHS: tuple[EmailPostDeliveryPath, ...] = (
    EmailPostDeliveryPath(
        action="Move to junk",
        action_type="Phish ZAP",
        trigger="ZAP",
        result="Success",
        delivery_location="JunkFolder",
    ),
    EmailPostDeliveryPath(
        action="Move to quarantine",
        action_type="Phish ZAP",
        trigger="ZAP",
        result="Success",
        delivery_location="Quarantine",
    ),
    EmailPostDeliveryPath(
        action="Soft delete",
        action_type="Manual remediation",
        trigger="Admin",
        result="Success",
        delivery_location="Deleted Items",
    ),
    EmailPostDeliveryPath(
        action="Hard delete",
        action_type="Manual remediation",
        trigger="Admin",
        result="Success",
        delivery_location="Deleted Items",
    ),
    EmailPostDeliveryPath(
        action="Move to inbox",
        action_type="User reported not junk",
        trigger="User",
        result="Success",
        delivery_location="Inbox",
    ),
)


# Weighted HTTP outcomes feeding GraphApiAuditEvents.ResponseStatusCode.
_DEFAULT_GRAPH_API_STATUS_CODES: tuple[GraphApiStatusCode, ...] = (
    GraphApiStatusCode(code="200", weight=80),
    GraphApiStatusCode(code="201", weight=4),
    GraphApiStatusCode(code="204", weight=4),
    GraphApiStatusCode(code="400", weight=2),
    GraphApiStatusCode(code="401", weight=2),
    GraphApiStatusCode(code="403", weight=3),
    GraphApiStatusCode(code="404", weight=2),
    GraphApiStatusCode(code="429", weight=2),
    GraphApiStatusCode(code="500", weight=1),
)


# IdentityAccountInfo authentication methods + Defender risk level distribution.
_DEFAULT_IDENTITY_AUTH_METHODS: tuple[str, ...] = ("Credentials", "Federated", "Hybrid")
_DEFAULT_IDENTITY_RISK_LEVELS: tuple[IdentityRiskLevel, ...] = (
    IdentityRiskLevel(level=0, weight=80),
    IdentityRiskLevel(level=1, weight=12),
    IdentityRiskLevel(level=2, weight=6),
    IdentityRiskLevel(level=3, weight=2),
)


# IdentityDirectoryEvents ActionType — group/password churn dominates.
_DEFAULT_IDENTITY_DIRECTORY_ACTIONS: tuple[IdentityDirectoryActionType, ...] = (
    IdentityDirectoryActionType(action="Group Membership changed", weight=32),
    IdentityDirectoryActionType(action="Account Password changed", weight=22),
    IdentityDirectoryActionType(action="Account enabled", weight=8),
    IdentityDirectoryActionType(action="Account disabled", weight=6),
    IdentityDirectoryActionType(action="Group created", weight=4),
    IdentityDirectoryActionType(action="Group deleted", weight=2),
    IdentityDirectoryActionType(action="User created", weight=4),
    IdentityDirectoryActionType(action="User deleted", weight=2),
    IdentityDirectoryActionType(action="Account name changed", weight=3),
    IdentityDirectoryActionType(action="Account display name changed", weight=5),
    IdentityDirectoryActionType(
        action="Domain controller authentication policy changed", weight=1
    ),
    IdentityDirectoryActionType(
        action="Account Constrained Delegation state changed", weight=1
    ),
    IdentityDirectoryActionType(
        action="Account Unconstrained Delegation state changed", weight=1
    ),
    IdentityDirectoryActionType(action="Account Sensitive flag changed", weight=2),
    IdentityDirectoryActionType(
        action="Service Principal Name added to account", weight=4
    ),
    IdentityDirectoryActionType(
        action="Service Principal Name removed from account", weight=3
    ),
)


# Raw IdentityEvents actions — source-side strings, not normalised.
_DEFAULT_IDENTITY_RAW_ACTIONS: tuple[IdentityRawAction, ...] = (
    IdentityRawAction(
        action="UserLoggedIn", application="AzureActiveDirectory", target_kind="user"
    ),
    IdentityRawAction(
        action="UserLoginFailed", application="AzureActiveDirectory", target_kind="user"
    ),
    IdentityRawAction(
        action="Add user.", application="AzureActiveDirectory", target_kind="user"
    ),
    IdentityRawAction(
        action="Delete user.", application="AzureActiveDirectory", target_kind="user"
    ),
    IdentityRawAction(
        action="Update user.", application="AzureActiveDirectory", target_kind="user"
    ),
    IdentityRawAction(
        action="Add member to group.",
        application="AzureActiveDirectory",
        target_kind="group",
    ),
    IdentityRawAction(
        action="Remove member from group.",
        application="AzureActiveDirectory",
        target_kind="group",
    ),
    IdentityRawAction(
        action="Reset user password.",
        application="AzureActiveDirectory",
        target_kind="user",
    ),
    IdentityRawAction(
        action="Add app role assignment to service principal.",
        application="AzureActiveDirectory",
        target_kind="app",
    ),
    IdentityRawAction(
        action="Consent to application.",
        application="AzureActiveDirectory",
        target_kind="app",
    ),
    IdentityRawAction(action="login", application="Okta", target_kind="user"),
    IdentityRawAction(
        action="user.session.start", application="Okta", target_kind="user"
    ),
    IdentityRawAction(
        action="group.user_membership.add", application="Okta", target_kind="group"
    ),
    IdentityRawAction(
        action="policy.lifecycle.update", application="Okta", target_kind="policy"
    ),
)


# Group / app name pools feeding IdentityEvents.TargetObjects.
_DEFAULT_IDENTITY_EVENT_GROUP_NAMES: tuple[str, ...] = (
    "Engineering",
    "Finance",
    "Sales",
    "Domain Admins",
    "All Employees",
    "Sales-EMEA",
)
_DEFAULT_IDENTITY_EVENT_APP_NAMES: tuple[str, ...] = (
    "Salesforce",
    "Box",
    "Workday",
    "ServiceNow",
    "GitHub",
)


# Weighted LogonType + (protocol, port) for IdentityLogonEvents.
_DEFAULT_IDENTITY_LOGON_TYPES: tuple[IdentityLogonType, ...] = (
    IdentityLogonType(logon_type="Network", weight=50),
    IdentityLogonType(logon_type="Interactive", weight=18),
    IdentityLogonType(logon_type="RemoteInteractive", weight=12),
    IdentityLogonType(logon_type="Service", weight=8),
    IdentityLogonType(logon_type="Batch", weight=4),
    IdentityLogonType(logon_type="Unlock", weight=4),
    IdentityLogonType(logon_type="NetworkCleartext", weight=2),
    IdentityLogonType(logon_type="CachedInteractive", weight=2),
)
_DEFAULT_IDENTITY_LOGON_PROTOCOLS: tuple[IdentityLogonProtocol, ...] = (
    IdentityLogonProtocol(protocol="Kerberos", port=88, weight=70),
    IdentityLogonProtocol(protocol="Ntlm", port=445, weight=22),
    IdentityLogonProtocol(protocol="Ldap", port=389, weight=4),
    IdentityLogonProtocol(protocol="LdapSecure", port=636, weight=4),
)
_DEFAULT_IDENTITY_LOGON_FAILURE_REASONS: tuple[str, ...] = (
    "WrongPassword",
    "AccountDisabled",
    "AccountExpired",
    "AccountLockedOut",
    "PasswordExpired",
    "NoSuchUser",
    "TimeSkew",
    "SmartcardRequired",
)


# IdentityQueryEvents — LDAP / SAMR / DNS recon shapes + target pools.
_DEFAULT_IDENTITY_QUERY_KINDS: tuple[IdentityQueryKind, ...] = (
    IdentityQueryKind(query_type="QueryUser", protocol="Ldap", port=389, weight=35),
    IdentityQueryKind(query_type="QueryGroup", protocol="Ldap", port=389, weight=25),
    IdentityQueryKind(
        query_type="EnumerateUsers", protocol="Samr", port=445, weight=12
    ),
    IdentityQueryKind(
        query_type="EnumerateGroups", protocol="Samr", port=445, weight=8
    ),
    IdentityQueryKind(query_type="QueryComputer", protocol="Ldap", port=389, weight=8),
    IdentityQueryKind(query_type="QueryDomain", protocol="Ldap", port=389, weight=5),
    IdentityQueryKind(query_type="Resolve", protocol="Dns", port=53, weight=7),
)
_DEFAULT_IDENTITY_QUERY_GROUP_TARGETS: tuple[str, ...] = (
    "Domain Admins",
    "Enterprise Admins",
    "Schema Admins",
    "Backup Operators",
    "Account Operators",
    "Server Operators",
    "Engineering",
    "Finance",
    "All Employees",
)
_DEFAULT_IDENTITY_QUERY_COMPUTER_TARGETS: tuple[str, ...] = (
    "DC01",
    "DC02",
    "FS01",
    "EXCH01",
    "CRM-DB-PROD",
    "BUILD-AGENT-03",
)


# Safe Links outcomes + source workloads feeding UrlClickEvents.
_DEFAULT_URL_CLICK_OUTCOMES: tuple[UrlClickOutcome, ...] = (
    UrlClickOutcome(action_type="ClickAllowed", is_clicked_through=True, weight=86),
    UrlClickOutcome(
        action_type="Blockpage",
        is_clicked_through=False,
        threat_types="Phish",
        weight=5,
    ),
    UrlClickOutcome(
        action_type="BlockpageOverride",
        is_clicked_through=True,
        threat_types="Phish",
        weight=2,
    ),
    UrlClickOutcome(
        action_type="ClickBlocked",
        is_clicked_through=False,
        threat_types="Malware",
        weight=3,
    ),
    UrlClickOutcome(
        action_type="PendingDetonationPage", is_clicked_through=True, weight=4
    ),
)
_DEFAULT_URL_CLICK_WORKLOADS: tuple[WeightedWorkload, ...] = (
    WeightedWorkload(workload="Email", weight=75),
    WeightedWorkload(workload="Office", weight=12),
    WeightedWorkload(workload="Teams", weight=13),
)


# DeviceLogonEvents LogonType distribution — Network / Interactive dominate
# on a managed endpoint.
_DEFAULT_DEVICE_LOGON_TYPES: tuple[DeviceLogonType, ...] = (
    DeviceLogonType(logon_type="Network", weight=50),
    DeviceLogonType(logon_type="Interactive", weight=18),
    DeviceLogonType(logon_type="RemoteInteractive", weight=10),
    DeviceLogonType(logon_type="Service", weight=8),
    DeviceLogonType(logon_type="Batch", weight=4),
    DeviceLogonType(logon_type="Unlock", weight=4),
    DeviceLogonType(logon_type="NetworkCleartext", weight=2),
    DeviceLogonType(logon_type="CachedInteractive", weight=4),
)


# Authentication protocols feeding DeviceLogonEvents.Protocol.
_DEFAULT_DEVICE_LOGON_PROTOCOLS: tuple[str, ...] = ("Kerberos", "Ntlm", "NetLogon")


# Failure reasons feeding DeviceLogonEvents.FailureReason — populated only
# when ActionType == "LogonFailed".
_DEFAULT_DEVICE_LOGON_FAILURE_REASONS: tuple[str, ...] = (
    "InvalidUserNameOrPassword",
    "AccountDisabled",
    "AccountExpired",
    "AccountLockedOut",
    "PasswordExpired",
    "UnknownUser",
    "TimeSkew",
    "SmartcardRequired",
)


# Curated DLL pool feeding DeviceImageLoadEvents. FolderPath stays consistent
# with the file name (Windows assigns kernel32.dll, ntdll.dll, etc. specific
# locations on disk).
_DEFAULT_LOADED_LIBRARIES: tuple[LoadedLibrary, ...] = (
    LoadedLibrary(file_name="kernel32.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="ntdll.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="user32.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="advapi32.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="ws2_32.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="crypt32.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="ole32.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="shell32.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="rpcrt4.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="msvcrt.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="amsi.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="wininet.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(file_name="urlmon.dll", folder_path=r"C:\Windows\System32"),
    LoadedLibrary(
        file_name="System.Management.Automation.dll",
        folder_path=r"C:\Windows\assembly\NativeImages_v4.0.30319_64",
    ),
)


# Real code-signing certs feeding DeviceFileCertificateInfo.
_DEFAULT_CODE_SIGNING_CERTIFICATES: tuple[CodeSigningCertificate, ...] = (
    CodeSigningCertificate(
        subject="Microsoft Windows",
        issuer="Microsoft Windows Production PCA 2011",
        serial="33000002ED2C45E4C145CF48E7000000000002",
        is_root_microsoft=True,
        signature_type="Embedded",
    ),
    CodeSigningCertificate(
        subject="Microsoft Corporation",
        issuer="Microsoft Code Signing PCA 2011",
        serial="33000003318FA52A4D8F2E1F2A000000000333",
        is_root_microsoft=True,
        signature_type="Embedded",
    ),
    CodeSigningCertificate(
        subject="Google LLC",
        issuer="DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1",
        serial="0AA89F4DEF6C2C4DBD3C1AB37B17EBE5",
        is_root_microsoft=False,
        signature_type="Embedded",
    ),
    CodeSigningCertificate(
        subject="Adobe Inc.",
        issuer="DigiCert SHA2 Assured ID Code Signing CA",
        serial="0F4F9D2BB12B4E8DAF3E2F46A1F19C2C",
        is_root_microsoft=False,
        signature_type="Embedded",
    ),
    CodeSigningCertificate(
        subject="Mozilla Corporation",
        issuer="DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1",
        serial="0EE0BCB37BFE32C7B1024F8AF8E1E2F1",
        is_root_microsoft=False,
        signature_type="Embedded",
    ),
    CodeSigningCertificate(
        subject="GitHub, Inc.",
        issuer="DigiCert SHA2 Assured ID Code Signing CA",
        serial="00B0BCDFA1A0CF24E5BCEDE53C2F7B8B81",
        is_root_microsoft=False,
        signature_type="Embedded",
    ),
    CodeSigningCertificate(
        subject="Slack Technologies, LLC",
        issuer="Sectigo RSA Code Signing CA",
        serial="0066AB7DC4B0A4E5BCEDE53C2F7B8B82A1",
        is_root_microsoft=False,
        signature_type="Embedded",
    ),
)


# Filenames DeviceFileCertificateInfo derives a stable SHA-1 from. Hashes are
# computed from the name so cross-table pivots line up with other Device*
# tables.
_DEFAULT_SIGNED_FILES: tuple[str, ...] = (
    "explorer.exe",
    "powershell.exe",
    "svchost.exe",
    "MsMpEng.exe",
    "msedge.exe",
    "chrome.exe",
    "outlook.exe",
    "winword.exe",
)


# CRL distribution points feeding DeviceFileCertificateInfo.CrlDistributionPointUrls.
_DEFAULT_CRL_URLS: tuple[str, ...] = (
    "http://www.microsoft.com/pkiops/crl/MicCodSigPCA_2011-07-08.crl",
    "http://crl3.digicert.com/DigiCertTrustedG4CodeSigningRSA4096SHA384.crl",
    "http://crl.sectigo.com/SectigoRSACodeSigningCA.crl",
)


# DeviceEvents ActionType pool — `shape` routes the row to a file / network /
# registry / none auxiliary block. Default distribution is uniform; weights
# let profiles bias toward a specific behaviour (e.g. ASR-heavy, AV-heavy).
_DEFAULT_DEVICE_EVENT_ACTIONS: tuple[DeviceEventAction, ...] = (
    DeviceEventAction(action="AntivirusDetection", shape="file"),
    DeviceEventAction(action="AntivirusDetectionAndBlock", shape="file"),
    DeviceEventAction(action="AntivirusReport", shape="file"),
    DeviceEventAction(action="ExploitGuardNetworkProtectionBlocked", shape="network"),
    DeviceEventAction(action="ExploitGuardNetworkProtectionAudited", shape="network"),
    DeviceEventAction(action="AsrLsassCredentialTheftAudited", shape="none"),
    DeviceEventAction(action="AsrOfficeChildProcessBlocked", shape="file"),
    DeviceEventAction(action="AsrUntrustedExecutableAudited", shape="file"),
    DeviceEventAction(action="BrowserLaunchedToOpenUrl", shape="network"),
    DeviceEventAction(action="ScreenshotTaken", shape="none"),
    DeviceEventAction(action="PowerShellCommand", shape="none"),
    DeviceEventAction(action="AmsiScriptDetection", shape="none"),
    DeviceEventAction(action="ControlFlowGuardViolation", shape="none"),
    DeviceEventAction(action="TamperingAttempt", shape="registry"),
    DeviceEventAction(action="AppControlPolicyApplied", shape="none"),
    DeviceEventAction(action="OpenProcessApiCall", shape="none"),
    DeviceEventAction(action="UsbDriveMounted", shape="none"),
    DeviceEventAction(action="UsbDriveUnmounted", shape="none"),
    DeviceEventAction(action="UserAccountAddedToLocalGroup", shape="none"),
)


# File templates feeding DeviceFileEvents. `{user}` is rendered to the picked
# user's sam_account_name. UNC folders surface as ShareName + Request* on
# NetworkShare* actions.
_DEFAULT_FILE_TEMPLATES: tuple[FileTemplate, ...] = (
    # Browser downloads — carry FileOrigin* fields.
    FileTemplate(
        folder_template=r"C:\Users\{user}\Downloads",
        file_name="invoice-2026-Q1.pdf",
        kind="download",
    ),
    FileTemplate(
        folder_template=r"C:\Users\{user}\Downloads",
        file_name="purchase-order.pdf",
        kind="download",
    ),
    FileTemplate(
        folder_template=r"C:\Users\{user}\Downloads",
        file_name="setup.exe",
        kind="download",
    ),
    FileTemplate(
        folder_template=r"C:\Users\{user}\Downloads",
        file_name="vpn-installer.msi",
        kind="download",
    ),
    FileTemplate(
        folder_template=r"C:\Users\{user}\Downloads",
        file_name="report.xlsx",
        kind="download",
    ),
    FileTemplate(
        folder_template=r"C:\Users\{user}\Downloads",
        file_name="presentation.pptx",
        kind="download",
    ),
    FileTemplate(
        folder_template=r"C:\Users\{user}\Downloads",
        file_name="screenshot.png",
        kind="download",
    ),
    # Locally produced documents — no FileOrigin*.
    FileTemplate(
        folder_template=r"C:\Users\{user}\Documents",
        file_name="meeting-minutes.docx",
        kind="doc",
    ),
    FileTemplate(
        folder_template=r"C:\Users\{user}\Documents",
        file_name="expenses.xlsx",
        kind="doc",
    ),
    FileTemplate(
        folder_template=r"C:\Users\{user}\Desktop",
        file_name="todo.txt",
        kind="doc",
    ),
    # Temp / cache — high-volume, no origin metadata.
    FileTemplate(
        folder_template=r"C:\Users\{user}\AppData\Local\Temp",
        file_name="tmp1A2B.tmp",
        kind="temp",
    ),
    FileTemplate(
        folder_template=r"C:\Users\{user}\AppData\Local\Microsoft\Outlook",
        file_name="Outlook.ost",
        kind="temp",
    ),
    FileTemplate(
        folder_template=r"C:\Windows\Temp",
        file_name="WERE6A9.tmp",
        kind="temp",
    ),
    FileTemplate(
        folder_template=r"C:\ProgramData\Microsoft\Windows Defender\Scans",
        file_name="MpCacheStore.bin",
        kind="temp",
    ),
    # SMB shares — UNC paths populate ShareName + Request* on share actions.
    FileTemplate(
        folder_template=r"\\fileserver01\Shared\HR",
        file_name="employee-policy.pdf",
        kind="share",
    ),
    FileTemplate(
        folder_template=r"\\fileserver01\Shared\Finance",
        file_name="Q4-budget.xlsx",
        kind="share",
    ),
    FileTemplate(
        folder_template=r"\\fileserver01\Shared\Engineering",
        file_name="design-spec.docx",
        kind="share",
    ),
)


# DeviceFileEvents ActionType distribution — FileCreated/FileModified dominate.
_DEFAULT_FILE_ACTION_TYPES: tuple[FileActionType, ...] = (
    FileActionType(action="FileCreated", weight=45),
    FileActionType(action="FileModified", weight=25),
    FileActionType(action="FileDeleted", weight=15),
    FileActionType(action="FileRenamed", weight=10),
    FileActionType(action="FileShredded", weight=2),
    FileActionType(action="NetworkShareFileSynchronized", weight=3),
)


# Pool of (label, sublabel) pairs DeviceFileEvents picks from for randomly
# labelled local Office documents. HR / Finance share paths are still
# auto-classified by the generator regardless of this pool.
_DEFAULT_FILE_SENSITIVITY_LABELS: tuple[SensitivityLabel, ...] = (
    SensitivityLabel(label="General"),
    SensitivityLabel(label="Confidential", sublabel="All Employees"),
    SensitivityLabel(label="Highly Confidential", sublabel="Finance"),
    SensitivityLabel(label="Highly Confidential", sublabel="HR"),
)


# Hosts DeviceFileEvents uses to render `FileOriginUrl` / `FileOriginReferrerUrl`
# for downloaded files.
_DEFAULT_FILE_DOWNLOAD_HOSTS: tuple[str, ...] = (
    "files.contoso.com",
    "cdn.example.com",
    "downloads.example.net",
    "share.acme-files.example.com",
)


# Outbound (port, url) pairs feeding DeviceNetworkEvents.{RemotePort,RemoteUrl}.
# `url=None` is used for ports unrelated to a hostname.
_DEFAULT_NETWORK_DESTINATIONS: tuple[NetworkDestination, ...] = (
    NetworkDestination(port=443, url="graph.microsoft.com"),
    NetworkDestination(port=443, url="outlook.office365.com"),
    NetworkDestination(port=443, url="login.microsoftonline.com"),
    NetworkDestination(port=443, url="github.com"),
    NetworkDestination(port=443, url="api.github.com"),
    NetworkDestination(port=443, url="windowsupdate.microsoft.com"),
    NetworkDestination(port=53, url=None),
    NetworkDestination(port=445, url=None),
    NetworkDestination(port=88, url=None),
    NetworkDestination(port=389, url=None),
    NetworkDestination(port=3389, url=None),
    NetworkDestination(port=80, url="ctldl.windowsupdate.com"),
)


# Azure regions graph.microsoft.com requests terminate in — feeds
# GraphApiAuditEvents.Location.
_DEFAULT_GRAPH_API_LOCATIONS: tuple[str, ...] = (
    "westeurope",
    "northeurope",
    "eastus",
    "westus2",
    "southeastasia",
    "uksouth",
)


_DEFAULT_CA_POLICIES: tuple[ConditionalAccessPolicy, ...] = (
    ConditionalAccessPolicy(
        id="8d2d8c45-2f9f-4c5e-8b1a-1c12fbb1d9e6",
        displayName="Require MFA for all users",
        enforcedGrantControls=("Mfa",),
    ),
    ConditionalAccessPolicy(
        id="2f0a8d9e-3a8c-4d20-9c7b-1d6f8a4d3a1b",
        displayName="Block legacy authentication",
        enforcedGrantControls=("Block",),
    ),
    ConditionalAccessPolicy(
        id="9c4e9b3d-1f6a-4d3e-b8a2-7e1c8a3b9d2f",
        displayName="Require compliant device for admin portals",
        enforcedGrantControls=("CompliantDevice",),
    ),
)


class World(BaseModel):
    """Immutable per-run fixture container; frozen + hashable for lru_cache.

    Pool fields use `WeightedPool[Item]` so each pool carries its own
    sampling mode (`random=True` ⇒ uniform; `random=False` ⇒ weighted with
    a per-entry `weight`). Test/builder code may still pass plain tuples
    or lists — they are auto-wrapped into a uniform pool."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str = "a1b2c3d4-5e6f-4071-8293-94a5b6c7d8e9"
    tenant_domain: str = "contoso.com"
    on_prem_ad_domain: str = "contoso.local"
    on_prem_netbios_domain: str = "CONTOSO"
    on_prem_sid_prefix: str = "S-1-5-21-1004336348-1177238915-682003330"

    domain_controllers: WeightedPool[DomainController] = _pool(
        _DEFAULT_DOMAIN_CONTROLLERS
    )
    devices: WeightedPool[Device] = _pool(_DEFAULT_DEVICES)
    processes: WeightedPool[Process] = _pool(_DEFAULT_PROCESSES)
    users: WeightedPool[User] = _pool(_DEFAULT_USERS)
    ips: WeightedPool[IPEntry] = _pool(_DEFAULT_IPS)
    user_agents: WeightedPool[UserAgentEntry] = _pool(_DEFAULT_USER_AGENTS)
    client_apps: WeightedPool[ClientApp] = _pool(_DEFAULT_CLIENT_APPS)
    service_principals: WeightedPool[ServicePrincipal] = _pool(
        _DEFAULT_SERVICE_PRINCIPALS
    )
    resources: WeightedPool[Resource] = _pool(_DEFAULT_RESOURCES)
    groups: WeightedPool[Group] = _pool(_DEFAULT_GROUPS)
    graph_api_endpoints: WeightedPool[GraphApiEndpoint] = _pool(
        _DEFAULT_GRAPH_API_ENDPOINTS
    )
    graph_api_locations: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_GRAPH_API_LOCATIONS
    )
    network_destinations: WeightedPool[NetworkDestination] = _pool(
        _DEFAULT_NETWORK_DESTINATIONS
    )
    registry_targets: WeightedPool[RegistryTarget] = _pool(_DEFAULT_REGISTRY_TARGETS)
    device_event_actions: WeightedPool[DeviceEventAction] = _pool(
        _DEFAULT_DEVICE_EVENT_ACTIONS
    )
    code_signing_certificates: WeightedPool[CodeSigningCertificate] = _pool(
        _DEFAULT_CODE_SIGNING_CERTIFICATES
    )
    signed_files: WeightedPool[ScalarEntry] = _scalar_pool(_DEFAULT_SIGNED_FILES)
    crl_urls: WeightedPool[ScalarEntry] = _scalar_pool(_DEFAULT_CRL_URLS)
    loaded_libraries: WeightedPool[LoadedLibrary] = _pool(_DEFAULT_LOADED_LIBRARIES)
    device_logon_types: WeightedPool[DeviceLogonType] = _pool(
        _DEFAULT_DEVICE_LOGON_TYPES
    )
    device_logon_protocols: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_DEVICE_LOGON_PROTOCOLS
    )
    device_logon_failure_reasons: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_DEVICE_LOGON_FAILURE_REASONS
    )
    cloud_apps: WeightedPool[CloudApp] = _pool(_DEFAULT_CLOUD_APPS)
    cloud_app_file_names: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_CLOUD_APP_FILE_NAMES
    )
    cloud_app_mail_subjects: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_CLOUD_APP_MAIL_SUBJECTS
    )
    cloud_app_group_names: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_CLOUD_APP_GROUP_NAMES
    )
    device_network_action_types: WeightedPool[DeviceNetworkActionType] = _pool(
        _DEFAULT_DEVICE_NETWORK_ACTIONS
    )
    network_adapters: WeightedPool[NetworkAdapter] = _pool(_DEFAULT_NETWORK_ADAPTERS)
    local_dns_servers: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_LOCAL_DNS_SERVERS
    )
    local_default_gateways: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_LOCAL_DEFAULT_GATEWAYS
    )
    device_registry_action_types: WeightedPool[DeviceRegistryActionType] = _pool(
        _DEFAULT_DEVICE_REGISTRY_ACTIONS
    )
    email_post_delivery_paths: WeightedPool[EmailPostDeliveryPath] = _pool(
        _DEFAULT_EMAIL_POST_DELIVERY_PATHS
    )
    graph_api_status_codes: WeightedPool[GraphApiStatusCode] = _pool(
        _DEFAULT_GRAPH_API_STATUS_CODES
    )
    identity_auth_methods: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_IDENTITY_AUTH_METHODS
    )
    identity_risk_levels: WeightedPool[IdentityRiskLevel] = _pool(
        _DEFAULT_IDENTITY_RISK_LEVELS
    )
    identity_directory_action_types: WeightedPool[IdentityDirectoryActionType] = _pool(
        _DEFAULT_IDENTITY_DIRECTORY_ACTIONS
    )
    identity_raw_actions: WeightedPool[IdentityRawAction] = _pool(
        _DEFAULT_IDENTITY_RAW_ACTIONS
    )
    identity_event_group_names: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_IDENTITY_EVENT_GROUP_NAMES
    )
    identity_event_app_names: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_IDENTITY_EVENT_APP_NAMES
    )
    identity_logon_types: WeightedPool[IdentityLogonType] = _pool(
        _DEFAULT_IDENTITY_LOGON_TYPES
    )
    identity_logon_protocols: WeightedPool[IdentityLogonProtocol] = _pool(
        _DEFAULT_IDENTITY_LOGON_PROTOCOLS
    )
    identity_logon_failure_reasons: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_IDENTITY_LOGON_FAILURE_REASONS
    )
    identity_query_kinds: WeightedPool[IdentityQueryKind] = _pool(
        _DEFAULT_IDENTITY_QUERY_KINDS
    )
    identity_query_group_targets: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_IDENTITY_QUERY_GROUP_TARGETS
    )
    identity_query_computer_targets: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_IDENTITY_QUERY_COMPUTER_TARGETS
    )
    url_click_outcomes: WeightedPool[UrlClickOutcome] = _pool(
        _DEFAULT_URL_CLICK_OUTCOMES
    )
    url_click_workloads: WeightedPool[WeightedWorkload] = _pool(
        _DEFAULT_URL_CLICK_WORKLOADS
    )
    file_templates: WeightedPool[FileTemplate] = _pool(_DEFAULT_FILE_TEMPLATES)
    file_action_types: WeightedPool[FileActionType] = _pool(_DEFAULT_FILE_ACTION_TYPES)
    file_sensitivity_labels: WeightedPool[SensitivityLabel] = _pool(
        _DEFAULT_FILE_SENSITIVITY_LABELS
    )
    file_download_hosts: WeightedPool[ScalarEntry] = _scalar_pool(
        _DEFAULT_FILE_DOWNLOAD_HOSTS
    )
    conditional_access_policies: WeightedPool[ConditionalAccessPolicy] = _pool(
        _DEFAULT_CA_POLICIES
    )
    entra_sign_in_error_codes: WeightedPool[WeightedErrorCode] = _pool(
        _DEFAULT_ENTRA_SIGN_IN_ERROR_CODES
    )
    entra_spn_sign_in_error_codes: WeightedPool[WeightedErrorCode] = _pool(
        _DEFAULT_ENTRA_SPN_SIGN_IN_ERROR_CODES
    )
    email_templates: WeightedPool[EmailTemplate] = _pool(_DEFAULT_EMAIL_TEMPLATES)

    @model_validator(mode="before")
    @classmethod
    def _wrap_pools(cls, data):
        return _auto_wrap_pools(cls, data)


class Overrides(BaseModel):
    """YAML patch on World defaults; collection overrides replace, never merge.

    Each pool override accepts two YAML shapes:
      • a bare list of items → uniform sampling (current default).
      • a wrapper `{random: false, entries: [...]}` → every entry must
        declare `weight`; sampling is weighted in generators."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: Optional[str] = None
    tenant_domain: Optional[str] = None
    on_prem_ad_domain: Optional[str] = None
    on_prem_netbios_domain: Optional[str] = None
    on_prem_sid_prefix: Optional[str] = None

    domain_controllers: Optional[WeightedPool[DomainController]] = None
    devices: Optional[WeightedPool[Device]] = None
    processes: Optional[WeightedPool[Process]] = None
    users: Optional[WeightedPool[User]] = None
    ips: Optional[WeightedPool[IPEntry]] = None
    user_agents: Optional[WeightedPool[UserAgentEntry]] = None
    resources: Optional[WeightedPool[Resource]] = None
    client_apps: Optional[WeightedPool[ClientApp]] = None
    service_principals: Optional[WeightedPool[ServicePrincipal]] = None
    groups: Optional[WeightedPool[Group]] = None
    graph_api_endpoints: Optional[WeightedPool[GraphApiEndpoint]] = None
    graph_api_locations: Optional[WeightedPool[ScalarEntry]] = None
    network_destinations: Optional[WeightedPool[NetworkDestination]] = None
    registry_targets: Optional[WeightedPool[RegistryTarget]] = None
    device_event_actions: Optional[WeightedPool[DeviceEventAction]] = None
    code_signing_certificates: Optional[WeightedPool[CodeSigningCertificate]] = None
    signed_files: Optional[WeightedPool[ScalarEntry]] = None
    crl_urls: Optional[WeightedPool[ScalarEntry]] = None
    loaded_libraries: Optional[WeightedPool[LoadedLibrary]] = None
    device_logon_types: Optional[WeightedPool[DeviceLogonType]] = None
    device_logon_protocols: Optional[WeightedPool[ScalarEntry]] = None
    device_logon_failure_reasons: Optional[WeightedPool[ScalarEntry]] = None
    cloud_apps: Optional[WeightedPool[CloudApp]] = None
    cloud_app_file_names: Optional[WeightedPool[ScalarEntry]] = None
    cloud_app_mail_subjects: Optional[WeightedPool[ScalarEntry]] = None
    cloud_app_group_names: Optional[WeightedPool[ScalarEntry]] = None
    device_network_action_types: Optional[WeightedPool[DeviceNetworkActionType]] = None
    network_adapters: Optional[WeightedPool[NetworkAdapter]] = None
    local_dns_servers: Optional[WeightedPool[ScalarEntry]] = None
    local_default_gateways: Optional[WeightedPool[ScalarEntry]] = None
    device_registry_action_types: Optional[WeightedPool[DeviceRegistryActionType]] = (
        None
    )
    email_post_delivery_paths: Optional[WeightedPool[EmailPostDeliveryPath]] = None
    graph_api_status_codes: Optional[WeightedPool[GraphApiStatusCode]] = None
    identity_auth_methods: Optional[WeightedPool[ScalarEntry]] = None
    identity_risk_levels: Optional[WeightedPool[IdentityRiskLevel]] = None
    identity_directory_action_types: Optional[
        WeightedPool[IdentityDirectoryActionType]
    ] = None
    identity_raw_actions: Optional[WeightedPool[IdentityRawAction]] = None
    identity_event_group_names: Optional[WeightedPool[ScalarEntry]] = None
    identity_event_app_names: Optional[WeightedPool[ScalarEntry]] = None
    identity_logon_types: Optional[WeightedPool[IdentityLogonType]] = None
    identity_logon_protocols: Optional[WeightedPool[IdentityLogonProtocol]] = None
    identity_logon_failure_reasons: Optional[WeightedPool[ScalarEntry]] = None
    identity_query_kinds: Optional[WeightedPool[IdentityQueryKind]] = None
    identity_query_group_targets: Optional[WeightedPool[ScalarEntry]] = None
    identity_query_computer_targets: Optional[WeightedPool[ScalarEntry]] = None
    url_click_outcomes: Optional[WeightedPool[UrlClickOutcome]] = None
    url_click_workloads: Optional[WeightedPool[WeightedWorkload]] = None
    file_templates: Optional[WeightedPool[FileTemplate]] = None
    file_action_types: Optional[WeightedPool[FileActionType]] = None
    file_sensitivity_labels: Optional[WeightedPool[SensitivityLabel]] = None
    file_download_hosts: Optional[WeightedPool[ScalarEntry]] = None
    conditional_access_policies: Optional[WeightedPool[ConditionalAccessPolicy]] = None
    entra_sign_in_error_codes: Optional[WeightedPool[WeightedErrorCode]] = None
    entra_spn_sign_in_error_codes: Optional[WeightedPool[WeightedErrorCode]] = None
    email_templates: Optional[WeightedPool[EmailTemplate]] = None

    @model_validator(mode="before")
    @classmethod
    def _wrap_pools(cls, data):
        return _auto_wrap_pools(cls, data)


class Profile(BaseModel):
    """Top-level YAML profile — `tables` and `overrides` are both optional."""

    model_config = ConfigDict(extra="forbid")

    tables: Optional[list[str]] = None
    overrides: Optional[Overrides] = None

    def build_world(self) -> World:
        if self.overrides is None:
            return World()
        return World(**self.overrides.model_dump(exclude_none=True))
