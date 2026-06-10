from datetime import datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class AgentsInfo(BaseModel):
    Timestamp: Optional[datetime] = Field(None, description="Date and time the agent information was recorded")
    AgentId: Optional[str] = Field(None, description="Unique identifier for the agent")
    AgentName: Optional[str] = Field(None, description="Display name of the agent")
    Platform: Optional[str] = Field(None, description="The platform that provided the information about the agent")
    AgentDescription: Optional[str] = Field(None, description="Description of the agent as displayed in the agent's source")
    Version: Optional[str] = Field(None, description="Version of the agent")
    SourceAgentId: Optional[str] = Field(None, description="Native identifier assigned by the platform where the agent originated")
    EntraAgentId: Optional[str] = Field(None, description="The agent's unique enterprise application object identifier by Microsoft Entra ID")
    EntraBlueprintId: Optional[str] = Field(None, description="The unique identifier by Microsoft Entra ID for the agent identity blueprint, which serves as the template from which the agent's identity was created")
    ToolsAuthenticationType: Optional[Any] = Field(None, description="Structured summary of agent identity, authentication, and authorization model")
    Permissions: Optional[Any] = Field(None, description="Permissions record of the agent, including those that have been requested and granted, their approval state, and consent enumeration")
    PublishedStatus: Optional[str] = Field(None, description="The agent's publication status; possible values:Draft,Published")
    LifecycleStatus: Optional[str] = Field(None, description="The agent's current operational state in the tenant; possible values:Active,Blocked,Uninstalled,Deleted")
    Availability: Optional[str] = Field(None, description="The deployment scope of the agent (that is, whether deployed to all users, specific groups, or individual users)")
    CreatedDateTime: Optional[datetime] = Field(None, description="Date and time when the agent was created")
    LastPublishedDateTime: Optional[datetime] = Field(None, description="Date and time when the agent was last published or deployed")
    LastUpdatedDateTime: Optional[datetime] = Field(None, description="Date and time when the agent's metadata was last modified")
    Owners: Optional[Any] = Field(None, description="Primary owners of the agent")
    SharedWith: Optional[Any] = Field(None, description="The users and security groups the agent has been shared with")
    InstanceCount: Optional[int] = Field(None, description="Number of agent instances created from the same Microsoft Entra ID agent identity blueprint")
    Instructions: Optional[str] = Field(None, description="The agent's system prompt that defines its default behavior, persona, and operating boundaries")
    Model: Optional[str] = Field(None, description="The AI model powering the agent")
    Channels: Optional[Any] = Field(None, description="The channels or surfaces where the agent can operate, such as Microsoft 365 applications or APIs")
    Capabilities: Optional[Any] = Field(None, description="The intents, actions, skills, and orchestrations of the agent")
    DeclaredDataSources: Optional[Any] = Field(None, description="The data repositories and knowledge sources the agent can access")
    DeclaredTools: Optional[Any] = Field(None, description="Functional tools the agent can invoke at runtime")
    McpServers: Optional[Any] = Field(None, description="The Model Context Protocol (MCP) servers connected to the agent, including server URLs and credential configuration")
    Skills: Optional[Any] = Field(None, description="Skills attached to the agent")
    ConnectedAgents: Optional[Any] = Field(None, description="List of other agents connected to the agent for multi-agent orchestration")
    Memory: Optional[Any] = Field(None, description="The agent's declarative memory store configuration")
    Triggers: Optional[Any] = Field(None, description="List of the agent's triggers")
    Guardrails: Optional[Any] = Field(None, description="Guardrails attached to the agent and their coverage")
    Endpoints: Optional[Any] = Field(None, description="List of agent runtime endpoints, including URL, transport type, and external connectivity flag")
    ObservabilityId: Optional[Any] = Field(None, description="Unique identifier used to correlate the agent with its usage and activity data in Microsoft Agent 365")
    RawAgentInfo: Optional[Any] = Field(None, description="Additional information about the agent, in JSON format")
