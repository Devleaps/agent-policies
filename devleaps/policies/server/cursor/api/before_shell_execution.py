"""
beforeShellExecution hook models.
"""
from .common import BaseHookInput, BaseHookOutput


class BeforeShellExecutionInput(BaseHookInput):
    """Input for beforeShellExecution hook."""
    command: str
    cwd: str


class BeforeShellExecutionOutput(BaseHookOutput):
    """Output for beforeShellExecution hook."""
    pass
