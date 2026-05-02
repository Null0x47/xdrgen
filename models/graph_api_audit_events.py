from typing import Optional

from pydantic import BaseModel, Field


class GraphApiAuditEvents(BaseModel):
    IdentityProvider: Optional[str] = Field(
        None,
        description="Identity provider that authenticated the subject of the token",
    )
    ApiVersion: Optional[str] = Field(None, description="The API version of the event")
    ApplicationId: Optional[str] = Field(
        None, description="Unique identifier for the application"
    )
    IPAddress: Optional[str] = Field(
        None, description="The IP address of the client from where the request was made"
    )
    ClientRequestId: Optional[str] = Field(
        None,
        description="Identifier for the client request sent; if none is available, the operation identifier is used instead",
    )
    EntityType: Optional[str] = Field(
        None,
        description="Type of object, such as a file, a process, a device, or a user, that made the request",
    )
    RequestUri: Optional[str] = Field(
        None, description="Uniform resource identifier (URI) of the request"
    )
    AccountObjectId: Optional[str] = Field(
        None, description="Unique identifier for the account making the request"
    )
    OperationId: Optional[str] = Field(
        None,
        description="Identifier for a batch of requests; the same identifier is used for all requests in a batch but if requests are non-batched, the identifier is unique per request",
    )
    Location: Optional[str] = Field(
        None, description="Name of the region that served the request"
    )
    RequestDuration: Optional[str] = Field(
        None, description="Duration of the request in milliseconds"
    )
    RequestId: Optional[str] = Field(
        None, description="Unique identifier of the request"
    )
    RequestMethod: Optional[str] = Field(None, description="HTTP method of the request")
    Timestamp: Optional[str] = Field(
        None, description="Date and time when the request was recorded"
    )
    ResponseStatusCode: Optional[str] = Field(
        None, description="HTTP response status code for the request"
    )
    Scopes: Optional[str] = Field(None, description="Scopes in token claims")
    UniqueTokenIdentifier: Optional[str] = Field(
        None,
        description="Unique identifier embedded in every access token and ID token that were issued",
    )
    TargetWorkload: Optional[str] = Field(
        None,
        description="The target workload (for example, Microsoft.Exchange, Microsoft.SharePoint) the API call was made to",
    )
    ServicePrincipalId: Optional[str] = Field(
        None, description="The identifier for the Service Principal making the request"
    )
    ResponseSize: Optional[int] = Field(
        None, description="The size of the response in bytes"
    )
