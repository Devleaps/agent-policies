from typing import Callable, Literal

from pydantic import BaseModel

from .output_base import BaseHookOutput


class PreCompactInput(BaseModel):
    """Input for PreCompact hook based on Claude Code documentation."""
    session_id: str
    transcript_path: str
    hook_event_name: Literal["PreCompact"]
    trigger: str
    custom_instructions: str


class PreCompactOutput(BaseHookOutput):
    """Output for PreCompact hook based on Claude Code documentation."""
    pass


# Type alias for handler function signature
PreCompactHandler = Callable[[PreCompactInput], PreCompactOutput]