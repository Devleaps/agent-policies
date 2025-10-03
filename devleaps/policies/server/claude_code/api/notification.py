from typing import Callable, Literal

from pydantic import BaseModel

from .output_base import BaseHookOutput


class NotificationInput(BaseModel):
    """Input for Notification hook based on Claude Code documentation."""
    session_id: str
    transcript_path: str
    cwd: str
    hook_event_name: Literal["Notification"]
    message: str


class NotificationOutput(BaseHookOutput):
    """Output for Notification hook based on Claude Code documentation."""
    pass


# Type alias for handler function signature
NotificationHandler = Callable[[NotificationInput], NotificationOutput]