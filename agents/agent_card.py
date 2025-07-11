from pydantic import BaseModel
from typing import List, Optional


class AgentSkill(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


class AgentCapabilities(BaseModel):
    streaming: bool = False
    other: Optional[List[str]] = None


class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    skills: List[AgentSkill]
    capabilities: AgentCapabilities
