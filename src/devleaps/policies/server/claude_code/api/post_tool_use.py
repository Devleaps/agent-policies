from typing import Any, Callable, Literal, Optional, Union

from pydantic import BaseModel

from .enums import ToolName
from .output_base import BaseBlockingHookOutput


class PostToolUseInput(BaseModel):
    """Input for PostToolUse hook based on Claude Code documentation."""
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: Literal["PostToolUse"]
    tool_name: Union[ToolName, str]  # ToolName enum for standard tools, str for MCP tools
    tool_input: Any  # Tool-specific input object
    tool_response: Any  # Tool-specific response object


class PostToolUseHookSpecificOutput(BaseModel):
    """Hook-specific output for PostToolUse hook."""
    hookEventName: str = "PostToolUse"
    additionalContext: Optional[str] = None


class PostToolUseOutput(BaseBlockingHookOutput):
    """Output for PostToolUse hook based on Claude Code documentation."""
    hookSpecificOutput: Optional[PostToolUseHookSpecificOutput] = None


# Type alias for handler function signature
PostToolUseHandler = Callable[[PostToolUseInput], PostToolUseOutput]