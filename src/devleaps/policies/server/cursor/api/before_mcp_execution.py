"""
beforeMCPExecution hook models.
"""
from typing import Any, Dict, Optional

from .common import BaseHookInput, BaseHookOutput


class BeforeMCPExecutionInput(BaseHookInput):
    """Input for beforeMCPExecution hook."""
    tool_name: str
    tool_input: Dict[str, Any]
    url: Optional[str] = None
    command: Optional[str] = None


class BeforeMCPExecutionOutput(BaseHookOutput):
    """Output for beforeMCPExecution hook."""
    pass
