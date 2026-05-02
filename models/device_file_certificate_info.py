from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceFileCertificateInfo(BaseModel):
    CertificateCountersignatureTime: Optional[datetime] = Field(None, description="Date and time (UTC) the certificate was countersigned.")
    CertificateCreationTime: Optional[datetime] = Field(None, description="Date and time (UTC) the certificate was created.")
    CertificateExpirationTime: Optional[datetime] = Field(None, description="Certificate expiry date and time (UTC).")
    CertificateSerialNumber: Optional[str] = Field(None, description="Identifier for the certificate that is unique to the issuing certificate authority (CA).")
    CrlDistributionPointUrls: Optional[str] = Field(None, description="A list of network shares URLs that contains certificates and certificate revocation (CRLs).")
    DeviceId: Optional[str] = Field(None, description="Unique identifier for the device in the service.")
    DeviceName: Optional[str] = Field(None, description="Fully qualified domain name (FQDN) of the device.")
    IsRootSignerMicrosoft: Optional[bool] = Field(None, description="Indicates whether the signer of the root certificate is Microsoft.")
    IsSigned: Optional[bool] = Field(None, description="Indicates whether the file is signed.")
    Issuer: Optional[str] = Field(None, description="Information about the issuing certificate authority (CA).")
    IssuerHash: Optional[str] = Field(None, description="Unique hash value identifying issuing certificate authority (CA).")
    IsTrusted: Optional[bool] = Field(None, description="Indicates whether the file is trusted based on the results of the WinVerifyTrust function, which checks for unknown root certificate information, invalid signatures, revoked certificates, and other questionable attributes.")
    MachineGroup: Optional[str] = Field(None, description="Machine group of the machine. This group is used by role-based access control to determine access to the machine.")
    ReportId: Optional[int] = Field(None, description="Unique identifier for the event.")
    SHA1: Optional[str] = Field(None, description="SHA-1 hash of the file that the recorded action was applied to.")
    SignatureType: Optional[str] = Field(None, description="Indicates whether signature information was read as embedded content in the file itself or read from an external catalog file.")
    Signer: Optional[str] = Field(None, description="Information about the signer of the file.")
    SignerHash: Optional[str] = Field(None, description="Unique hash value identifying the signer.")
    SourceSystem: Optional[str] = Field(None, description="The type of agent the event was collected by. For example,OpsManagerfor Windows agent, either direct connect or Operations Manager,Linuxfor all Linux agents, orAzurefor Azure Diagnostics")
    TenantId: Optional[str] = Field(None, description="The Log Analytics workspace ID")
    TimeGenerated: Optional[datetime] = Field(None, description="Date and time the event was recorded by the MDE agent on the endpoint.")
    Type: Optional[str] = Field(None, description="The name of the table")
