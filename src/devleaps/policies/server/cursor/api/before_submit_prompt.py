"""
beforeSubmitPrompt hook models.
"""
from typing import Any, List, Optional

from .common import BaseHookInput, BaseHookOutput


class BeforeSubmitPromptInput(BaseHookInput):
    """Input for beforeSubmitPrompt hook."""
    prompt: str
    attachments: Optional[List[Any]] = None


class BeforeSubmitPromptOutput(BaseHookOutput):
    """Output for beforeSubmitPrompt hook."""
    pass
