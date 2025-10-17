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
from .api.request_wrapper import RequestWrapper
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
    """Log the outcome of a PreToolUse hook with response body."""
    continue_status = "CONTINUE" if result.continue_ else "BLOCK"
    response_body = result.model_dump(exclude_none=True) if hasattr(result, 'model_dump') else result

    logger.info(f"PreToolUse: {continue_status} | Response: {response_body}")


def _log_generic_hook_outcome(hook_name: str, input_data, result):
    """Log the outcome of a generic hook with response body."""
    outcome = "CONTINUE" if result.continue_ else "BLOCK"
    response_body = result.model_dump(exclude_none=True) if hasattr(result, 'model_dump') else result
    logger.info(f"{hook_name}: {outcome} | Response: {response_body}")


@router.post("/PreToolUse", response_model=PreToolUseOutput, response_model_exclude_none=True)
async def pre_tool_use_hook(wrapper: RequestWrapper) -> PreToolUseOutput:
    """Handle PreToolUse hook events."""
    input_data = PreToolUseInput(**wrapper.event)
    bundles = wrapper.bundles

    tool_name_str = input_data.tool_name.value if hasattr(input_data.tool_name, 'value') else str(input_data.tool_name)
    logger.info(f"PreToolUse hook: {tool_name_str} in session {input_data.session_id}")

    generic_input = mapper.map_pre_tool_use_input(input_data)

    results = execute_handlers_generic(generic_input, bundles)

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
async def post_tool_use_hook(wrapper: RequestWrapper) -> PostToolUseOutput:
    """Handle PostToolUse hook events."""
    input_data = PostToolUseInput(**wrapper.event)
    bundles = wrapper.bundles

    logger.info(f"PostToolUse hook: {input_data.tool_name} in session {input_data.session_id}")

    generic_input = mapper.map_post_tool_use_input(input_data)

    results = execute_handlers_generic(generic_input, bundles)

    default = PostToolUseOutput(continue_=True)
    result = mapper.map_to_post_tool_use_output(results, default)
    _log_generic_hook_outcome("PostToolUse", input_data, result)
    return result


@router.post("/UserPromptSubmit", response_model=UserPromptSubmitOutput, response_model_exclude_none=True)
async def user_prompt_submit_hook(wrapper: RequestWrapper) -> UserPromptSubmitOutput:
    """Handle UserPromptSubmit hook events."""
    input_data = UserPromptSubmitInput(**wrapper.event)
    bundles = wrapper.bundles

    logger.info(f"UserPromptSubmit hook: session {input_data.session_id}")

    generic_input = mapper.map_user_prompt_submit_input(input_data)

    results = execute_handlers_generic(generic_input, bundles)

    default = UserPromptSubmitOutput(continue_=True)
    result = mapper.map_to_user_prompt_submit_output(results, default)
    _log_generic_hook_outcome("UserPromptSubmit", input_data, result)
    return result


@router.post("/Stop", response_model=StopOutput, response_model_exclude_none=True)
async def stop_hook(wrapper: RequestWrapper) -> StopOutput:
    """Handle Stop hook events."""
    input_data = StopInput(**wrapper.event)
    bundles = wrapper.bundles

    logger.info(f"Stop hook: session {input_data.session_id}")

    generic_input = mapper.map_stop_input(input_data)

    results = execute_handlers_generic(generic_input, bundles)

    default = StopOutput(continue_=True)
    result = mapper.map_to_stop_output(results, default)
    _log_generic_hook_outcome("Stop", input_data, result)
    return result


@router.post("/SubagentStop", response_model=SubagentStopOutput, response_model_exclude_none=True)
async def subagent_stop_hook(wrapper: RequestWrapper) -> SubagentStopOutput:
    """Handle SubagentStop hook events."""
    input_data = SubagentStopInput(**wrapper.event)
    bundles = wrapper.bundles

    logger.info(f"SubagentStop hook: session {input_data.session_id}")

    generic_input = mapper.map_subagent_stop_input(input_data)

    results = execute_handlers_generic(generic_input, bundles)

    default = SubagentStopOutput(continue_=True)
    result = mapper.map_to_subagent_stop_output(results, default)
    _log_generic_hook_outcome("SubagentStop", input_data, result)
    return result


@router.post("/Notification", response_model=NotificationOutput, response_model_exclude_none=True)
async def notification_hook(wrapper: RequestWrapper) -> NotificationOutput:
    """Handle Notification hook events."""
    input_data = NotificationInput(**wrapper.event)
    bundles = wrapper.bundles

    logger.info(f"Notification hook: session {input_data.session_id}")

    generic_input = mapper.map_notification_input(input_data)

    results = execute_handlers_generic(generic_input, bundles)

    default = NotificationOutput(continue_=True)
    result = mapper.map_to_notification_output(results, default)
    _log_generic_hook_outcome("Notification", input_data, result)
    return result


@router.post("/PreCompact", response_model=PreCompactOutput, response_model_exclude_none=True)
async def pre_compact_hook(wrapper: RequestWrapper) -> PreCompactOutput:
    """Handle PreCompact hook events."""
    input_data = PreCompactInput(**wrapper.event)
    bundles = wrapper.bundles

    logger.info(f"PreCompact hook: session {input_data.session_id}")

    generic_input = mapper.map_pre_compact_input(input_data)

    results = execute_handlers_generic(generic_input, bundles)

    default = PreCompactOutput(continue_=True)
    result = mapper.map_to_pre_compact_output(results, default)
    _log_generic_hook_outcome("PreCompact", input_data, result)
    return result


@router.post("/SessionStart", response_model=SessionStartOutput, response_model_exclude_none=True)
async def session_start_hook(wrapper: RequestWrapper) -> SessionStartOutput:
    """Handle SessionStart hook events."""
    input_data = SessionStartInput(**wrapper.event)
    bundles = wrapper.bundles

    logger.info(f"SessionStart hook: session {input_data.session_id}")

    generic_input = mapper.map_session_start_input(input_data)

    results = execute_handlers_generic(generic_input, bundles)

    default = SessionStartOutput(
        continue_=True,
        hookSpecificOutput=SessionStartHookSpecificOutput()
    )
    result = mapper.map_to_session_start_output(results, default)
    _log_generic_hook_outcome("SessionStart", input_data, result)
    return result


@router.post("/SessionEnd", response_model=SessionEndOutput, response_model_exclude_none=True)
async def session_end_hook(wrapper: RequestWrapper) -> SessionEndOutput:
    """Handle SessionEnd hook events."""
    input_data = SessionEndInput(**wrapper.event)
    bundles = wrapper.bundles

    logger.info(f"SessionEnd hook: session {input_data.session_id}")

    generic_input = mapper.map_session_end_input(input_data)

    results = execute_handlers_generic(generic_input, bundles)

    default = SessionEndOutput(continue_=True)
    result = mapper.map_to_session_end_output(results, default)
    _log_generic_hook_outcome("SessionEnd", input_data, result)
    return result
