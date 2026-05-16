# AzureHound threat profile

Generates a `GraphApiAuditEvents` stream shaped like an AzureHound
collection run so the
[CloudBrothers detection](https://cloudbrothers.info/detect-threats-graphapiauditevents-part-3/)
fires end-to-end against a local Kustainer / Sentinel.

## What it does

`profile.yaml` constrains the world to a single compromised operator
(`morgan.hale@northwind.com`) calling the 14 Microsoft Graph endpoints
AzureHound walks during a full directory collection:

| API version | Endpoint                                                      |
|-------------|---------------------------------------------------------------|
| `beta`      | `servicePrincipals/{id}/owners`                               |
| `beta`      | `groups/{id}/owners`                                          |
| `beta`      | `groups/{id}/members`                                         |
| `beta`      | `applications/{id}/owners`                                    |
| `beta`      | `devices/{id}/registeredOwners`                               |
| `v1.0`      | `servicePrincipals/{id}/appRoleAssignedTo`                    |
| `v1.0`      | `users`                                                       |
| `v1.0`      | `applications`                                                |
| `v1.0`      | `groups`                                                      |
| `v1.0`      | `roleManagement/directory/roleAssignments`                    |
| `v1.0`      | `roleManagement/directory/roleDefinitions`                    |
| `v1.0`      | `devices`                                                     |
| `v1.0`      | `organization`                                                |
| `v1.0`      | `servicePrincipals`                                           |

URIs are pinned to `/v1.0/` or `/beta/`, so after the detection's UUID
normalisation every generated `RequestUri` collapses to one of the strings
in the detection's `AzureHoundGraphQueries` set — `set_intersect` returns
all 14 entries, giving a `ConfidenceScore` of `1.0`.

## Run it

Send straight to the Kustainer emulator:

```bash
docker compose -f docker/docker-compose-kustainer.yml up -d
uv run xdrgen generate examples/threat-profiles/azure-hound/profile.yaml \
    -n 3000 -i 0 --sink kustainer
```

Or write to a JSON file and ingest it however you prefer:

```bash
uv run xdrgen generate examples/threat-profiles/azure-hound/profile.yaml \
    -n 3000 -i 0 -o ./out/azurehound.json
```

`-n 3000` is the recommended minimum: the generator splits ~60/40 between
delegated (User) and app-only (ServicePrincipal) calls, so the
per-`ObjectId` bucket needs ~2000 events to clear `TotalCount > 1000`. Crank
`-n` higher if you want longer-running runs or to test summarisation over
multiple ingestion windows.

## Detection query

Run this in Kustainer (or against the live Defender Advanced Hunting
schema). Source: cloudbrothers.info, part 3.

```kql
let AzureHoundGraphQueries = dynamic([
    "https://graph.microsoft.com/beta/servicePrincipals/<UUID>/owners",
    "https://graph.microsoft.com/beta/groups/<UUID>/owners",
    "https://graph.microsoft.com/beta/groups/<UUID>/members",
    "https://graph.microsoft.com/v1.0/servicePrincipals/<UUID>/appRoleAssignedTo",
    "https://graph.microsoft.com/beta/applications/<UUID>/owners",
    "https://graph.microsoft.com/beta/devices/<UUID>/registeredOwners",
    "https://graph.microsoft.com/v1.0/users",
    "https://graph.microsoft.com/v1.0/applications",
    "https://graph.microsoft.com/v1.0/groups",
    "https://graph.microsoft.com/v1.0/roleManagement/directory/roleAssignments",
    "https://graph.microsoft.com/v1.0/roleManagement/directory/roleDefinitions",
    "https://graph.microsoft.com/v1.0/devices",
    "https://graph.microsoft.com/v1.0/organization",
    "https://graph.microsoft.com/v1.0/servicePrincipals"
]);
GraphApiAuditEvents
| extend ObjectId = coalesce(AccountObjectId, ApplicationId)
| where RequestUri !has "microsoft.graph.delta"
| extend NormalizedRequestUri = replace_regex(RequestUri, @'[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}', @'<UUID>')
| extend NormalizedRequestUri = replace_regex(NormalizedRequestUri, @'\?.*$', @'')
| summarize
    TotalCount = count(),
    GraphEndpointsCalled = make_set(NormalizedRequestUri, 1000),
    arg_min(Timestamp, *)
    by ObjectId, EntityType
| extend MatchingQueries = set_intersect(AzureHoundGraphQueries, GraphEndpointsCalled)
| extend ConfidenceScore = round(todouble(array_length(MatchingQueries)) / todouble(array_length(AzureHoundGraphQueries)), 1)
| where ConfidenceScore > 0.7
| where TotalCount > 1000
```

The Defender Advanced Hunting table is `GraphAPIAuditEvents` (uppercase
`API`); `xdrgen`'s Pydantic model and Kustainer schema use
`GraphApiAuditEvents` to match the column naming convention used elsewhere
in this repo. Adjust the table name if you copy this query into a real
Sentinel / Defender XDR workspace.

The original `ingestion_time() > ago(1h)` filter is dropped here because
`xdrgen` writes events whose `Timestamp` is "now" but Kustainer's
`ingestion_time()` reflects when the row landed. Re-add the filter when
running against a real tenant.
