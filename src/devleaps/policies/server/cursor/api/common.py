"""
Common Cursor hook models and types.
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class Permission(str, Enum):
    """Permission decision for Cursor hooks."""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class BaseHookInput(BaseModel):
    """Base input for all Cursor hooks."""
    conversation_id: str
    generation_id: str
    hook_event_name: str
    workspace_roots: List[str]


class BaseHookOutput(BaseModel):
    """Base output for all Cursor hooks."""
    permission: Optional[Permission] = None
    userMessage: Optional[str] = None
    agentMessage: Optional[str] = None
