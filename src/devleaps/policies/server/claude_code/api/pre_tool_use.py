from typing import Any, Callable, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .enums import PermissionDecision, ToolName
from .output_base import BaseHookOutput


class PreToolUseInput(BaseModel):
    """Input for PreToolUse hook based on Claude Code documentation."""
    model_config = ConfigDict(validate_assignment=True)  # Allow field mutations

    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: Literal["PreToolUse"]
    tool_name: Union[ToolName, str]  # ToolName enum for standard tools, str for MCP tools
    tool_input: Any  # Tool-specific object that varies by tool

    _command_cache: Optional[str] = None  # Internal cache for command

    @property
    def command(self) -> str:
        """Extract command string from tool_input (cached and stripped)."""
        # Invalidate cache if tool_input has changed since last access
        current_command = self._extract_command()
        if self._command_cache != current_command:
            self._command_cache = current_command
        return self._command_cache

    def _extract_command(self) -> str:
        """Extract command from tool_input."""
        if isinstance(self.tool_input, dict):
            return self.tool_input.get("command", "").strip()
        elif isinstance(self.tool_input, str):
            return self.tool_input.strip()
        else:
            return str(self.tool_input).strip()

    def invalidate_command_cache(self):
        """Invalidate the command cache when tool_input is modified."""
        self._command_cache = None


class PreToolUseHookSpecificOutput(BaseModel):
    """Hook-specific output for PreToolUse hook."""
    hookEventName: str = "PreToolUse"
    permissionDecision: Optional[PermissionDecision] = None
    permissionDecisionReason: Optional[str] = None


class PreToolUseOutput(BaseHookOutput):
    """Output for PreToolUse hook based on Claude Code documentation."""
    hookSpecificOutput: Optional[PreToolUseHookSpecificOutput] = None


# Type alias for handler function signature
PreToolUseHandler = Callable[[PreToolUseInput], PreToolUseOutput]