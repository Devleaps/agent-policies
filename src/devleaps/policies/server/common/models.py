from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .enums import SourceClient


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


@dataclass
class ToolUseEvent:
    """
    Generic representation of tool/command execution.
    Maps from:
    - Claude Code: PreToolUse (Bash, WebFetch, MCP tools)
    - Cursor: beforeShellExecution, beforeMCPExecution
    """
    session_id: str
    tool_name: str  # "bash", "mcp__*", etc.
    source_client: SourceClient
    tool_is_bash: bool = False
    tool_is_mcp: bool = False
    command: Optional[str] = None  # For bash-like tools
    parameters: Optional[Dict[str, Any]] = None  # For other tools
    workspace_roots: Optional[List[str]] = None
    source_event: Any = None  # Original hook input data object


@dataclass
class PromptSubmitEvent:
    """
    Generic representation of user prompt submission.
    Maps from:
    - Claude Code: UserPromptSubmit
    - Cursor: beforeSubmitPrompt
    """
    session_id: str
    source_client: SourceClient
    prompt: Optional[str] = None
    workspace_roots: Optional[List[str]] = None
    source_event: Any = None  # Original hook input data object


@dataclass
class FileEditEvent:
    """
    Generic representation of file edit events (BEFORE they happen).
    Maps from:
    - Claude Code: PreToolUse (Edit/Write tools)
    - Cursor: No equivalent at this time

    Policies can ALLOW or DENY file edits before they are executed.
    """
    session_id: str
    source_client: SourceClient
    file_path: Optional[str] = None
    operation: Optional[str] = None  # "edit", "write", etc.
    workspace_roots: Optional[List[str]] = None
    source_event: Any = None  # Original hook input data object


@dataclass
class StopEvent:
    """
    Generic representation of stop/interrupt events.
    Maps from:
    - Claude Code: Stop, SubagentStop
    - Cursor: stop
    """
    session_id: str
    source_client: SourceClient
    stop_type: Optional[str] = None  # "stop", "subagent_stop", etc.
    workspace_roots: Optional[List[str]] = None
    source_event: Any = None  # Original hook input data object


@dataclass
class HookEvent:
    """
    Catch-all for hooks that don't fit specific categories.
    Maps from:
    - Claude Code: SessionStart, SessionEnd, Notification, PreCompact
    - Cursor: beforeReadFile
    - Any future hooks for that matter
    """
    session_id: str
    source_client: SourceClient
    hook_type: str  # "session_start", "session_end", "notification", etc.
    workspace_roots: Optional[List[str]] = None
    source_event: Any = None  # Original hook input data object
