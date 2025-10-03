import logging

from fastapi import APIRouter

from ..executor import execute_handlers_generic
from . import mapper
from .api.enums import PermissionDecision, ToolName
from .api.notification import NotificationInput, NotificationOutput
from .api.post_tool_use import PostToolUseInput, PostToolUseOutput
from .api.pre_compact import PreCompactInput, PreCompactOutput
from .api.pre_tool_use import (
    PreToolUseHookSpecificOutput,
    PreToolUseInput,
    PreToolUseOutput,
)
from .api.session_end import SessionEndInput, SessionEndOutput
from .api.session_start import (
    SessionStartHookSpecificOutput,
    SessionStartInput,
    SessionStartOutput,
)
from .api.stop import StopInput, StopOutput, SubagentStopInput, SubagentStopOutput
from .api.user_prompt_submit import UserPromptSubmitInput, UserPromptSubmitOutput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy/claude-code")





def _log_pretool_use_outcome(input_data: PreToolUseInput, result: PreToolUseOutput):
    """Log the outcome of a PreToolUse hook with structured data."""
    continue_status = "CONTINUE" if result.continue_ else "BLOCK"

    permission_decision = None
    if result.hookSpecificOutput and result.hookSpecificOutput.permissionDecision:
        permission_decision = result.hookSpecificOutput.permissionDecision.value

    logger.info(
        f"PreToolUse: {continue_status} {permission_decision}",
        extra={
            "hook": "PreToolUse",
            "session_id": input_data.session_id,
            "tool_name": input_data.tool_name.value if hasattr(input_data.tool_name, 'value') else str(input_data.tool_name),
            "continue": result.continue_,
            "permission": permission_decision,
        }
    )


def _log_generic_hook_outcome(hook_name: str, input_data, result):
    """Log the outcome of a generic hook with structured data."""
    outcome = "CONTINUE" if result.continue_ else "BLOCK"
    logger.info(
        f"{hook_name}: {outcome}",
        extra={
            "hook": hook_name,
            "session_id": input_data.session_id,
            "continue": result.continue_,
        }
    )


@router.post("/PreToolUse", response_model=PreToolUseOutput, response_model_exclude_none=True)
async def pre_tool_use_hook(input_data: PreToolUseInput) -> PreToolUseOutput:
    """Handle PreToolUse hook events."""
    logger.debug(
        "PreToolUse hook received",
        extra={
            "hook": "PreToolUse",
            "session_id": input_data.session_id,
            "tool_name": input_data.tool_name.value if hasattr(input_data.tool_name, 'value') else str(input_data.tool_name),
        }
    )

    generic_input = mapper.map_pre_tool_use_input(input_data)

    results = execute_handlers_generic(generic_input)

    # Default to ASK for Bash and WebFetch
    if input_data.tool_name in [ToolName.BASH, ToolName.WEB_FETCH]:
        default_decision = PermissionDecision.ASK
    else:
        default_decision = PermissionDecision.ALLOW

    default = PreToolUseOutput(
        continue_=True,
        hookSpecificOutput=PreToolUseHookSpecificOutput(
            permissionDecision=default_decision
        )
    )

    result = mapper.map_to_pre_tool_use_output(results, default)
    _log_pretool_use_outcome(input_data, result)
    return result


@router.post("/PostToolUse", response_model=PostToolUseOutput, response_model_exclude_none=True)
async def post_tool_use_hook(input_data: PostToolUseInput) -> PostToolUseOutput:
    """Handle PostToolUse hook events."""
    logger.info(f"PostToolUse hook: {input_data.tool_name} in session {input_data.session_id}")

    generic_input = mapper.map_post_tool_use_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = PostToolUseOutput(continue_=True)
    result = mapper.map_to_post_tool_use_output(results, default)
    _log_generic_hook_outcome("PostToolUse", input_data, result)
    return result


@router.post("/UserPromptSubmit", response_model=UserPromptSubmitOutput, response_model_exclude_none=True)
async def user_prompt_submit_hook(input_data: UserPromptSubmitInput) -> UserPromptSubmitOutput:
    """Handle UserPromptSubmit hook events."""
    logger.info(f"UserPromptSubmit hook: session {input_data.session_id}")

    generic_input = mapper.map_user_prompt_submit_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = UserPromptSubmitOutput(continue_=True)
    result = mapper.map_to_user_prompt_submit_output(results, default)
    _log_generic_hook_outcome("UserPromptSubmit", input_data, result)
    return result


@router.post("/Stop", response_model=StopOutput, response_model_exclude_none=True)
async def stop_hook(input_data: StopInput) -> StopOutput:
    """Handle Stop hook events."""
    logger.info(f"Stop hook: session {input_data.session_id}")

    generic_input = mapper.map_stop_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = StopOutput(continue_=True)
    result = mapper.map_to_stop_output(results, default)
    _log_generic_hook_outcome("Stop", input_data, result)
    return result


@router.post("/SubagentStop", response_model=SubagentStopOutput, response_model_exclude_none=True)
async def subagent_stop_hook(input_data: SubagentStopInput) -> SubagentStopOutput:
    """Handle SubagentStop hook events."""
    logger.info(f"SubagentStop hook: session {input_data.session_id}")

    generic_input = mapper.map_subagent_stop_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = SubagentStopOutput(continue_=True)
    result = mapper.map_to_subagent_stop_output(results, default)
    _log_generic_hook_outcome("SubagentStop", input_data, result)
    return result


@router.post("/Notification", response_model=NotificationOutput, response_model_exclude_none=True)
async def notification_hook(input_data: NotificationInput) -> NotificationOutput:
    """Handle Notification hook events."""
    logger.info(f"Notification hook: session {input_data.session_id}")

    generic_input = mapper.map_notification_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = NotificationOutput(continue_=True)
    result = mapper.map_to_notification_output(results, default)
    _log_generic_hook_outcome("Notification", input_data, result)
    return result


@router.post("/PreCompact", response_model=PreCompactOutput, response_model_exclude_none=True)
async def pre_compact_hook(input_data: PreCompactInput) -> PreCompactOutput:
    """Handle PreCompact hook events."""
    logger.info(f"PreCompact hook: session {input_data.session_id}")

    generic_input = mapper.map_pre_compact_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = PreCompactOutput(continue_=True)
    result = mapper.map_to_pre_compact_output(results, default)
    _log_generic_hook_outcome("PreCompact", input_data, result)
    return result


@router.post("/SessionStart", response_model=SessionStartOutput, response_model_exclude_none=True)
async def session_start_hook(input_data: SessionStartInput) -> SessionStartOutput:
    """Handle SessionStart hook events."""
    logger.info(f"SessionStart hook: session {input_data.session_id}")

    generic_input = mapper.map_session_start_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = SessionStartOutput(
        continue_=True,
        hookSpecificOutput=SessionStartHookSpecificOutput()
    )
    result = mapper.map_to_session_start_output(results, default)
    _log_generic_hook_outcome("SessionStart", input_data, result)
    return result


@router.post("/SessionEnd", response_model=SessionEndOutput, response_model_exclude_none=True)
async def session_end_hook(input_data: SessionEndInput) -> SessionEndOutput:
    """Handle SessionEnd hook events."""
    logger.info(f"SessionEnd hook: session {input_data.session_id}")

    generic_input = mapper.map_session_end_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = SessionEndOutput(continue_=True)
    result = mapper.map_to_session_end_output(results, default)
    _log_generic_hook_outcome("SessionEnd", input_data, result)
    return result
