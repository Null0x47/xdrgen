# Production-like data

The generators are hand-curated per table to produce realistic, *correlated* values rather than random noise. A single immutable `World` object (defined in [`../world.py`](../world.py)) is built once per `xdrgen generate` run and threaded into every generator — that's how the world stays consistent across tables: a single tenant ID, the same user pool, the same IP-to-geo mapping, and user agents paired with their matching OS / browser. The same Avery Chen who downloads a file in `CloudAppEvents` is the same Avery Chen who interactively signs in via `EntraIdSignInEvents`, from the same set of source IPs.

Generators self-register via a `@register("TableName")` decorator on their `generate(world)` function; [`__init__.py`](./__init__.py) walks the package with `pkgutil.iter_modules` at import time, so adding a new generator is a one-file change — drop a module under `generators/`, decorate, done.

### Sampling: uniform by default, weighted on opt-in

Every pool field listed below as profile-overridable accepts two YAML shapes:

- A bare list of entries — sampled uniformly. Any `weight` value is ignored.
- `{random: false, entries: [...]}` — sampled weighted. Every entry must declare `weight`; the profile loader fails fast if any is missing. Scalar pools (plain string lists like `cloud_app_file_names`, `local_dns_servers`) switch their entries to `{value, weight}` objects in this mode.

The exception is the two pools sampled via `random.sample(k=2)` — `local_dns_servers` and the DNS-server slot of `DeviceNetworkInfo`. They still pick uniformly even when `random: false` (no stdlib weighted-sample-without-replacement); the validator still enforces weights are present.

## Per-table specifics

### `CloudAppEvents`

- A curated catalogue of cloud apps with their real Defender for Cloud Apps `ApplicationId` values (Microsoft 365, Exchange Online, Teams, Salesforce, Box, GitHub) and the actual `ActionType` vocabulary each connector emits.
- `ObjectId` / `ObjectName` / `ObjectType` and `ActivityObjects` are derived from the chosen `ActionType` (file actions get filenames, mail actions get message-IDs, account actions reference the acting user, etc.).
- `RawEventData` mirrors source-side audit fields (`Operation`, `OrganizationId`, `RecordType`, `UserKey`, …) so the row matches the shape of a real Office 365 / Cloud App audit record.
- `IsAdminOperation`, `IsExternalUser`, `IsAnonymousProxy` are derived from the picked entities, not random booleans.
- **Profile-overridable** via `cloud_apps:` (`{name, app_id, instance_id, audit_source, actions}` — replace the default DfCA catalogue with your own connectors), `cloud_app_file_names:`, `cloud_app_mail_subjects:`, and `cloud_app_group_names:` (string pools driving the `ObjectName` of File / Email / Group-shaped activities).

### `EntraIdSignInEvents`

- `Application` / `ApplicationId` are picked from a pool of well-known first-party Microsoft client apps (Microsoft Office, Teams, Outlook Mobile, Authenticator, Edge, Azure CLI, Azure PowerShell, Azure Portal) using their real app IDs.
- `ResourceDisplayName` / `ResourceId` are picked from a pool of resources users typically authenticate to (Microsoft Graph, Exchange Online, SharePoint, ARM, Teams Services, Office 365 Management APIs).
- `ErrorCode` is weighted: ~80% success (`0`) with a long-tail of real Entra error codes (`50126` invalid credentials, `50076` MFA required, `50074` strong-auth interrupt, `53003` blocked by CA, `53000` device not compliant, `50053` account locked, `50158` external security challenge, `50140` KMSI interrupt, `50057` disabled, `50055` expired, `50034` unknown user, `50173` fresh token needed, `50097` device auth required). `AuthenticationProcessingDetails` carries the actual processor message tied to the error code on failures (e.g. `"InvalidUserNameOrPassword: Error validating credentials due to invalid username or password."`). The whole catalogue — codes, weights, descriptions — is overridable via `entra_sign_in_error_codes:` in YAML, so you can shape the distribution to a scenario (password-spray spike, CA rollout, etc.) without code changes.
- `ConditionalAccessPolicies` is a JSON-encoded list of policy decisions; `ConditionalAccessStatus` is consistent with the policy results.
- `LogonType`, `ClientAppUsed`, and `Browser` are derived from the picked user / user-agent (e.g. `nonInteractiveUser` for service accounts, `Mobile Apps and Desktop clients` for the iOS UA).
- `DeviceName` / `EntraIdDeviceId` / `DeviceTrustType` / `IsManaged` / `IsCompliant` follow the user's primary registered device (with a probability of unmanaged sign-ins for users without a device).
- `RiskLevelAggregated` / `RiskState` / `RiskDetails` are mostly clean (`0`); risk fields elevate together when failures occur.
- `IsExternalUser` (`-1`/`0`/`1`), `IsGuestUser`, and `AlternateSignInName` follow Entra's actual semantics for cloud-only vs. hybrid vs. guest accounts.

