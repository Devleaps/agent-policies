from typing import Callable, Literal, Optional

from pydantic import BaseModel

from .output_base import BaseHookOutput


class SessionStartInput(BaseModel):
    """Input for SessionStart hook based on Claude Code documentation."""
    session_id: str
    transcript_path: str
    hook_event_name: Literal["SessionStart"]
    source: str


class SessionStartHookSpecificOutput(BaseModel):
    """Hook-specific output for SessionStart hook."""
    hookEventName: str = "SessionStart"
    additionalContext: Optional[str] = None


class SessionStartOutput(BaseHookOutput):
    """Output for SessionStart hook based on Claude Code documentation."""
    hookSpecificOutput: Optional[SessionStartHookSpecificOutput] = None


# Type alias for handler function signature
SessionStartHandler = Callable[[SessionStartInput], SessionStartOutput]