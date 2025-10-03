from enum import Enum


class SourceClient(str, Enum):
    """The AI editor/IDE that originated the hook"""
    CLAUDE_CODE = "claude-code"
    CURSOR = "cursor"
