from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import BlockDecision


class BaseHookOutput(BaseModel):
    """Base class for all hook outputs with common control fields."""
    model_config = ConfigDict(populate_by_name=True)

    continue_: Optional[bool] = Field(default=True, alias='continue')
    stopReason: Optional[str] = None
    suppressOutput: Optional[bool] = False
    systemMessage: Optional[str] = None


class BaseBlockingHookOutput(BaseHookOutput):
    """Base output class for hooks that can block with decision/reason fields."""
    decision: Optional[BlockDecision] = None
    reason: Optional[str] = None