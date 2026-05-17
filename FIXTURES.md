# Profile fixtures

This document is the canonical reference for every override key accepted under `overrides:` in a profile YAML. The matching Pydantic schemas live in [`world.py`](./world.py) — unknown keys, wrong shapes, and missing required sub-fields fail fast at load time.

For the high-level usage flow (where the profile fits, how to run it) see the [Profile section in `README.md`](./README.md#profile). Per-table notes on *how* each fixture is consumed live in [`generators/PRODUCTION_LIKE_DATA.md`](./generators/PRODUCTION_LIKE_DATA.md).

## Two shapes per pool

Every pool override accepts two YAML shapes:

1. **Bare list** — sampled uniformly. Any per-entry `weight` is ignored.

   ```yaml
   devices:
     - device_id: ws01
       device_name: WS-01
     - device_id: ws02
       device_name: WS-02
   ```

2. **`{random: false, entries: [...]}`** — sampled weighted. Every entry must declare `weight`; the profile loader fails fast otherwise. Scalar pools (plain string lists) switch their entries to `{value, weight}` objects in this mode.

   ```yaml
   devices:
     random: false
     entries:
       - device_id: ws01
         device_name: WS-01
         weight: 10
       - device_id: ws02
         device_name: WS-02
         weight: 1
   ```

Every item model carries an optional `weight: int` field. Setting it under `random: true` (the default) is a no-op; under `random: false` it is required.

Caveat: pools sampled with `random.sample` (k>1) — currently `local_dns_servers` and the DNS slot of `DeviceNetworkInfo` — still pick uniformly even when `random: false`. The validator still enforces weights are present.

---

## Tenant identity (scalars)

Top-level scalar overrides that stamp every row.

- `tenant_id` — Entra tenant GUID. Surfaces on every row's `TenantId` column and is interpolated into `IdentityProvider` (`https://sts.windows.net/{tenant_id}/`).
- `tenant_domain` — primary verified domain (e.g. `contoso.com`). Used as the `@domain` for internet message IDs and intra-org email semantics.
- `on_prem_ad_domain` — on-prem AD FQDN (e.g. `contoso.local`). Drives `AccountDomain` on Identity* and Device* logon rows.
- `on_prem_netbios_domain` — pre-Windows-2000 short domain name (e.g. `CONTOSO`).
- `on_prem_sid_prefix` — shared SID prefix (`S-1-5-21-…`). Combined with each user's `sid_rid` to form `AccountSid` across Identity* / Device* tables.

---

## Shared identity pools

These pools are drawn from by *most* generators — change them and the whole stream looks like a different tenant.

### `users`

User / service-account / guest catalogue. Drives every account-bearing column on Identity*, Device*, EntraId*, CloudApp*, Email*, GraphApi* rows.

- **Shape:** `User(display_name, upn, object_id, type, device_name, device_id, last_password_change_days_ago, sam_account_name, sid_rid, given_name, surname, department, job_title, employee_id, city, country, weight)`.
- `type ∈ {Regular, Admin, Application}` — `Application` biases sign-ins to non-interactive and disables MFA enrollment in `IdentityAccountInfo`.
- `device_name` / `device_id` model the user's primary registered endpoint and are quoted on `EntraIdSignInEvents`.
- `sid_rid` participates in `{on_prem_sid_prefix}-{sid_rid}` to form on-prem SIDs; leave `None` for cloud-only / guest accounts.
- `sam_account_name` is the match key used by `email_templates[].recipient_persona` (hash-index fallback when not found).

### `devices`

MDE-managed endpoints. Drives every Device* table; also surfaces in `GraphApiAuditEvents` device URI paths.

- **Shape:** `Device(device_id, device_name, os_platform, os_version, public_ip, local_ip, mac_address, machine_group, primary_user_upn, weight)`.
- `device_name` is the FQDN MDE reports; `device_id` is the GUID.
- `primary_user_upn` should match a `users[].upn`. When set, the generator biases the row's `InitiatingProcessAccount*` toward that user ~75% of the time; the remaining 25% picks a random world user. Omit for shared boxes (file servers, build runners).

### `ips`

Source IPs with paired geo / ISP / category metadata. Used as `IPAddress` / `RemoteIP` and as the source of `City` / `Country` / `Latitude` / `Longitude` / `ISP` columns.

- **Shape:** `IPEntry(ip, city, state, country, isp, category, latitude, longitude, weight)`.
- `category ∈ {Cloud provider, Corporate, ISP}` — `Cloud provider` IPs are biased toward managed-identity sign-ins in `EntraIdSpnSignInEvents`; `Corporate` IPs become `trustedNamedLocation` on Entra sign-ins; `ISP` IPs become eligible for `IsAnonymousProxy` flags in `CloudAppEvents`.

### `user_agents`

UA / platform / device-type / browser tuples. Drives `UserAgent`, `OSPlatform`, `DeviceType`, `Browser`, and the `ClientAppUsed` heuristic on `EntraIdSignInEvents`.

- **Shape:** `UserAgentEntry(ua, platform, device_type, browser, weight)`.
- `device_type ∈ {Workstation, Mobile}` — `Mobile` flips `ClientAppUsed` to `Mobile Apps and Desktop clients`; an Outlook-string `browser` flips it to `Modern Authentication Clients`.

### `processes`

InitiatingProcess catalogue. Used by every Device* table's `InitiatingProcess*` columns and again for the created-process columns on `DeviceProcessEvents`.

- **Shape:** `Process(file_name, folder_path, company, description, internal_file_name, original_file_name, product_name, product_version, command_lines, integrity_level, elevation, signature_status, signer_type, parent, md5, sha1, sha256, weight)`.
- Hashes (`md5`, `sha1`, `sha256`) are *optional* — when set, they pin published IOC hashes into the telemetry. When omitted, hashes are derived deterministically from `file_name` so cross-table pivots stay consistent.
- `command_lines` is a tuple of plausible argv strings; the generator picks one per row.

### `domain_controllers`

DCs that terminate Identity* logon / query / directory rows.

- **Shape:** `DomainController(name, ip, device_id, weight)`.
- Surfaces on `DestinationDeviceName` / `DestinationIPAddress` / `TargetDeviceName` in `IdentityLogonEvents`, `IdentityQueryEvents`, `IdentityDirectoryEvents`.

### `groups`

Entra ID directory groups surfaced in `GraphApiAuditEvents` request URIs.

- **Shape:** `Group(name, id, weight)`.

---

## Entra ID (`EntraIdSignInEvents`, `EntraIdSpnSignInEvents`)

### `client_apps`

First-party / line-of-business client apps that initiate Entra sign-ins and Graph API calls.

- **Shape:** `ClientApp(name, app_id, weight)`.
- Drives `Application` / `ApplicationId` on `EntraIdSignInEvents`, and `ApplicationId` / `ServicePrincipalId` on `GraphApiAuditEvents`.

### `service_principals`

Workload identities (app SPNs, system-assigned and user-assigned managed identities, CI/CD principals).

- **Shape:** `ServicePrincipal(name, id, app_id, is_managed_identity, weight)`.
- `is_managed_identity=True` biases the row's source IP to `category="Cloud provider"` entries from `ips`.

### `resources`

Resources users / SPNs authenticate to.

- **Shape:** `Resource(name, id, weight)`.
- Drives `ResourceDisplayName` / `ResourceId` on both Entra sign-in tables.

### `conditional_access_policies`

CA policies serialized into the `ConditionalAccessPolicies` JSON column on `EntraIdSignInEvents`.

- **Shape:** `ConditionalAccessPolicy(id, displayName, enforcedGrantControls, enforcedSessionControls, weight)`.
- Field names use Graph's camelCase; the column is rendered as a JSON array with a per-row `result` (`success` / `failure` / `notApplied`) attached.

### `entra_sign_in_error_codes`

Weighted `ErrorCode` distribution for `EntraIdSignInEvents`. Default leans ~80% success (`code=0`); failure tail covers real-world Entra codes (`50126`, `50076`, `53003`, …).

- **Shape:** `ErrorCode(code, weight, description)`.
- `description` populates `AuthenticationProcessingDetails` on failures.

### `entra_spn_sign_in_error_codes`

Weighted `ErrorCode` distribution for `EntraIdSpnSignInEvents`. Default leans ~92% success; failure tail covers SPN-specific codes (`7000215` invalid secret, `7000222` expired keys, `700016` app not found, …).

- **Shape:** `ErrorCode(code, weight, description)`.

---

## Graph API (`GraphApiAuditEvents`)

### `graph_api_endpoints`

Catalogue of real Graph endpoints across `Microsoft.DirectoryServices`, `Microsoft.Exchange`, `Microsoft.SharePoint`, `Microsoft.Teams`, `Microsoft.Reports`, and `Microsoft.Security`.

- **Shape:** `GraphApiEndpoint(method, uri, workload, scope, weight)`.
- `uri` may hard-code `/v1.0/` or `/beta/`, or use `{ver}` for random selection. Path placeholders `{user_id}`, `{group_id}`, `{sp_id}`, `{app_id}`, `{device_id}`, `{role_id}`, `{drive_id}`, `{team_id}`, `{chat_id}` are substituted from world fixtures at emit time.
- `scope` is the OAuth scope appropriate for the call (e.g. `User.Read.All`, `Mail.Send`).

### `graph_api_locations`

Azure regions stamped on `Location`.

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `graph_api_status_codes`

Weighted HTTP response-code distribution. Default leans ~80% `200`; failure tail covers `400`, `401`, `403`, `404`, `429`, `500`.

- **Shape:** `GraphApiStatusCode(code, weight)`.
- `ResponseSize` is derived from the status (`204` → `0`; failure → short; `GET` success → large; write success → small).

---

## Defender for Endpoint (Device* tables)

ActionType pools and Device* auxiliary catalogues.

### `device_event_actions`

ActionType pool for the catch-all `DeviceEvents` table. Each entry declares which auxiliary column block the row populates.

- **Shape:** `DeviceEventAction(action, shape, weight)`.
- `shape ∈ {file, network, registry, none}` — drives whether the row carries `File*` (AV detections), `Remote*` / `Local*` (Network Protection), `Registry*` (tampering), or nothing.

### `device_network_action_types`

ActionType pool for `DeviceNetworkEvents`. Default-weighted toward `ConnectionSuccess`.

- **Shape:** `DeviceNetworkActionType(action, weight)`.

### `device_registry_action_types`

ActionType pool for `DeviceRegistryEvents`. `*Renamed` and `*Set` actions automatically populate the `PreviousRegistry*` columns.

- **Shape:** `DeviceRegistryActionType(action, weight)`.

### `file_action_types`

ActionType pool for `DeviceFileEvents`. `NetworkShare*` actions are routed to UNC `share` templates regardless of weighting.

- **Shape:** `FileActionType(action, weight)`.

### `device_logon_types`

`LogonType` pool for `DeviceLogonEvents`. Default emphasises `Network` and `Interactive`; thin tail of `RemoteInteractive`, `Service`, `Batch`, `Unlock`, `NetworkCleartext`, `CachedInteractive`.

- **Shape:** `DeviceLogonType(logon_type, weight)`.

### `device_logon_protocols`

Auth protocol pool. Default: `Kerberos`, `Ntlm`, `NetLogon`.

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `device_logon_failure_reasons`

Failure-reason strings populated only on `LogonFailed` (~8% of events).

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `network_destinations`

`{port, url}` outbound destination pool for `DeviceNetworkEvents`.

- **Shape:** `NetworkDestination(port, url, weight)`.
- `url=None` for ports unrelated to a hostname (DNS, SMB, Kerberos, …) so the field stays null in the emitted row.
- `Protocol` is derived: `Udp` for port `53`, `Tcp` otherwise.

### `network_adapters`

Wi-Fi / Ethernet / VPN adapters for `DeviceNetworkInfo`.

- **Shape:** `NetworkAdapter(name, type, vendor, tunnel, network_category, network_name, weight)`.
- `type ∈ {Wireless, Ethernet, Tunnel}`; `tunnel` is `Ssh`, `Ipsec`, or `None`; `network_category ∈ {Private, Public, Domain}`.

### `local_dns_servers`

Local DNS resolver pool. **Sampled `k=2` per row — weights are ignored in this mode** (the `random: false` validator still requires weights be present).

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `local_default_gateways`

Default-gateway pool. Surfaces on `DefaultGateways` and `IPv4Dhcp`.

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `file_templates`

Templates for `DeviceFileEvents` `FileName` / `FolderPath`.

- **Shape:** `FileTemplate(folder_template, file_name, kind, weight)`.
- `kind ∈ {download, doc, temp, share}` — drives row shape:
  - `download` + `ActionType=FileCreated` populates `FileOrigin*` (host from `file_download_hosts`, IP from `ips`).
  - `share` (UNC paths) populates `ShareName` and the `Request*` block; selected automatically for `NetworkShare*` actions.
  - `doc` / `temp` keep `FileOrigin*` null.
- `folder_template` may include `{user}` — rendered with the picked user's `sam_account_name` at emit time.

### `file_sensitivity_labels`

Fallback label / sublabel pair for randomly classified local Office documents (~15% of `doc`-kind rows). Generator-level heuristics (HR / Finance share paths) take precedence.

- **Shape:** `SensitivityLabel(label, sublabel, weight)`.

### `file_download_hosts`

Host pool rendered into `FileOriginUrl` / `FileOriginReferrerUrl` for `download`-kind file creations.

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `code_signing_certificates`

Code-signing cert catalogue for `DeviceFileCertificateInfo`.

- **Shape:** `CodeSigningCertificate(subject, issuer, serial, is_root_microsoft, signature_type, weight)`.
- `is_root_microsoft` drives `IsRootSignerMicrosoft`; `signature_type ∈ {Embedded, Catalog, None}`.

### `signed_files`

Filename pool driving the `SHA1` column on `DeviceFileCertificateInfo`. Filename → stable hash mapping survives across runs.

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `crl_urls`

CRL distribution-point URLs. Populated only on signed rows.

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `loaded_libraries`

DLL / managed-assembly pool for `DeviceImageLoadEvents`.

- **Shape:** `LoadedLibrary(file_name, folder_path, weight)`.
- Hashes are derived from `file_name` so the same DLL hashes the same across every Device* table.

### `registry_targets`

Registry key + value catalogue for `DeviceRegistryEvents`.

- **Shape:** `RegistryTarget(key, value_name, value_data, value_type, weight)`.
- `value_type ∈ {REG_SZ, REG_DWORD, REG_BINARY, …}`.

---

## Cloud Apps (`CloudAppEvents`)

### `cloud_apps`

DfCA connector catalogue with real Defender for Cloud Apps `ApplicationId` values.

- **Shape:** `CloudApp(name, app_id, instance_id, audit_source, actions, weight)`.
- `actions` is a tuple of the connector-specific ActionType vocabulary; the generator draws one per row.

### `cloud_app_file_names`

`ObjectName` pool for File-shaped activities (downloads, uploads, sharing).

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `cloud_app_mail_subjects`

`ObjectName` pool for Email-shaped activities (send, delete, inbox rules).

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `cloud_app_group_names`

`ObjectName` pool for Group-shaped activities (member add, Teams collaboration, channel events).

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

---

## Defender for Identity / unified IdentityEvents

### `identity_auth_methods`

`AuthenticationMethod` pool for `IdentityAccountInfo`. Default: `Credentials`, `Federated`, `Hybrid`.

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `identity_risk_levels`

`DefenderRiskLevel` distribution (0 = None .. 3 = High) for `IdentityAccountInfo`.

- **Shape:** `IdentityRiskLevel(level, weight)`.

### `identity_directory_action_types`

ActionType pool for `IdentityDirectoryEvents` — MDI's readable vocabulary (group-membership churn, password resets, `Account Constrained Delegation state changed`, …).

- **Shape:** `IdentityDirectoryActionType(action, weight)`.

### `identity_raw_actions`

Raw source-side action vocabulary for `IdentityEvents` (the Sentinel unified identity table). Actions are *not* normalised — they come from the source application's vocabulary (`UserLoggedIn`, `Add member to group.`, `group.user_membership.add`).

- **Shape:** `IdentityRawAction(action, application, target_kind, weight)`.
- `application` is the source system (`AzureActiveDirectory`, `Okta`); drives `ApplicationInstanceId` (`contoso.onmicrosoft.com` vs `contoso.okta.com`).
- `target_kind ∈ {user, group, app, policy}` — picks the matching `TargetObjects` shape.

### `identity_event_group_names`

Group-name pool used as `TargetObjects.Name` for `target_kind=group` actions.

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `identity_event_app_names`

App-name pool used as `TargetObjects.Name` for `target_kind=app` actions.

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `identity_logon_types`

`LogonType` pool for `IdentityLogonEvents`.

- **Shape:** `IdentityLogonType(logon_type, weight)`.

### `identity_logon_protocols`

`{protocol, port}` pool for `IdentityLogonEvents`. Service / Batch logons still route through Kerberos when present, regardless of weighting.

- **Shape:** `IdentityLogonProtocol(protocol, port, weight)`.
- Pairs to preserve: Kerberos → 88, NTLM → 445, LDAP → 389, LDAPS → 636.

### `identity_logon_failure_reasons`

Failure-reason strings populated only on `LogonFailed`.

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `identity_query_kinds`

`{query_type, protocol, port}` tuple for `IdentityQueryEvents` — the BloodHound-style enumeration patterns SOC analysts hunt for.

- **Shape:** `IdentityQueryKind(query_type, protocol, port, weight)`.
- Protocol↔port pairing: `Ldap` → 389, `Samr` → 445, `Dns` → 53.

### `identity_query_group_targets`

`QueryTarget` strings for `Query*Group*` / `Enumerate*Groups` queries (e.g. `Domain Admins`, `Enterprise Admins`).

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

### `identity_query_computer_targets`

`QueryTarget` strings for `QueryComputer` / `Resolve` queries (e.g. DC names, member-server short names).

- **Shape:** plain string list, or `ScalarEntry(value, weight)` in weighted mode.

---

## Email / URL clicks (Email* + `UrlClickEvents`)

### `email_templates`

Full pre-built email catalogue. Every Email* row plus `UrlClickEvents` draws from this single pool, joined by `NetworkMessageId` — that's how cross-table pivots work.

- **Shape:** `EmailTemplate(subject, sender_display_name, sender_from_address, sender_from_domain, sender_mail_from_address, sender_mail_from_domain, sender_object_id, sender_ipv4, sender_ipv6, recipient_persona, direction, delivery_action, delivery_location, email_action, email_action_policy, email_action_policy_guid, email_size, bulk_complaint_level, authentication_details, confidence_level, threat_types, threat_names, weight, threat_classification, detection_methods, is_first_contact, language, attachments, urls)`.
- `recipient_persona` matches `users[].sam_account_name` (hash-index fallback when not found).
- `direction ∈ {Inbound, Outbound, Intra-org}`.
- `threat_types` carrying `Phish` / `Malware` forces `EmailPostDeliveryEvents` to a ZAP / Admin trigger and forces `UrlClickEvents` to a blocking outcome.
- `NetworkMessageId`, `InternetMessageId`, and per-attachment SHA-256s are minted at runtime by `EmailPool`.

### `email_post_delivery_paths`

ZAP / manual-remediation / user-reported paths for `EmailPostDeliveryEvents`.

- **Shape:** `EmailPostDeliveryPath(action, action_type, trigger, result, delivery_location, weight)`.
- `trigger ∈ {ZAP, Admin, User}` — phish-verdict emails are constrained to `ZAP` / `Admin` triggers.

### `url_click_outcomes`

Safe Links click-outcome distribution for `UrlClickEvents`.

- **Shape:** `UrlClickOutcome(action_type, is_clicked_through, threat_types, weight)`.
- A phish-verdict email overrides the rolled outcome and forces a blocking entry (`is_clicked_through=False` or `action_type=BlockpageOverride`).

### `url_click_workloads`

Source workload distribution for `UrlClickEvents.Workload`.

- **Shape:** `Workload(workload, weight)`.
- Default values: `Email`, `Office`, `Teams`. `Email` workload renders `AppName=Outlook`; others use the workload as the app name.
