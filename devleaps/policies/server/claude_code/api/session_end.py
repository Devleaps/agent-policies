from typing import Callable, Literal

from pydantic import BaseModel

from .output_base import BaseHookOutput


class SessionEndInput(BaseModel):
    """Input for SessionEnd hook based on Claude Code documentation."""
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: Literal["SessionEnd"]
    reason: str


class SessionEndOutput(BaseHookOutput):
    """Output for SessionEnd hook based on Claude Code documentation."""
    pass


# Type alias for handler function signature
SessionEndHandler = Callable[[SessionEndInput], SessionEndOutput]