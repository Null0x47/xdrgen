"""Single-source-of-truth for the runtime world telemetry generators sample from.

`World` is a frozen Pydantic model holding every fixture (tenant identity
scalars, users, IPs, user-agents, domain controllers, client apps, resources,
conditional access policies). Generators take a `World` as a parameter — they
never read or mutate module-level state. A `World` instance is built exactly
once per `xdrgen generate` run, from `Profile.build_world()`, and threaded
through every event.

`Profile` and `Overrides` are the YAML-shape models. `Overrides` mirrors `World`
field-for-field but every field is `Optional`, modelling the patch that the
user's YAML supplies on top of the defaults.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """A tenant user / service account / guest. All fields except the four
    identity essentials default sensibly so YAML overrides can stay terse."""

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


class DomainController(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    ip: str
    device_id: str


class Process(BaseModel):
    """An entry in the curated `InitiatingProcess*` catalogue used by the
    Device* generators. Each row is one process Defender for Endpoint
    surfaces as the initiator of an event — `cmd.exe`, `powershell.exe`,
    `MsMpEng.exe`, … — paired with the version-info, signing posture,
    typical command lines, and parent process the real binary carries.
    Hashes are derived from `file_name` at runtime; supplying them in
    YAML would be redundant."""

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


class Device(BaseModel):
    """A managed endpoint reported on by Microsoft Defender for Endpoint.

    Drives every `Device*` table (`DeviceEvents`, `DeviceProcessEvents`,
    `DeviceLogonEvents`, …). The fixture pool is intentionally separate from
    `User.device_name` / `User.device_id` (which only stamp identity-side
    rows) — endpoint events need richer context: OS platform, MAC, primary
    local/public IP, machine group, and a back-link to the primary user."""

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


class IPEntry(BaseModel):
    """A source IP paired with its geolocation. Real Defender events are
    enriched from the same IP-to-geo table, so City / State / Country / ISP /
    Lat / Long must stay aligned per IP."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ip: str
    city: str
    state: str
    country: str
    isp: str
    category: str  # Cloud provider | Corporate | ISP
    latitude: str
    longitude: str


class UserAgentEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ua: str
    platform: str
    device_type: str  # Workstation | Mobile
    browser: str


class Resource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    id: str


class ClientApp(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    app_id: str


class Group(BaseModel):
    """A directory group (Microsoft Entra ID security/M365 group). Surfaces
    as the `{group_id}` path segment in `GraphApiAuditEvents.RequestUri`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    id: str


class ConditionalAccessPolicy(BaseModel):
    """Field names mirror Microsoft Graph's camelCase shape because the
    payload is serialised straight into the `ConditionalAccessPolicies` JSON
    column on EntraIdSignInEvents."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    displayName: str
    enforcedGrantControls: tuple[str, ...] = ()
    enforcedSessionControls: tuple[str, ...] = ()


class WeightedErrorCode(BaseModel):
    """An Entra ID `ErrorCode` value with a sampling weight and an optional
    short description. The weight is relative — `[(0, 80), (50126, 5)]` means
    success outweighs InvalidUserNameOrPassword 16:1. The description, when
    provided, surfaces in `AuthenticationProcessingDetails` so failed sign-ins
    carry a realistic processor message instead of a bare error number."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: int
    weight: int
    description: Optional[str] = None


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


# Expanded vocabulary of real Entra ID interactive / non-interactive sign-in
# error codes. Codes and descriptions track the published catalogue at
# https://learn.microsoft.com/azure/active-directory/develop/reference-error-codes
# Weights are tuned to mirror a healthy tenant — ~80% success with a long tail
# dominated by credential and MFA friction. Override `entra_sign_in_error_codes`
# in YAML to reshape the distribution (e.g. simulate a password-spray spike).
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


# Service-principal sign-ins fail more rarely than user sign-ins and almost
# always over secret / consent issues rather than credential typos. The
# weights bias toward success and the long tail covers the failure modes a
# detection engineer would actually want to see in their telemetry.
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
    """Immutable per-run container for all tenant + fixture data.

    Built once via `Profile.build_world()` and threaded into every generator
    call. Generators read; never mutate. Frozen + tuple-typed collections make
    it deeply immutable AND hashable, which lets `EmailCorpus` cache itself
    per-World via `functools.lru_cache`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str = "a1b2c3d4-5e6f-4071-8293-94a5b6c7d8e9"
    tenant_domain: str = "contoso.com"
    on_prem_ad_domain: str = "contoso.local"
    on_prem_netbios_domain: str = "CONTOSO"
    on_prem_sid_prefix: str = "S-1-5-21-1004336348-1177238915-682003330"

    domain_controllers: tuple[DomainController, ...] = _DEFAULT_DOMAIN_CONTROLLERS
    devices: tuple[Device, ...] = _DEFAULT_DEVICES
    processes: tuple[Process, ...] = _DEFAULT_PROCESSES
    users: tuple[User, ...] = _DEFAULT_USERS
    ips: tuple[IPEntry, ...] = _DEFAULT_IPS
    user_agents: tuple[UserAgentEntry, ...] = _DEFAULT_USER_AGENTS
    client_apps: tuple[ClientApp, ...] = _DEFAULT_CLIENT_APPS
    resources: tuple[Resource, ...] = _DEFAULT_RESOURCES
    groups: tuple[Group, ...] = _DEFAULT_GROUPS
    conditional_access_policies: tuple[ConditionalAccessPolicy, ...] = (
        _DEFAULT_CA_POLICIES
    )
    entra_sign_in_error_codes: tuple[WeightedErrorCode, ...] = (
        _DEFAULT_ENTRA_SIGN_IN_ERROR_CODES
    )
    entra_spn_sign_in_error_codes: tuple[WeightedErrorCode, ...] = (
        _DEFAULT_ENTRA_SPN_SIGN_IN_ERROR_CODES
    )


class Overrides(BaseModel):
    """YAML-shape patch applied on top of World defaults.

    Every field mirrors `World` but is `Optional`. Unset fields keep their
    defaults; set fields fully replace them (no merge for collections).
    """

    model_config = ConfigDict(extra="forbid")

    tenant_id: Optional[str] = None
    tenant_domain: Optional[str] = None
    on_prem_ad_domain: Optional[str] = None
    on_prem_netbios_domain: Optional[str] = None
    on_prem_sid_prefix: Optional[str] = None

    domain_controllers: Optional[list[DomainController]] = None
    devices: Optional[list[Device]] = None
    processes: Optional[list[Process]] = None
    users: Optional[list[User]] = None
    ips: Optional[list[IPEntry]] = None
    user_agents: Optional[list[UserAgentEntry]] = None
    resources: Optional[list[Resource]] = None
    client_apps: Optional[list[ClientApp]] = None
    groups: Optional[list[Group]] = None
    conditional_access_policies: Optional[list[ConditionalAccessPolicy]] = None
    entra_sign_in_error_codes: Optional[list[WeightedErrorCode]] = None
    entra_spn_sign_in_error_codes: Optional[list[WeightedErrorCode]] = None


class Profile(BaseModel):
    """Top-level YAML profile: an optional list of tables to generate, plus an
    optional `overrides:` block that patches World defaults. When `tables` is
    omitted (or empty), the CLI falls back to every registered generator —
    handy for users who only want to ship overrides without restating the
    full table list."""

    model_config = ConfigDict(extra="forbid")

    tables: Optional[list[str]] = None
    overrides: Optional[Overrides] = None

    def build_world(self) -> World:
        if self.overrides is None:
            return World()
        return World(**self.overrides.model_dump(exclude_none=True))
