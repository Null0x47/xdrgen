from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class AIAgentsInfo(BaseModel):
    Timestamp: Optional[datetime] = Field(
        None, description="Last date and time recorded for the agent info"
    )
    AIAgentId: Optional[str] = Field(
        None,
        description="Unique identifier for the agent as assigned to it in Microsoft 365 Copilot or Copilot Studio",
    )
    AIAgentName: Optional[str] = Field(None, description="Display name of the agent")
    AgentCreationTime: Optional[datetime] = Field(
        None, description="Date and time when the agent was created"
    )
    CreatorAccountUpn: Optional[str] = Field(
        None,
        description="User principal name (UPN) of the account that created the agent",
    )
    OwnerAccountUpns: Optional[str] = Field(
        None, description="User principal names (UPN) of all the owners of the agent"
    )
    LastModifiedByUpn: Optional[str] = Field(
        None,
        description="User principal name (UPN) of the account that last modified that agent",
    )
    LastModifiedTime: Optional[datetime] = Field(
        None, description="Date and time when the agent was last modified"
    )
    LastPublishedTime: Optional[datetime] = Field(
        None, description="Date and time when the agent was last published"
    )
    LastPublishedByUpn: Optional[str] = Field(
        None,
        description="User principal name (UPN) of the account that last published the agent",
    )
    AgentDescription: Optional[str] = Field(
        None, description="Description of the agent as displayed in the agent's source"
    )
    AgentStatus: Optional[str] = Field(
        None,
        description="Status of the agent; possible values: Created, Published, Deleted",
    )
    UserAuthenticationType: Optional[str] = Field(
        None,
        description="The agentâs configured authentication type for users interacting with the agent; possible values: None, Microsoft, Custom",
    )
    AgentUsers: Optional[str] = Field(
        None,
        description="List of user principal names (UPNs) or group IDs that can use the agent",
    )
    KnowledgeDetails: Optional[str] = Field(
        None, description="Details about the knowledge sources added to the agent"
    )
    AgentActionTriggers: Optional[str] = Field(
        None, description="List of triggers that makes an autonomous agent take action"
    )
    RawAgentInfo: Optional[str] = Field(
        None,
        description="Contents of the raw JSON that describes the agent and contains configuration details, as received from the provider",
    )
    AuthenticationTrigger: Optional[str] = Field(
        None,
        description="Indicates when authentication is triggered for the agent; possible values: As Needed, Always",
    )
    AccessControlPolicy: Optional[str] = Field(
        None,
        description="Users that can interact with the agent; possible values: Any, Copilot readers, Group membership, Any (multitenant)",
    )
    AuthorizedSecurityGroupIds: Optional[Any] = Field(
        None,
        description="List of Azure Active Directory Group IDs that are allowed to interact with the agent",
    )
    AgentTopicsDetails: Optional[Any] = Field(
        None, description="Specifications of the topics that the agent can perform"
    )
    AgentToolsDetails: Optional[Any] = Field(
        None,
        description="Specifications of the tools that the agent can access and perform actions on",
    )
    EnvironmentId: Optional[str] = Field(
        None,
        description="The identifier of the Microsoft Power Platform environment the agent resides in",
    )
    Platform: Optional[str] = Field(
        None,
        description="The platform that provided the information about the agents; possible values: Copilot Studio",
    )
    IsGenerativeOrchestrationEnabled: Optional[bool] = Field(
        None,
        description="ndicates whether the agent uses generative orchestration (that is, dynamically chooses tools, knowledge, and actions based on context) to operate",
    )
    AgentAppId: Optional[str] = Field(
        None,
        description="The unique app identifier registered for the agent in Microsoft Entra",
    )
    ConnectedAgentsSchemaNames: Optional[Any] = Field(
        None,
        description="Lists the schema names of connected agents, which are independently managed agents that are linked to the main one for orchestration",
    )
    ChildAgentsSchemaNames: Optional[Any] = Field(
        None,
        description="Lists the schema names of the child agents that exist within the main agent",
    )
