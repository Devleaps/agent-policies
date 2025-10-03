"""
stop hook models.
"""
from typing import Optional

from .common import BaseHookInput, BaseHookOutput


class StopInput(BaseHookInput):
    """Input for stop hook."""
    completion_status: Optional[str] = None


class StopOutput(BaseHookOutput):
    """Output for stop hook."""
    pass
