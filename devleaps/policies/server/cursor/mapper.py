"""
Mappers to convert Cursor hook inputs/outputs to/from generic models.
"""
from typing import List, Union

from ..common.enums import SourceClient
from ..common.models import (
    POLICY_PRECEDENCE,
    HookEvent,
    PolicyAction,
    PolicyDecision,
    PolicyGuidance,
    PromptSubmitEvent,
    StopEvent,
    ToolUseEvent,
)
from .api.after_file_edit import AfterFileEditInput, AfterFileEditOutput
from .api.before_mcp_execution import BeforeMCPExecutionInput, BeforeMCPExecutionOutput
from .api.before_read_file import BeforeReadFileInput, BeforeReadFileOutput
from .api.before_shell_execution import (
    BeforeShellExecutionInput,
    BeforeShellExecutionOutput,
)
from .api.before_submit_prompt import BeforeSubmitPromptInput, BeforeSubmitPromptOutput
from .api.common import Permission
from .api.stop import StopInput, StopOutput

# ============================================================================
# INPUT MAPPERS: Cursor → Generic
# ============================================================================

def map_before_shell_execution_input(input_data: BeforeShellExecutionInput) -> ToolUseEvent:
    """Map beforeShellExecution to ToolUseEvent"""
    return ToolUseEvent(
        session_id=input_data.conversation_id,
        tool_name="Bash",
        source_client=SourceClient.CURSOR,
        tool_is_bash=True,
        tool_is_mcp=False,
        command=input_data.command,
        workspace_roots=input_data.workspace_roots,
        source_event=input_data
    )


def map_before_mcp_execution_input(input_data: BeforeMCPExecutionInput) -> ToolUseEvent:
    """Map beforeMCPExecution to ToolUseEvent"""
    tool_name_str = input_data.tool_name

    return ToolUseEvent(
        session_id=input_data.conversation_id,
        tool_name=tool_name_str,
        source_client=SourceClient.CURSOR,
        tool_is_bash=False,
        tool_is_mcp=tool_name_str.startswith("mcp__") or True,  # Assume MCP tools
        command=input_data.command,
        parameters=input_data.tool_input,
        workspace_roots=input_data.workspace_roots,
        source_event=input_data
    )


def map_after_file_edit_input(input_data: AfterFileEditInput) -> HookEvent:
    """Map afterFileEdit to HookEvent (post-edit observation only)"""
    return HookEvent(
        session_id=input_data.conversation_id,
        source_client=SourceClient.CURSOR,
        hook_type="after_file_edit",
        workspace_roots=input_data.workspace_roots,
        source_event=input_data
    )


def map_before_read_file_input(input_data: BeforeReadFileInput) -> HookEvent:
    """Map beforeReadFile to HookEvent"""
    return HookEvent(
        session_id=input_data.conversation_id,
        source_client=SourceClient.CURSOR,
        hook_type="before_read_file",
        workspace_roots=input_data.workspace_roots,
        source_event=input_data
    )


def map_before_submit_prompt_input(input_data: BeforeSubmitPromptInput) -> PromptSubmitEvent:
    """Map beforeSubmitPrompt to PromptSubmitEvent"""
    return PromptSubmitEvent(
        session_id=input_data.conversation_id,
        source_client=SourceClient.CURSOR,
        prompt=input_data.prompt,
        workspace_roots=input_data.workspace_roots,
        source_event=input_data
    )


def map_stop_input(input_data: StopInput) -> StopEvent:
    """Map stop to StopEvent"""
    return StopEvent(
        session_id=input_data.conversation_id,
        source_client=SourceClient.CURSOR,
        stop_type="stop",
        workspace_roots=input_data.workspace_roots,
        source_event=input_data
    )


# ============================================================================
# OUTPUT MAPPERS: Generic → Cursor
# ============================================================================

def map_to_cursor_output(
    results: List[Union[PolicyDecision, PolicyGuidance]],
    default_output
) -> Union[BeforeShellExecutionOutput, BeforeMCPExecutionOutput, BeforeReadFileOutput, BeforeSubmitPromptOutput, StopOutput, AfterFileEditOutput]:
    """Map generic results to Cursor output"""
    decisions = [r for r in results if isinstance(r, PolicyDecision)]
    guidances = [r for r in results if isinstance(r, PolicyGuidance)]

    if not decisions and not guidances:
        return default_output

    final_decision = None
    for action in POLICY_PRECEDENCE:
        matching = [d for d in decisions if d.action == action]
        if matching:
            final_decision = matching[0]
            break

    permission_map = {
        PolicyAction.ALLOW: Permission.ALLOW,
        PolicyAction.DENY: Permission.DENY,
        PolicyAction.ASK: Permission.ASK,
        PolicyAction.HALT: Permission.DENY,
    }

    user_messages = []
    agent_messages = []

    if final_decision:
        reasons = [d.reason for d in decisions if d.action == final_decision.action and d.reason]
        user_messages.extend(reasons)

    for guidance in guidances:
        # Guidance is always shown to both user and agent
        user_messages.append(guidance.content)
        agent_messages.append(guidance.content)

    output_type = type(default_output)
    return output_type(
        permission=permission_map.get(final_decision.action) if final_decision else None,
        userMessage="\n".join(user_messages) if user_messages else None,
        agentMessage="\n".join(agent_messages) if agent_messages else None
    )
