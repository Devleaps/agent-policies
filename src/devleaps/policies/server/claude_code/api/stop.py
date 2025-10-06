from typing import Callable, Literal, Optional

from pydantic import BaseModel

from .output_base import BaseBlockingHookOutput


class StopInput(BaseModel):
    """Input for Stop hook based on Claude Code documentation."""
    session_id: str
    transcript_path: str
    hook_event_name: Literal["Stop"]
    stop_hook_active: Optional[bool] = None


class SubagentStopInput(BaseModel):
    """Input for SubagentStop hook based on Claude Code documentation."""
    session_id: str
    transcript_path: str
    hook_event_name: Literal["SubagentStop"]
    stop_hook_active: Optional[bool] = None


class StopOutput(BaseBlockingHookOutput):
    """Output for Stop hook based on Claude Code documentation."""
    pass


class SubagentStopOutput(BaseBlockingHookOutput):
    """Output for SubagentStop hook based on Claude Code documentation."""
    pass


# Type aliases for handler function signatures
StopHandler = Callable[[StopInput], StopOutput]
SubagentStopHandler = Callable[[SubagentStopInput], SubagentStopOutput]