### `EntraIdSpnSignInEvents`

- A pool of service principals modelling realistic shapes: production app SPNs, system-assigned managed identities (AKS), user-assigned managed identities (Functions), and CI/CD principals (GitHub Actions, Terraform Cloud).
- `IsManagedIdentity` matches the SPN type. Managed identities are biased toward Azure cloud-provider source IPs (because that's where they actually run); regular SPNs come from anywhere in the IP pool.
- `ResourceDisplayName` / `ResourceId` cover the resources SPNs typically hit (Microsoft Graph, ARM, Key Vault, Storage, SQL, Container Registry).
- `ErrorCode` is weighted toward success (~92%) with realistic SPN failure modes (`7000215` invalid client secret, `7000222` expired secret keys, `700016` app not found, `50105` user not assigned to app role, `90094` admin consent required, `65001` consent missing, `53003` blocked by CA on the workload identity, `9002313` invalid grant). The catalogue is overridable via `entra_spn_sign_in_error_codes:` in YAML.

### `GraphApiAuditEvents`

- A curated catalogue of real Microsoft Graph endpoints across `Microsoft.DirectoryServices`, `Microsoft.Exchange`, `Microsoft.SharePoint`, `Microsoft.Teams`, `Microsoft.Reports`, and `Microsoft.Security`. Each endpoint pairs the URI template with the actual HTTP method and an OAuth scope appropriate for that call (e.g. `User.Read.All`, `Mail.Send`, `Policy.Read.All`).
- `RequestUri` is rendered to a fully-formed `https://graph.microsoft.com/{v1.0|beta}/...` URL — `ApiVersion` matches the version embedded in the URI, and path placeholders are substituted from world fixtures (the calling user's `object_id` for `/users/{id}`, a directory group from `world.groups` for `/groups/{id}`) plus real-shaped GUIDs for SharePoint drives and Teams identifiers.
- `EntityType` flips between `User` (delegated, user-context call — both `AccountObjectId` and `ServicePrincipalId` populated) and `ServicePrincipal` (app-only / `client_credentials` call — `AccountObjectId` empty, `ServicePrincipalId` and `ApplicationId` both equal to the calling app). Service-account users always go through the app-only path.
- `IdentityProvider` resolves to `https://sts.windows.net/{tenantId}/`, picking up the tenant override from the YAML config. `IPAddress` and `Location` come from the world's IP / Azure-region pools.
- `ResponseStatusCode` is weighted toward `200` (~80%) with the failure tail covering the codes a SOC analyst actually filters for: `401` invalid token, `403` insufficient scope, `404` target not found, `429` throttled, plus a small slice of `400` and `500`. `ResponseSize` tracks the outcome — large for `GET` reads, small for writes, exactly `0` for `204 No Content`, short for failures. The status-code distribution is profile-overridable via `graph_api_status_codes:` (`{code, weight}`) so you can model a throttling spike, a 5xx outage, or any other failure-heavy scenario.

### `IdentityLogonEvents` (Defender for Identity, on-prem AD)

- `LogonType` is weighted toward `Network` (SMB share access) and `Interactive`, with realistic representation of `RemoteInteractive` (RDP), `Service`, `Batch`, `Unlock`, `NetworkCleartext`, and `CachedInteractive`.
- `Protocol` and `DestinationPort` stay consistent — Kerberos → 88, NTLM → 445, LDAP → 389, LDAPS → 636. Service / batch logons skew toward Kerberos.
- `DestinationDeviceName` / `DestinationIPAddress` always terminate at one of the configured domain controllers (`DC01.contoso.local`, `DC02.contoso.local`).
- `AccountSid` uses a single shared SID prefix per tenant; per-user RIDs (`500` for the admin, regular RIDs for users, none for the federated guest) keep accounts identifiable across rows.
- `FailureReason` is populated only when `ActionType == "LogonFailed"` (~8% of events) and uses MDI's actual vocabulary (`WrongPassword`, `AccountLockedOut`, `SmartcardRequired`, …).
- **Profile-overridable** via `identity_logon_types:` (weighted LogonType pool), `identity_logon_protocols:` (weighted `{protocol, port}` pool; Service/Batch still routes through Kerberos), and `identity_logon_failure_reasons:` (string pool).

### `IdentityQueryEvents` (LDAP / SAMR / DNS recon against AD)

- `QueryType` covers the BloodHound-style enumeration patterns SOC analysts actually look for: `QueryUser`, `QueryGroup`, `EnumerateUsers`, `EnumerateGroups`, `QueryComputer`, `QueryDomain`, `Resolve`.
- `Query` is a real LDAP filter for LDAP queries (`(&(objectClass=user)(sAMAccountName=jordan.patel))`), an A-record lookup for DNS, etc.
- `QueryTarget` is drawn from a real-world target pool (`Domain Admins`, `Enterprise Admins`, `Schema Admins`, tier-0 OU names, DC names) so the row exercises the same patterns detection rules trigger on.
- `Protocol` ↔ `DestinationPort` are paired (`Ldap` → 389, `Samr` → 445, `Dns` → 53). User-scoped queries fill `TargetAccountDisplayName` / `TargetAccountUpn` from the same shared user pool.
- **Profile-overridable** via `identity_query_kinds:` (`{query_type, protocol, port, weight}` — keeps the protocol↔port pairing consistent), `identity_query_group_targets:` (string pool for group queries), and `identity_query_computer_targets:` (string pool for computer / DNS Resolve queries).

### `IdentityDirectoryEvents` (AD directory changes)

- `ActionType` uses MDI's readable strings — group-membership churn and password resets dominate; rarer admin operations like `Account Constrained Delegation state changed`, `Service Principal Name added to account`, and `Account Sensitive flag changed` are present but thin.
- Actor (`Account*`) and target (`TargetAccount*`) are independently sampled from the user pool, so admin-on-user, user-on-user, and self-modifications all appear.
- All events terminate at a domain controller and use LDAP / port 389, matching the wire format MDI captures.
- **Profile-overridable** via `identity_directory_action_types:` (`{action, weight}` — replace or reshape the MDI vocabulary distribution).

### `IdentityEvents` (Sentinel unified identity table)

- A different shape from the Defender-for-Identity tables: `ActionType` is the *raw* action string from the source application, not a normalised enum (`UserLoggedIn`, `Add member to group.`, `group.user_membership.add`, …).
- `Application` covers both `AzureActiveDirectory` and federated sources (`Okta`); `ApplicationInstanceId` matches the source (`contoso.onmicrosoft.com` vs. `contoso.okta.com`).
- `ActionResult` (`Success` / `Failure`) and `ActionFailureReason` are derived from the action type — anything containing `Failed` flips both consistently.
- `TargetObjects` is a typed list (`user`, `group`, `application`, …) chosen to match the action.
- `RawEventData` mirrors the activity-log shape Microsoft Graph / Okta would have produced for that operation.
- **Profile-overridable** via `identity_raw_actions:` (`{action, application, target_kind, weight}` with `target_kind ∈ {user, group, app, policy}`), `identity_event_group_names:` (string pool surfaced as `TargetObjects.Name` for group actions), and `identity_event_app_names:` (string pool for app actions).

### `IdentityAccountInfo` (account / identity profile snapshot)

- One row per account, sampled from the same shared user pool — display name, given/surname, department, job title, employee ID, city, country all stay consistent with that user across runs.
- `Type` flips to `ServiceAccount` for the application user (no MFA enrolled, no manager); `Tags` carry `Sensitive` for admins, `Service Account` for SPNs, `Guest` for federated guests.
- `CriticalityLevel` is `4` for admins and `2` otherwise. `DefenderRiskLevel` is weighted (`80%` clean, with a long tail).
- `Sid` uses the same on-prem SID prefix as `IdentityLogonEvents` / `IdentityDirectoryEvents`, so the same account pivots cleanly between cloud-provider and on-prem rows.
- `IdentityLinkType` / `IdentityLinkBy` model both the common `Strong identifiers` / `System` path and the rarer manual SOC-merge case.
- **Profile-overridable** via `identity_auth_methods:` (string pool for `AuthenticationMethod`) and `identity_risk_levels:` (`{level, weight}` — Defender risk-level distribution, `0` = None .. `3` = High).

### `Device*` tables (Defender for Endpoint / MDE)

The nine Device* generators (`DeviceEvents`, `DeviceProcessEvents`, `DeviceLogonEvents`, `DeviceNetworkEvents`, `DeviceImageLoadEvents`, `DeviceRegistryEvents`, `DeviceFileEvents`, `DeviceFileCertificateInfo`, `DeviceNetworkInfo`) all draw from a shared device fixture pool ([`world.Device`](../world.py)) and a shared initiating-process catalogue in [`device_common.py`](./device_common.py). Devices are profile-overridable via the `devices:` key in the YAML — supply your own pool to make the generated rows look like *your* fleet.

- **Device pool**: each entry carries `device_id`, `device_name` (FQDN), `os_platform`, `os_version`, `public_ip`, `local_ip`, `mac_address`, `machine_group`, and an optional `primary_user_upn` linking the endpoint back to its primary user. The default pool covers two Windows workstations, a macOS workstation, a Linux build server, and a Windows file server so the generated rows span the OS / role mix of a realistic tenant.
- **Initiating-process pool**: a curated catalogue of processes Defender actually surfaces as initiators (`explorer.exe`, `cmd.exe`, `powershell.exe`, `svchost.exe`, `chrome.exe`, `msedge.exe`, `outlook.exe`, `winword.exe`, `MsMpEng.exe`, `rundll32.exe`). Each entry carries the right folder path, signed-binary version-info (CompanyName / FileDescription / OriginalFileName / ProductName / ProductVersion), integrity-level / token-elevation defaults, and a typical parent process. Hashes (MD5 / SHA-1 / SHA-256) are derived deterministically from the file name, so the same `cmd.exe` always reports the same SHA-1 across a run — analysts pivoting on hashes see consistent values regardless of which Device* table the row came from. **Like devices, the catalogue is profile-overridable** via the `processes:` key in the YAML: replace the default pool with the binaries that actually run in your tenant (Office vs. LibreOffice, your in-house deployment scripts, etc.) and every Device* row's `InitiatingProcess*` columns redraws from your supplied list.
- **User binding**: when the picked device declares a `primary_user_upn`, the generator biases the `InitiatingProcessAccount*` columns toward that user (~75% of events). The remaining 25% pick a random world user, modelling shared / secondary logins. Devices with no `primary_user_upn` (file servers, build boxes) always pick a random user.
- **Per-table specifics**:
  - `DeviceProcessEvents` — `ActionType` is `ProcessCreated`. Both the initiating process and the created process come from the catalogue (with their own `Process*` columns: integrity level, token elevation, version info, hashes).
  - `DeviceLogonEvents` — `LogonType` is weighted toward `Network` (SMB share access) and `Interactive`, mirroring `IdentityLogonEvents` but with a slightly different vocabulary (e.g. `CachedInteractive` is more common on managed endpoints). `RemoteIP` / `RemotePort` / `RemoteDeviceName` are populated only for network-style logons; local interactive logons leave them null. `FailureReason` is populated only when `ActionType == "LogonFailed"` (~8% of events). The `LogonType` distribution, the authentication `Protocol` pool (`Kerberos`, `Ntlm`, `NetLogon`), and the `FailureReason` vocabulary are all profile-overridable via `device_logon_types:` (`{logon_type, weight}`), `device_logon_protocols:` (plain string list), and `device_logon_failure_reasons:` (plain string list).
  - `DeviceNetworkEvents` — `Protocol` agrees with the destination port (UDP for DNS on `53`, TCP otherwise). `RemoteUrl` is paired with the port (HTTPS endpoints get `graph.microsoft.com` / `outlook.office365.com`-style URLs; LDAP / SMB / Kerberos / RDP destinations leave it null). `LocalIPType` is `Private` (the local adapter is on RFC1918 space); `RemoteIPType` flips between `Private` / `Public` based on the world IP that was picked. The `ActionType` distribution is profile-overridable via `device_network_action_types:` (`{action, weight}`).
  - `DeviceImageLoadEvents` — DLLs come from a curated pool (`kernel32.dll`, `ntdll.dll`, `amsi.dll`, `System.Management.Automation.dll`, …) paired with the folder they actually live in, so `FolderPath` always matches `FileName`. Hashes are stable per DLL. The pool is profile-overridable via `loaded_libraries:` (`{file_name, folder_path}`), so you can mix in custom in-house DLLs or replace the default Windows set entirely.
  - `DeviceRegistryEvents` — registry targets are real keys hunters look at (Run keys, IFEO debugger, Windows Defender service start, `RunAsPPL`, Office macro security). `PreviousRegistry*` columns are populated only for `*Renamed` and `*Set` action types, matching MDE's actual emission. The `ActionType` distribution is profile-overridable via `device_registry_action_types:` (`{action, weight}`).
  - `DeviceFileEvents` — `ActionType` is weighted (`FileCreated` dominates, then `FileModified`, `FileDeleted`, `FileRenamed`, `FileShredded`, and a thin slice of `NetworkShareFileSynchronized`). Files are drawn from a curated mix of browser downloads, locally produced documents, temp/cache paths, and SMB share locations — `FolderPath` always matches the `FileName` and the user's `sam_account_name`. Hashes are stable per filename so the same `setup.exe` pivots cleanly across runs. `FileOriginIP` / `FileOriginUrl` / `FileOriginReferrerUrl` are only populated for browser-downloaded files freshly written to `\Users\<u>\Downloads`. `PreviousFileName` / `PreviousFolderPath` are populated only for `FileRenamed`. UNC paths fill `ShareName`; `NetworkShare*` actions additionally populate `RequestAccountDomain` / `RequestAccountName` / `RequestAccountSid` / `RequestProtocol=SMB` / `RequestSourceIP` / `RequestSourcePort` so the row reflects the SMB client that touched the share. `SensitivityLabel` / `SensitivitySubLabel` track HR / Finance share paths and a thin tail of locally classified Office documents; `IsAzureInfoProtectionApplied` flips true whenever a Confidential label is set. **Profile-overridable** via `file_templates:` (folder + filename + kind ∈ `download` / `doc` / `temp` / `share`), `file_action_types:` (weighted ActionType pool), `file_sensitivity_labels:` (label/sublabel pool for the random local-doc fallback), and `file_download_hosts:` (host pool used to render `FileOriginUrl` / `FileOriginReferrerUrl`).
  - `DeviceEvents` — the catch-all table. `ActionType` covers Antivirus detections, ASR rules, Network Protection, Tamper Protection, AMSI, App Control, USB events, and others. Each action type declares which auxiliary block it populates (file fields for AV detections, network fields for Network Protection, registry fields for tampering attempts) so the row is internally consistent — an AV detection won't carry a `RemoteIP`, a Network Protection block won't carry `RegistryKey`. The action pool is profile-overridable via `device_event_actions:` — each entry is `{action, shape, weight}` with `shape ∈ {file, network, registry, none}`, letting you bias toward a specific behaviour (ASR-heavy, AV-heavy, USB-only) or inject custom action names while keeping the per-shape column-block consistency.
  - `DeviceFileCertificateInfo` — code-signing certs from a real catalogue (Microsoft Windows / Microsoft Corporation / Google / Adobe / Mozilla / GitHub / Slack). `IsRootSignerMicrosoft` is true only for the Microsoft chains; `IsTrusted` follows `IsSigned` (a thin tail of unsigned binaries leaves all certificate-specific fields null, so a row that says "unsigned" cannot have an Issuer). The cert catalogue, the filename pool that drives `SHA1`, and the CRL distribution points are all profile-overridable via `code_signing_certificates:` (`{subject, issuer, serial, is_root_microsoft, signature_type}`), `signed_files:` (plain string list), and `crl_urls:` (plain string list).
  - `DeviceNetworkInfo` — one row per network adapter (Wi-Fi, Ethernet, vEthernet (WSL), Cisco AnyConnect VPN). `IPAddresses` / `DnsAddresses` / `DefaultGateways` / `ConnectedNetworks` are JSON-encoded arrays as Defender emits them. The adapter catalogue, DNS resolver pool, and default gateway pool are profile-overridable via `network_adapters:` (`{name, type, vendor, tunnel, network_category, network_name}`), `local_dns_servers:`, and `local_default_gateways:`.

### `EmailEvents` / `EmailAttachmentInfo` / `EmailPostDeliveryEvents` / `EmailUrlInfo` / `UrlClickEvents` (correlated by `NetworkMessageId`)

These five tables are the email side of Defender XDR and are designed to be **pivotable on `NetworkMessageId`** — given any one row, an analyst can join to every related row in the other four tables. To make that work, the generators all draw from a shared pool ([`email_pool.py`](./email_pool.py)) of pre-built emails. Each pool entry carries everything any of the five tables needs: sender / recipient identities, attachments (with stable per-filename SHA-256s), embedded URLs, threat verdict, delivery action, and `NetworkMessageId` itself.

The pool covers a realistic mix:

- routine vendor mail (Acme Billing, DocuSign) — clean, delivered to Inbox
- platform notifications (GitHub PR, Microsoft Teams mention) — clean, no attachments
- a phishing attempt from `securemail-update.io` — `Phish` threat type, blocked / quarantined, `SPF=fail; DKIM=none; DMARC=fail; CompAuth=fail`
- a high-bulk newsletter — `BulkComplaintLevel=7`, `Junked`
- an intra-org reply (Avery → Jordan) — `EmailDirection=Intra-org`, SharePoint URL
- an outbound message from an admin to an external partner — `EmailDirection=Outbound`

Per table:

- **`EmailEvents`** — full email metadata including `AuthenticationDetails` (SPF / DKIM / DMARC / CompAuth pass-fail breakdown), `BulkComplaintLevel`, `ConfidenceLevel`, `DeliveryAction` / `DeliveryLocation`, `EmailAction` / `EmailActionPolicy`, `IsFirstContact`, `AttachmentCount` / `UrlCount` derived from the pool.
- **`EmailAttachmentInfo`** — one row per pulled attachment, with file name, extension, type, size, and a stable SHA-256 (so the same attachment hashes the same across runs).
- **`EmailPostDeliveryEvents`** — ZAP / manual-remediation / user-reported-not-junk paths. When the underlying email already carries a phishing verdict, the action is forced to a ZAP or admin-triggered path (a user can't "Move to inbox" an email that was quarantined as phish). The path catalogue is profile-overridable via `email_post_delivery_paths:` (`{action, action_type, trigger, result, delivery_location}`).
- **`EmailUrlInfo`** — one row per embedded URL, with `Url`, `UrlDomain`, and `UrlLocation` (Body / Subject / Attachment).
- **`UrlClickEvents`** — Safe Links click telemetry. The clicker is always the email's recipient (joins on `(NetworkMessageId, AccountUpn)`); a click into a known-phish email is collapsed to a blocking outcome regardless of the random outcome roll. `UrlChain` shows the realistic `safelinks.protection.outlook.com → tracker → final URL` shape. The outcome and workload pools are profile-overridable via `url_click_outcomes:` (`{action_type, is_clicked_through, threat_types, weight}`) and `url_click_workloads:` (`{workload, weight}`).

The full pool is small (8 emails) on purpose: with 5 generators sampling from it, mixed streams produce many rows-per-email so an analyst exploring the JSON output can practice pivoting on `NetworkMessageId` without first having to dig for matches.
