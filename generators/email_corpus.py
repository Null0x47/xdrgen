"""Shared email pool for Email* / UrlClickEvents generators.

Every email-side table joins on `NetworkMessageId`, so all generators draw
from one finite pool of pre-built emails. `corpus_for(world)` returns the
per-World singleton with personas resolved against `world.users`.
"""

from __future__ import annotations

import functools
import hashlib
import random
import uuid
from typing import Any

from world import User, World


def _sha256_hex(name: str) -> str:
    # Stable per-filename so the same attachment hashes the same across rows.
    return hashlib.sha256(f"contoso::{name}".encode()).hexdigest()


def _new_network_message_id() -> str:
    return str(uuid.uuid4())


def _new_internet_message_id(domain: str) -> str:
    # RFC 5322 message-id: <token@domain>.
    return f"<{uuid.uuid4().hex}@{domain}>"


# Templates — runtime fields (NetworkMessageId, InternetMessageId, SHA-256,
# recipient) are filled in by EmailCorpus.__init__.
_EMAIL_TEMPLATES: list[dict[str, Any]] = [
    {
        "subject": "Invoice 8421 - Q2 services",
        "sender_display_name": "Acme Billing",
        "sender_from_address": "billing@acme-corp.com",
        "sender_from_domain": "acme-corp.com",
        "sender_mail_from_address": "billing@bounces.acme-corp.com",
        "sender_mail_from_domain": "bounces.acme-corp.com",
        "sender_object_id": None,
        "sender_ipv4": "203.0.113.45",
        "sender_ipv6": None,
        "recipient_persona": "jordan.patel",
        "direction": "Inbound",
        "delivery_action": "Delivered",
        "delivery_location": "Inbox",
        "email_action": "No action taken",
        "email_action_policy": None,
        "email_action_policy_guid": None,
        "email_size": 28412,
        "bulk_complaint_level": 4,
        "authentication_details": "SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        "confidence_level": '{"Spam":"1"}',
        "threat_types": None,
        "threat_names": None,
        "threat_classification": None,
        "detection_methods": None,
        "is_first_contact": False,
        "language": "en",
        "attachments": [
            {
                "file_name": "invoice_8421.pdf",
                "extension": "pdf",
                "file_type": "PDF Document",
                "file_size": 24813,
            },
        ],
        "urls": [
            {
                "url": "https://billing.acme-corp.com/pay/8421",
                "domain": "billing.acme-corp.com",
                "location": "Body",
            },
            {
                "url": "https://acme-corp.com/policy",
                "domain": "acme-corp.com",
                "location": "Body",
            },
        ],
    },
    {
        "subject": "[contoso/main] Pull request #482 ready for review",
        "sender_display_name": "GitHub",
        "sender_from_address": "noreply@github.com",
        "sender_from_domain": "github.com",
        "sender_mail_from_address": "bounces+482@sgmail.github.com",
        "sender_mail_from_domain": "sgmail.github.com",
        "sender_object_id": None,
        "sender_ipv4": "140.82.114.10",
        "sender_ipv6": None,
        "recipient_persona": "avery.chen",
        "direction": "Inbound",
        "delivery_action": "Delivered",
        "delivery_location": "Inbox",
        "email_action": "No action taken",
        "email_action_policy": None,
        "email_action_policy_guid": None,
        "email_size": 14210,
        "bulk_complaint_level": 1,
        "authentication_details": "SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        "confidence_level": '{"Spam":"1"}',
        "threat_types": None,
        "threat_names": None,
        "threat_classification": None,
        "detection_methods": None,
        "is_first_contact": False,
        "language": "en",
        "attachments": [],
        "urls": [
            {
                "url": "https://github.com/contoso/main/pull/482",
                "domain": "github.com",
                "location": "Body",
            },
            {
                "url": "https://github.com/settings/notifications",
                "domain": "github.com",
                "location": "Body",
            },
        ],
    },
    {
        "subject": "Please sign: NDA - Contoso / Northwind",
        "sender_display_name": "DocuSign EU System",
        "sender_from_address": "dse@eumail.docusign.net",
        "sender_from_domain": "eumail.docusign.net",
        "sender_mail_from_address": "dse@eumail.docusign.net",
        "sender_mail_from_domain": "eumail.docusign.net",
        "sender_object_id": None,
        "sender_ipv4": "162.248.184.10",
        "sender_ipv6": None,
        "recipient_persona": "sam.rivera",
        "direction": "Inbound",
        "delivery_action": "Delivered",
        "delivery_location": "Inbox",
        "email_action": "No action taken",
        "email_action_policy": None,
        "email_action_policy_guid": None,
        "email_size": 51201,
        "bulk_complaint_level": 1,
        "authentication_details": "SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        "confidence_level": '{"Spam":"1"}',
        "threat_types": None,
        "threat_names": None,
        "threat_classification": None,
        "detection_methods": None,
        "is_first_contact": True,
        "language": "en",
        "attachments": [
            {
                "file_name": "NDA_Contoso_Northwind.pdf",
                "extension": "pdf",
                "file_type": "PDF Document",
                "file_size": 48201,
            },
        ],
        "urls": [
            {
                "url": "https://www.docusign.net/Member/EmailStart.aspx?envelopeId=abc123",
                "domain": "docusign.net",
                "location": "Body",
            },
        ],
    },
    {
        "subject": "Action required: Verify your Microsoft account before May 5",
        "sender_display_name": "Microsoft Security",
        "sender_from_address": "no-reply@securemail-update.io",
        "sender_from_domain": "securemail-update.io",
        "sender_mail_from_address": "bounce@securemail-update.io",
        "sender_mail_from_domain": "securemail-update.io",
        "sender_object_id": None,
        "sender_ipv4": "185.244.25.121",
        "sender_ipv6": None,
        "recipient_persona": "priya.iyer",
        "direction": "Inbound",
        "delivery_action": "Blocked",
        "delivery_location": "Quarantine",
        "email_action": "Send to quarantine",
        "email_action_policy": "Anti-phishing user impersonation",
        "email_action_policy_guid": "8d2d8c45-2f9f-4c5e-8b1a-1c12fbb1d9e6",
        "email_size": 18394,
        "bulk_complaint_level": 1,
        "authentication_details": "SPF=fail; DKIM=none; DMARC=fail; CompAuth=fail (reason=000)",
        "confidence_level": '{"Phish":"High"}',
        "threat_types": "Phish",
        "threat_names": "Phish:HTML/Generic.A",
        "threat_classification": "Credential phishing",
        "detection_methods": "URL detonation reputation, Heuristic clustering",
        "is_first_contact": True,
        "language": "en",
        "attachments": [
            {
                "file_name": "password_reset_form.html",
                "extension": "html",
                "file_type": "HTML Document",
                "file_size": 7821,
            },
        ],
        "urls": [
            {
                "url": "https://securemail-update.io/verify?u=priya.iyer",
                "domain": "securemail-update.io",
                "location": "Body",
            },
            {
                "url": "http://malicious-redirect.example/track?m=99281",
                "domain": "malicious-redirect.example",
                "location": "Body",
            },
        ],
    },
    {
        "subject": "Re: Q3 forecast — updated numbers",
        "sender_display_name": "Avery Chen",
        "sender_from_address": "avery.chen@contoso.com",
        "sender_from_domain": "contoso.com",
        "sender_mail_from_address": "avery.chen@contoso.com",
        "sender_mail_from_domain": "contoso.com",
        "sender_object_id": "8a9b1c2d-3e4f-4061-8283-94a5b6c7d8e9",
        "sender_ipv4": None,
        "sender_ipv6": None,
        "recipient_persona": "jordan.patel",
        "direction": "Intra-org",
        "delivery_action": "Delivered",
        "delivery_location": "Inbox",
        "email_action": "No action taken",
        "email_action_policy": None,
        "email_action_policy_guid": None,
        "email_size": 89102,
        "bulk_complaint_level": 0,
        "authentication_details": "SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        "confidence_level": '{"Spam":"-1"}',
        "threat_types": None,
        "threat_names": None,
        "threat_classification": None,
        "detection_methods": None,
        "is_first_contact": False,
        "language": "en",
        "attachments": [
            {
                "file_name": "Q3_forecast_v3.xlsx",
                "extension": "xlsx",
                "file_type": "Excel Workbook",
                "file_size": 64218,
            },
        ],
        "urls": [
            {
                "url": "https://contoso-my.sharepoint.com/personal/avery_chen/Q3_forecast_v3.xlsx",
                "domain": "contoso-my.sharepoint.com",
                "location": "Body",
            },
        ],
    },
    {
        "subject": "Avery Chen mentioned you in #engineering",
        "sender_display_name": "Microsoft Teams",
        "sender_from_address": "noreply@email.teams.microsoft.com",
        "sender_from_domain": "email.teams.microsoft.com",
        "sender_mail_from_address": "noreply@email.teams.microsoft.com",
        "sender_mail_from_domain": "email.teams.microsoft.com",
        "sender_object_id": None,
        "sender_ipv4": "52.114.6.45",
        "sender_ipv6": None,
        "recipient_persona": "sam.rivera",
        "direction": "Inbound",
        "delivery_action": "Delivered",
        "delivery_location": "Inbox",
        "email_action": "No action taken",
        "email_action_policy": None,
        "email_action_policy_guid": None,
        "email_size": 9412,
        "bulk_complaint_level": 1,
        "authentication_details": "SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        "confidence_level": '{"Spam":"1"}',
        "threat_types": None,
        "threat_names": None,
        "threat_classification": None,
        "detection_methods": None,
        "is_first_contact": False,
        "language": "en",
        "attachments": [],
        "urls": [
            {
                "url": "https://teams.microsoft.com/l/message/19:abc/1715000000000",
                "domain": "teams.microsoft.com",
                "location": "Body",
            },
        ],
    },
    {
        "subject": "Industry watch: 5 trends shaping Q3",
        "sender_display_name": "Contoso Marketing",
        "sender_from_address": "newsletter@mc.contoso-marketing.io",
        "sender_from_domain": "mc.contoso-marketing.io",
        "sender_mail_from_address": "bounce-mc@mc.contoso-marketing.io",
        "sender_mail_from_domain": "mc.contoso-marketing.io",
        "sender_object_id": None,
        "sender_ipv4": "198.2.180.45",
        "sender_ipv6": None,
        "recipient_persona": "avery.chen",
        "direction": "Inbound",
        "delivery_action": "Junked",
        "delivery_location": "JunkFolder",
        "email_action": "Move message to junk mail folder",
        "email_action_policy": "Antispam bulk mail",
        "email_action_policy_guid": "7e1c8a3b-9d2f-4d3e-b8a2-9c4e9b3d1f6a",
        "email_size": 31415,
        "bulk_complaint_level": 7,
        "authentication_details": "SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        "confidence_level": '{"Spam":"5"}',
        "threat_types": None,
        "threat_names": None,
        "threat_classification": None,
        "detection_methods": "Bulk mail",
        "is_first_contact": False,
        "language": "en",
        "attachments": [],
        "urls": [
            {
                "url": "https://mc.contoso-marketing.io/track?c=12345",
                "domain": "mc.contoso-marketing.io",
                "location": "Body",
            },
            {
                "url": "https://contoso-marketing.io/unsubscribe",
                "domain": "contoso-marketing.io",
                "location": "Body",
            },
        ],
    },
    {
        "subject": "Quarterly SOC update for Northwind",
        "sender_display_name": "Sam Rivera",
        "sender_from_address": "sam.rivera@contoso.com",
        "sender_from_domain": "contoso.com",
        "sender_mail_from_address": "sam.rivera@contoso.com",
        "sender_mail_from_domain": "contoso.com",
        "sender_object_id": "2c3d4e5f-6071-4293-a4b5-c6d7e8f90112",
        "sender_ipv4": "73.62.18.101",
        "sender_ipv6": None,
        "recipient_persona": "robin.park_acme.com#EXT#",
        "direction": "Outbound",
        "delivery_action": "Delivered",
        "delivery_location": "On-premises/External",
        "email_action": "No action taken",
        "email_action_policy": None,
        "email_action_policy_guid": None,
        "email_size": 102488,
        "bulk_complaint_level": 0,
        "authentication_details": "SPF=pass; DKIM=pass; DMARC=pass; CompAuth=pass",
        "confidence_level": '{"Spam":"-1"}',
        "threat_types": None,
        "threat_names": None,
        "threat_classification": None,
        "detection_methods": None,
        "is_first_contact": False,
        "language": "en",
        "attachments": [
            {
                "file_name": "soc_update_northwind.pdf",
                "extension": "pdf",
                "file_type": "PDF Document",
                "file_size": 91204,
            },
        ],
        "urls": [
            {
                "url": "https://contoso.com/security/disclosures",
                "domain": "contoso.com",
                "location": "Body",
            },
        ],
    },
]


