"""
Mappers to convert Claude Code hook inputs/outputs to/from generic models.
"""
from typing import List, TypeVar, Union

from ..common.enums import SourceClient
from ..common.models import (
    POLICY_PRECEDENCE,
    FileEditEvent,
    HookEvent,
    PatchLine,
    PolicyAction,
    PolicyDecision,
    PolicyGuidance,
    PostFileEditEvent,
    PostToolUseEvent,
    PromptSubmitEvent,
    StopEvent,
    StructuredPatch,
    ToolUseEvent,
)
from .api.enums import PermissionDecision, ToolName
from .api.notification import NotificationInput, NotificationOutput
from .api.post_tool_use import PostToolUseInput, PostToolUseOutput, PostToolUseHookSpecificOutput
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
# HELPER FUNCTIONS
# ============================================================================

def _parse_patch_lines(raw_lines: List[str]) -> List[PatchLine]:
    """
    Parse raw patch lines (with +/- prefixes) into PatchLine objects.

    Args:
        raw_lines: List of diff lines (e.g., ["+# comment", " code", "-old_code"])

    Returns:
        List of PatchLine objects with operation and content separated
    """
    parsed_lines = []
    for line in raw_lines:
        if not line:
            parsed_lines.append(PatchLine(operation="unchanged", content=""))
            continue

        # Check first character for operation type
        if line[0] == '+':
            operation = "added"
            content = line[1:]
        elif line[0] == '-':
            operation = "removed"
            content = line[1:]
        else:  # space or anything else
            operation = "unchanged"
            content = line[1:] if len(line) > 0 and line[0] == ' ' else line

        parsed_lines.append(PatchLine(operation=operation, content=content))

    return parsed_lines


# ============================================================================
# INPUT MAPPERS: Claude Code → Generic
# ============================================================================

def map_pre_tool_use_input(input_data: PreToolUseInput) -> Union[ToolUseEvent, FileEditEvent]:
    """Map PreToolUse to appropriate event type"""
    tool_name_str = input_data.tool_name.value if isinstance(input_data.tool_name, ToolName) else str(input_data.tool_name)

    if input_data.tool_name in [ToolName.EDIT, ToolName.WRITE]:
        tool_input = input_data.tool_input or {}
        file_path = tool_input.get('file_path') if isinstance(tool_input, dict) else None

        return FileEditEvent(
            session_id=input_data.session_id,
            source_client=SourceClient.CLAUDE_CODE,
            file_path=file_path,
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


def map_post_tool_use_input(input_data: PostToolUseInput) -> Union[PostFileEditEvent, PostToolUseEvent]:
    """Map PostToolUse to appropriate post-event type"""
    tool_name_str = input_data.tool_name.value if isinstance(input_data.tool_name, ToolName) else str(input_data.tool_name)

    # File edit/write operations map to PostFileEditEvent
    if input_data.tool_name in [ToolName.EDIT, ToolName.WRITE]:
        tool_input = input_data.tool_input or {}
        tool_response = input_data.tool_response or {}

        file_path = tool_input.get('file_path') if isinstance(tool_input, dict) else None
        content = tool_response.get('content') if isinstance(tool_response, dict) else None

        # Convert raw patch dicts to StructuredPatch objects with parsed lines
        raw_patches = tool_response.get('structuredPatch') if isinstance(tool_response, dict) else None
        structured_patch = None
        if raw_patches:
            structured_patch = []
            for patch in raw_patches:
                # Parse the raw lines into PatchLine objects
                raw_lines = patch.get('lines', [])
                parsed_lines = _parse_patch_lines(raw_lines)

                # Create StructuredPatch with parsed lines
                parsed_patch = StructuredPatch(
                    oldStart=patch.get('oldStart', 0),
                    oldLines=patch.get('oldLines', 0),
                    newStart=patch.get('newStart', 0),
                    newLines=patch.get('newLines', 0),
                    lines=parsed_lines
                )
                structured_patch.append(parsed_patch)

        return PostFileEditEvent(
            session_id=input_data.session_id,
            source_client=SourceClient.CLAUDE_CODE,
            file_path=file_path,
            operation=tool_name_str,
            content=content,
            structured_patch=structured_patch,
            workspace_roots=None,
            source_event=input_data
        )

    # All other tools map to PostToolUseEvent
    command = None
    parameters = None

    tool_is_bash = input_data.tool_name == ToolName.BASH
    tool_is_mcp = tool_name_str.startswith("mcp__")

    if tool_is_bash and hasattr(input_data, 'command'):
        command = input_data.command
    else:
        parameters = input_data.model_dump(exclude={'session_id', 'tool_name'})

    return PostToolUseEvent(
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
    guidances = [r for r in results if isinstance(r, PolicyGuidance)]

    if not decisions and not guidances:
        return default_output

    final_decision = _find_highest_priority_decision(decisions) if decisions else None

    permission_map = {
        PolicyAction.ALLOW: PermissionDecision.ALLOW,
        PolicyAction.DENY: PermissionDecision.DENY,
        PolicyAction.ASK: PermissionDecision.ASK,
        PolicyAction.HALT: PermissionDecision.DENY,
    }

    reasons = [d.reason for d in decisions if d.action == final_decision.action and d.reason] if final_decision else []
    guidance_texts = [g.content for g in guidances]

    all_messages = reasons + guidance_texts
    combined_reason = "\n".join(all_messages) if all_messages else None

    # If we have a decision, use it; otherwise use the default permission from default_output
    permission = permission_map[final_decision.action] if final_decision else default_output.hookSpecificOutput.permissionDecision
    should_continue = (final_decision.action != PolicyAction.HALT) if final_decision else default_output.continue_

    return PreToolUseOutput(
        continue_=should_continue,
        systemMessage=combined_reason,
        hookSpecificOutput=PreToolUseHookSpecificOutput(
            permissionDecision=permission,
            permissionDecisionReason=combined_reason
        )
    )


def map_to_post_tool_use_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output: PostToolUseOutput
) -> PostToolUseOutput:
    """Map generic results to PostToolUseOutput"""
    decisions = [r for r in results if isinstance(r, PolicyDecision)]
    guidances = [r for r in results if isinstance(r, PolicyGuidance)]

    if not decisions and not guidances:
        return default_output

    # Check for HALT
    halt_result = _check_for_halt_and_return(results, default_output, PostToolUseOutput)
    if halt_result:
        return halt_result

    # Collect all messages (reasons + guidance) for additionalContext
    reasons = [d.reason for d in decisions if d.reason]
    guidance_texts = [g.content for g in guidances]

    all_messages = reasons + guidance_texts
    additional_context = "\n".join(all_messages) if all_messages else None

    return PostToolUseOutput(
        continue_=True,
        hookSpecificOutput=PostToolUseHookSpecificOutput(
            additionalContext=additional_context
        )
    ) if additional_context else default_output


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
