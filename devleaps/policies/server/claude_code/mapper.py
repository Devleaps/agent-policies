"""
Mappers to convert Claude Code hook inputs/outputs to/from generic models.
"""
from typing import List, TypeVar, Union

from ..common.enums import SourceClient
from ..common.models import (
    POLICY_PRECEDENCE,
    FileEditEvent,
    HookEvent,
    PolicyAction,
    PolicyDecision,
    PolicyGuidance,
    PromptSubmitEvent,
    StopEvent,
    ToolUseEvent,
)
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

# ============================================================================
# INPUT MAPPERS: Claude Code → Generic
# ============================================================================

def map_pre_tool_use_input(input_data: PreToolUseInput) -> Union[ToolUseEvent, FileEditEvent]:
    """Map PreToolUse to appropriate event type"""
    tool_name_str = input_data.tool_name.value if isinstance(input_data.tool_name, ToolName) else str(input_data.tool_name)

    if input_data.tool_name in [ToolName.EDIT, ToolName.WRITE]:
        return FileEditEvent(
            session_id=input_data.session_id,
            source_client=SourceClient.CLAUDE_CODE,
            file_path=getattr(input_data, 'file_path', None),
            operation=tool_name_str,
            workspace_roots=None,
            source_event=input_data
        )

    command = None
    parameters = None

    tool_is_bash = input_data.tool_name == ToolName.BASH
    tool_is_mcp = tool_name_str.startswith("mcp__")

    if tool_is_bash and hasattr(input_data, 'command'):
        command = input_data.command
    else:
        parameters = input_data.model_dump(exclude={'session_id', 'tool_name'})

    return ToolUseEvent(
        session_id=input_data.session_id,
        tool_name=tool_name_str,
        source_client=SourceClient.CLAUDE_CODE,
        command=command,
        parameters=parameters,
        workspace_roots=None,
        source_event=input_data,
        tool_is_bash=tool_is_bash,
        tool_is_mcp=tool_is_mcp
    )


def map_post_tool_use_input(input_data: PostToolUseInput) -> HookEvent:
    """Map PostToolUse to HookEvent (generic post-execution hook)"""
    return HookEvent(
        session_id=input_data.session_id,
        source_client=SourceClient.CLAUDE_CODE,
        hook_type="post_tool_use",
        workspace_roots=None,
        source_event=input_data
    )


def map_user_prompt_submit_input(input_data: UserPromptSubmitInput) -> PromptSubmitEvent:
    """Map UserPromptSubmit to PromptSubmitEvent"""
    return PromptSubmitEvent(
        session_id=input_data.session_id,
        source_client=SourceClient.CLAUDE_CODE,
        prompt=getattr(input_data, 'prompt', None),
        workspace_roots=None,
        source_event=input_data
    )


def map_stop_input(input_data: StopInput) -> StopEvent:
    """Map Stop to StopEvent"""
    return StopEvent(
        session_id=input_data.session_id,
        source_client=SourceClient.CLAUDE_CODE,
        stop_type="stop",
        workspace_roots=None,
        source_event=input_data
    )


def map_subagent_stop_input(input_data: SubagentStopInput) -> StopEvent:
    """Map SubagentStop to StopEvent"""
    return StopEvent(
        session_id=input_data.session_id,
        source_client=SourceClient.CLAUDE_CODE,
        stop_type="subagent_stop",
        workspace_roots=None,
        source_event=input_data
    )


def map_notification_input(input_data: NotificationInput) -> HookEvent:
    """Map Notification to HookEvent"""
    return HookEvent(
        session_id=input_data.session_id,
        source_client=SourceClient.CLAUDE_CODE,
        hook_type="notification",
        workspace_roots=None,
        source_event=input_data
    )


def map_pre_compact_input(input_data: PreCompactInput) -> HookEvent:
    """Map PreCompact to HookEvent"""
    return HookEvent(
        session_id=input_data.session_id,
        source_client=SourceClient.CLAUDE_CODE,
        hook_type="pre_compact",
        workspace_roots=None,
        source_event=input_data
    )


def map_session_start_input(input_data: SessionStartInput) -> HookEvent:
    """Map SessionStart to HookEvent"""
    return HookEvent(
        session_id=input_data.session_id,
        source_client=SourceClient.CLAUDE_CODE,
        hook_type="session_start",
        workspace_roots=None,
        source_event=input_data
    )


def map_session_end_input(input_data: SessionEndInput) -> HookEvent:
    """Map SessionEnd to HookEvent"""
    return HookEvent(
        session_id=input_data.session_id,
        source_client=SourceClient.CLAUDE_CODE,
        hook_type="session_end",
        workspace_roots=None,
        source_event=input_data
    )


