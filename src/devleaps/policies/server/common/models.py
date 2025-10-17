from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel

from .enums import SourceClient


@dataclass
class BaseEvent:
    """Base class for all hook events."""
    session_id: str
    source_client: SourceClient
    workspace_roots: Optional[List[str]] = None
    source_event: Any = None  # Original hook input data object


class PolicyAction(str, Enum):
    """Generic policy decision actions"""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"
    HALT = "halt"  # Stop the entire process (Claude Code continue_=False)


# Policy decision precedence: highest priority first
# When multiple policy decisions are returned, the first matching action in this list wins
POLICY_PRECEDENCE: List[PolicyAction] = [
    PolicyAction.HALT,
    PolicyAction.DENY,
    PolicyAction.ASK,
    PolicyAction.ALLOW
]


@dataclass
class PolicyDecision:
    """A decision about whether to allow/deny/halt an action"""
    action: PolicyAction
    reason: Optional[str] = None


@dataclass
class PolicyGuidance:
    """Guidance/context without making a decision - always shown to both user and agent"""
    content: str
    metadata: Optional[Dict[str, Any]] = None


class PatchLine(BaseModel):
    """Represents a single line in a patch with operation type and content separated"""
    operation: Literal["added", "removed", "unchanged"]  # Whether line was added, removed, or unchanged
    content: str  # The actual line content (without the +/- prefix)


class StructuredPatch(BaseModel):
    """Represents a single patch in a structured diff"""
    oldStart: int  # Line number where old content starts
    oldLines: int  # Number of lines in old content
    newStart: int  # Line number where new content starts
    newLines: int  # Number of lines in new content
    lines: List[PatchLine]  # Parsed diff lines with operation and content separated


@dataclass
class ToolUseEvent(BaseEvent):
    """
    Generic representation of tool/command execution.
    Maps from:
    - Claude Code: PreToolUse (Bash, WebFetch, MCP tools)
    - Cursor: beforeShellExecution, beforeMCPExecution
    """
    tool_name: str = ""  # "bash", "mcp__*", etc.
    tool_is_bash: bool = False
    tool_is_mcp: bool = False
    command: Optional[str] = None  # For bash-like tools
    parameters: Optional[Dict[str, Any]] = None  # For other tools


@dataclass
class PromptSubmitEvent(BaseEvent):
    """
    Generic representation of user prompt submission.
    Maps from:
    - Claude Code: UserPromptSubmit
    - Cursor: beforeSubmitPrompt
    """
    prompt: Optional[str] = None


@dataclass
class FileEditEvent(BaseEvent):
    """
    Generic representation of file edit events (BEFORE they happen).
    Maps from:
    - Claude Code: PreToolUse (Edit/Write tools)

    Policies can ALLOW or DENY file edits before they are executed.
    """
    file_path: Optional[str] = None
    operation: Optional[str] = None  # "edit", "write", etc.


@dataclass
class StopEvent(BaseEvent):
    """
    Generic representation of stop/interrupt events.
    Maps from:
    - Claude Code: Stop, SubagentStop
    - Cursor: stop
    """
    stop_type: Optional[str] = None  # "stop", "subagent_stop", etc.


@dataclass
class PostFileEditEvent(BaseEvent):
    """
    Generic representation of file edit events (AFTER they happen).
    Maps from:
    - Claude Code: PostToolUse (Edit/Write tools)

    Policies can yield guidance or additional context after file edits complete.
    """
    file_path: Optional[str] = None
    operation: Optional[str] = None  # "edit", "write", etc.
    content: Optional[str] = None  # The full file content after the edit
    structured_patch: Optional[List[StructuredPatch]] = None  # List of structured diffs


@dataclass
class PostToolUseEvent(BaseEvent):
    """
    Generic representation of tool execution completion.
    Maps from:
    - Claude Code: PostToolUse (all tools except Edit/Write which map to PostFileEditEvent)

    Policies can yield guidance or additional context after tool execution completes.
    """
    tool_name: str = ""  # "bash", "mcp__*", etc.
    tool_is_bash: bool = False
    tool_is_mcp: bool = False
    command: Optional[str] = None  # For bash-like tools
    parameters: Optional[Dict[str, Any]] = None  # For other tools


@dataclass
class HookEvent(BaseEvent):
    """
    Catch-all for hooks that don't fit specific categories.
    Maps from:
    - Claude Code: SessionStart, SessionEnd, Notification, PreCompact
    - Cursor: beforeReadFile
    - Any future hooks for that matter
    """
    hook_type: str = ""  # "session_start", "session_end", "notification", etc.
