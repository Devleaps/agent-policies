"""
beforeReadFile hook models.
"""
from typing import Any, List, Optional

from .common import BaseHookInput, BaseHookOutput


class BeforeReadFileInput(BaseHookInput):
    """Input for beforeReadFile hook."""
    file_path: str
    content: Optional[str] = None
    attachments: Optional[List[Any]] = None


class BeforeReadFileOutput(BaseHookOutput):
    """Output for beforeReadFile hook."""
    pass
