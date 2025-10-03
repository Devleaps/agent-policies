from typing import Callable, Literal, Optional

from pydantic import BaseModel

from .output_base import BaseBlockingHookOutput


class UserPromptSubmitInput(BaseModel):
    """Input for UserPromptSubmit hook based on Claude Code documentation."""
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: Literal["UserPromptSubmit"]
    prompt: str


class UserPromptSubmitHookSpecificOutput(BaseModel):
    """Hook-specific output for UserPromptSubmit hook."""
    hookEventName: str = "UserPromptSubmit"
    additionalContext: Optional[str] = None


class UserPromptSubmitOutput(BaseBlockingHookOutput):
    """Output for UserPromptSubmit hook based on Claude Code documentation."""
    hookSpecificOutput: Optional[UserPromptSubmitHookSpecificOutput] = None


# Type alias for handler function signature
UserPromptSubmitHandler = Callable[[UserPromptSubmitInput], UserPromptSubmitOutput]