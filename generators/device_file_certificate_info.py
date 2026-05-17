from __future__ import annotations

import random
from datetime import timedelta

from generators.base import register
from generators.common import now_utc, pick
from generators.device_common import envelope, hashes_for, pick_device
from models import DeviceFileCertificateInfo
from world import World


@register("DeviceFileCertificateInfo")
def generate(world: World) -> DeviceFileCertificateInfo:
    device = pick_device(world)
    cert = pick(world.code_signing_certificates)
    file_name = pick(world.signed_files).value
    _, sha1, _ = hashes_for(file_name)

    # ~95% signed.
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
        CertificateSerialNumber=cert.serial if is_signed else None,
        CrlDistributionPointUrls=(
            pick(world.crl_urls).value
            if is_signed and len(world.crl_urls) > 0
            else None
        ),
        IsRootSignerMicrosoft=cert.is_root_microsoft if is_signed else None,
        IsSigned=is_signed,
        IsTrusted=is_trusted,
        Issuer=cert.issuer if is_signed else None,
        IssuerHash=hashes_for(cert.issuer)[1] if is_signed else None,
        ReportId=random.randint(10**9, 10**10 - 1),
        SHA1=sha1,
        SignatureType=cert.signature_type if is_signed else None,
        Signer=cert.subject if is_signed else None,
        SignerHash=hashes_for(cert.subject)[1] if is_signed else None,
        Type="DeviceFileCertificateInfo",
        **envelope(world, device),
    )
