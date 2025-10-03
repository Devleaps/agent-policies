"""
afterFileEdit hook models.
"""
from typing import List

from pydantic import BaseModel

from .common import BaseHookInput, BaseHookOutput


class FileEdit(BaseModel):
    """Represents a single file edit."""
    start_line: int
    end_line: int
    new_content: str


class AfterFileEditInput(BaseHookInput):
    """Input for afterFileEdit hook."""
    file_path: str
    edits: List[FileEdit]


class AfterFileEditOutput(BaseHookOutput):
    """Output for afterFileEdit hook."""
    pass
