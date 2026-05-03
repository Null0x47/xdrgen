from __future__ import annotations

import random
from datetime import timedelta

from generators.base import register
from generators.common import now_utc
from generators.device_common import envelope, hashes_for, pick_device
from models import DeviceFileCertificateInfo
from world import World

# Curated catalogue of code-signing certificates seen in the wild on signed
# Windows binaries. `is_root_microsoft` mirrors the IsRootSignerMicrosoft
# column — flips on iff the chain terminates at a Microsoft root, which is
# what Defender uses to surface "trusted system binary" rows.
_CERTIFICATES = [
    {
        "subject": "Microsoft Windows",
        "issuer": "Microsoft Windows Production PCA 2011",
        "serial": "33000002ED2C45E4C145CF48E7000000000002",
        "is_root_microsoft": True,
        "signature_type": "Embedded",
    },
    {
        "subject": "Microsoft Corporation",
        "issuer": "Microsoft Code Signing PCA 2011",
        "serial": "33000003318FA52A4D8F2E1F2A000000000333",
        "is_root_microsoft": True,
        "signature_type": "Embedded",
    },
    {
        "subject": "Google LLC",
        "issuer": "DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1",
        "serial": "0AA89F4DEF6C2C4DBD3C1AB37B17EBE5",
        "is_root_microsoft": False,
        "signature_type": "Embedded",
    },
    {
        "subject": "Adobe Inc.",
        "issuer": "DigiCert SHA2 Assured ID Code Signing CA",
        "serial": "0F4F9D2BB12B4E8DAF3E2F46A1F19C2C",
        "is_root_microsoft": False,
        "signature_type": "Embedded",
    },
    {
        "subject": "Mozilla Corporation",
        "issuer": "DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1",
        "serial": "0EE0BCB37BFE32C7B1024F8AF8E1E2F1",
        "is_root_microsoft": False,
        "signature_type": "Embedded",
    },
    {
        "subject": "GitHub, Inc.",
        "issuer": "DigiCert SHA2 Assured ID Code Signing CA",
        "serial": "00B0BCDFA1A0CF24E5BCEDE53C2F7B8B81",
        "is_root_microsoft": False,
        "signature_type": "Embedded",
    },
    {
        "subject": "Slack Technologies, LLC",
        "issuer": "Sectigo RSA Code Signing CA",
        "serial": "0066AB7DC4B0A4E5BCEDE53C2F7B8B82A1",
        "is_root_microsoft": False,
        "signature_type": "Embedded",
    },
]

_SIGNED_FILES = [
    "explorer.exe",
    "powershell.exe",
    "svchost.exe",
    "MsMpEng.exe",
    "msedge.exe",
    "chrome.exe",
    "outlook.exe",
    "winword.exe",
]

_CRL_URLS = [
    "http://www.microsoft.com/pkiops/crl/MicCodSigPCA_2011-07-08.crl",
    "http://crl3.digicert.com/DigiCertTrustedG4CodeSigningRSA4096SHA384.crl",
    "http://crl.sectigo.com/SectigoRSACodeSigningCA.crl",
]


@register("DeviceFileCertificateInfo")
def generate(world: World) -> DeviceFileCertificateInfo:
    device = pick_device(world)
    cert = random.choice(_CERTIFICATES)
    file_name = random.choice(_SIGNED_FILES)
    _, sha1, _ = hashes_for(file_name)

    # Roughly 95% of files in the inventory are signed; a thin tail of
    # unsigned binaries (vendor tools that stripped their signature, etc.).
    is_signed = random.random() < 0.95
    is_trusted = is_signed and random.random() < 0.97

    now = now_utc()
    creation_time = now - timedelta(days=random.randint(180, 365 * 4))
    expiration_time = creation_time + timedelta(days=365 * 3)
    countersignature_time = creation_time + timedelta(seconds=random.randint(60, 600))

    return DeviceFileCertificateInfo(
        CertificateCountersignatureTime=countersignature_time if is_signed else None,
        CertificateCreationTime=creation_time if is_signed else None,
        CertificateExpirationTime=expiration_time if is_signed else None,
        CertificateSerialNumber=cert["serial"] if is_signed else None,
        CrlDistributionPointUrls=random.choice(_CRL_URLS) if is_signed else None,
        IsRootSignerMicrosoft=cert["is_root_microsoft"] if is_signed else None,
        IsSigned=is_signed,
        IsTrusted=is_trusted,
        Issuer=cert["issuer"] if is_signed else None,
        IssuerHash=hashes_for(cert["issuer"])[1] if is_signed else None,
        ReportId=random.randint(10**9, 10**10 - 1),
        SHA1=sha1,
        SignatureType=cert["signature_type"] if is_signed else None,
        Signer=cert["subject"] if is_signed else None,
        SignerHash=hashes_for(cert["subject"])[1] if is_signed else None,
        Type="DeviceFileCertificateInfo",
        **envelope(world, device),
    )
