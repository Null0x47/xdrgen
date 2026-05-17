from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class DeviceTvmCertificateInfo(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time when the event was recorded")
    DeviceId: Optional[str] = Field(None, description="Unique identifier for the device in the service")
    Thumbprint: Optional[str] = Field(None, description="Unique identifier for the certificate")
    Path: Optional[str] = Field(None, description="The location of the certificate")
    SerialNumber: Optional[str] = Field(None, description="Unique identifier for the certificate within a certificate authority's systems")
    IssuedTo: Optional[Any] = Field(None, description="Entity that a certificate belongs to; can be a device, an individual, or an organization")
    IssuedBy: Optional[Any] = Field(None, description="Entity that verified the information and signed the certificate")
    FriendlyName: Optional[str] = Field(None, description="Easy-to-understand version of a certificate's title")
    SignatureAlgorithm: Optional[str] = Field(None, description="Hashing algorithm and encryption algorithm used")
    KeySize: Optional[str] = Field(None, description="Size of the key used in the signature algorithm")
    ExpirationDate: Optional[str] = Field(None, description="The date and time beyond which the certificate is no longer valid")
    IssueDate: Optional[str] = Field(None, description="The earliest date and time when the certificate became valid")
    SubjectType: Optional[str] = Field(None, description="Indicates if the holder of the certificate is a CA or end entity")
    KeyUsage: Optional[str] = Field(None, description="The valid cryptographic uses of the certificate's public key")
    ExtendedKeyUsage: Optional[str] = Field(None, description="Other valid uses for the certificate")
