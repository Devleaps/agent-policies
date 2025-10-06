from enum import Enum


class PermissionDecision(str, Enum):
    """Permission decisions for PreToolUse hooks."""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


class BlockDecision(str, Enum):
    """Block decisions for PostToolUse, UserPromptSubmit, Stop, and SubagentStop hooks."""
    BLOCK = "block"


class ToolName(str, Enum):
    """Claude Code tool names based on official documentation."""
    # Core Claude Code tools
    TASK = "Task"
    BASH = "Bash"
    GLOB = "Glob"
    GREP = "Grep"
    READ = "Read"
    EDIT = "Edit"
    MULTI_EDIT = "MultiEdit"
    WRITE = "Write"
    WEB_FETCH = "WebFetch"
    WEB_SEARCH = "WebSearch"

    # Additional tools that may be encountered
    NOTEBOOK_EDIT = "NotebookEdit"
    TODO_WRITE = "TodoWrite"
    EXIT_PLAN_MODE = "ExitPlanMode"
    BASH_OUTPUT = "BashOutput"
    KILL_SHELL = "KillShell"

    @classmethod
    def is_mcp_tool(cls, tool_name: str) -> bool:
        """Check if a tool name follows MCP pattern: mcp__<server>__<tool>"""
        return tool_name.startswith("mcp__") and tool_name.count("__") >= 2