def _resolve_recipient(persona: str, users: tuple[User, ...]) -> User:
    # Hash-index fallback when the persona has been removed from the world.
    match = next((u for u in users if u.sam_account_name == persona), None)
    if match is not None:
        return match
    return users[hash(persona) % len(users)]


class EmailCorpus:
    """Per-World email pool — resolves recipients and mints stable IDs once."""

    def __init__(self, world: World) -> None:
        resolved: list[dict[str, Any]] = []
        for tpl in _EMAIL_TEMPLATES:
            entry = {**tpl}
            entry["network_message_id"] = _new_network_message_id()
            entry["internet_message_id"] = _new_internet_message_id(
                tpl["sender_mail_from_domain"]
            )
            entry["attachments"] = [
                {**a, "sha256": _sha256_hex(a["file_name"])} for a in tpl["attachments"]
            ]
            entry["urls"] = list(tpl["urls"])
            entry["recipient"] = _resolve_recipient(
                tpl["recipient_persona"], world.users
            )
            resolved.append(entry)
        self.entries: tuple[dict[str, Any], ...] = tuple(resolved)

    def pick(self) -> dict[str, Any]:
        return random.choice(self.entries)

    def pick_with_attachments(self) -> dict[str, Any]:
        candidates = [e for e in self.entries if e["attachments"]]
        return random.choice(candidates)

    def pick_with_urls(self) -> dict[str, Any]:
        candidates = [e for e in self.entries if e["urls"]]
        return random.choice(candidates)


@functools.lru_cache(maxsize=4)
def corpus_for(world: World) -> EmailCorpus:
    # Cached on World (frozen + hashable) — one corpus per generate run.
    return EmailCorpus(world)