# ============================================================================
# OUTPUT MAPPERS: Generic → Claude Code
# ============================================================================

OutputType = TypeVar('OutputType')


def _find_highest_priority_decision(
    decisions: List[PolicyDecision]
) -> PolicyDecision | None:
    """Find the highest priority decision based on POLICY_PRECEDENCE."""
    for action in POLICY_PRECEDENCE:
        matching = [d for d in decisions if d.action == action]
        if matching:
            return matching[0]
    return None


def _check_for_halt_and_return(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: OutputType,
    output_class: type
) -> OutputType | None:
    """
    Check if any decision is HALT and return appropriate output.
    Returns None if no HALT found, allowing caller to continue processing.
    """
    decisions = [r for r in results if isinstance(r, PolicyDecision)]
    for decision in decisions:
        if decision.action == PolicyAction.HALT:
            return output_class(continue_=False)
    return None


def map_to_pre_tool_use_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: PreToolUseOutput
) -> PreToolUseOutput:
    """Map generic results to PreToolUseOutput"""
    decisions = [r for r in results if isinstance(r, PolicyDecision)]

    if not decisions:
        return default_output

    final_decision = _find_highest_priority_decision(decisions)

    if not final_decision:
        return default_output

    permission_map = {
        PolicyAction.ALLOW: PermissionDecision.ALLOW,
        PolicyAction.DENY: PermissionDecision.DENY,
        PolicyAction.ASK: PermissionDecision.ASK,
        PolicyAction.HALT: PermissionDecision.DENY,
    }

    reasons = [d.reason for d in decisions if d.action == final_decision.action and d.reason]
    combined_reason = "\n".join(reasons) if reasons else None

    return PreToolUseOutput(
        continue_=(final_decision.action != PolicyAction.HALT),
        hookSpecificOutput=PreToolUseHookSpecificOutput(
            permissionDecision=permission_map[final_decision.action],
            permissionDecisionReason=combined_reason
        )
    )


def map_to_post_tool_use_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: PostToolUseOutput
) -> PostToolUseOutput:
    """Map generic results to PostToolUseOutput"""
    halt_result = _check_for_halt_and_return(results, default_output, PostToolUseOutput)
    return halt_result if halt_result else default_output


def map_to_user_prompt_submit_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: UserPromptSubmitOutput
) -> UserPromptSubmitOutput:
    """Map generic results to UserPromptSubmitOutput"""
    halt_result = _check_for_halt_and_return(results, default_output, UserPromptSubmitOutput)
    return halt_result if halt_result else default_output


def map_to_stop_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: StopOutput
) -> StopOutput:
    """Map generic results to StopOutput"""
    halt_result = _check_for_halt_and_return(results, default_output, StopOutput)
    return halt_result if halt_result else default_output


def map_to_subagent_stop_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: SubagentStopOutput
) -> SubagentStopOutput:
    """Map generic results to SubagentStopOutput"""
    halt_result = _check_for_halt_and_return(results, default_output, SubagentStopOutput)
    return halt_result if halt_result else default_output


def map_to_notification_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: NotificationOutput
) -> NotificationOutput:
    """Map generic results to NotificationOutput"""
    halt_result = _check_for_halt_and_return(results, default_output, NotificationOutput)
    return halt_result if halt_result else default_output


def map_to_pre_compact_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: PreCompactOutput
) -> PreCompactOutput:
    """Map generic results to PreCompactOutput"""
    halt_result = _check_for_halt_and_return(results, default_output, PreCompactOutput)
    return halt_result if halt_result else default_output


def map_to_session_start_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: SessionStartOutput
) -> SessionStartOutput:
    """Map generic results to SessionStartOutput"""
    halt_result = _check_for_halt_and_return(results, default_output, SessionStartOutput)
    if halt_result:
        return halt_result

    guidances = [r for r in results if isinstance(r, PolicyGuidance)]
    if guidances:
        instructions = "\n".join([g.content for g in guidances])
        return SessionStartOutput(
            continue_=True,
            hookSpecificOutput=SessionStartHookSpecificOutput(
                sessionInstructions=instructions
            )
        )

    return default_output


def map_to_session_end_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: SessionEndOutput
) -> SessionEndOutput:
    """Map generic results to SessionEndOutput"""
    halt_result = _check_for_halt_and_return(results, default_output, SessionEndOutput)
    return halt_result if halt_result else default_output
