"""
Cursor hook routes.
"""
import logging

from fastapi import APIRouter

from ..executor import execute_handlers_generic
from . import mapper
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy/cursor")




@router.post("/beforeShellExecution", response_model=BeforeShellExecutionOutput, response_model_exclude_none=True)
async def before_shell_execution_hook(input_data: BeforeShellExecutionInput) -> BeforeShellExecutionOutput:
    """Handle beforeShellExecution hook events."""
    logger.info(f"beforeShellExecution hook: '{input_data.command}' in conversation {input_data.conversation_id}")

    generic_input = mapper.map_before_shell_execution_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = BeforeShellExecutionOutput(permission=Permission.ASK)
    result = mapper.map_to_cursor_output(results, default)

    logger.info(f"beforeShellExecution result: {result.permission}")
    return result


@router.post("/beforeMCPExecution", response_model=BeforeMCPExecutionOutput, response_model_exclude_none=True)
async def before_mcp_execution_hook(input_data: BeforeMCPExecutionInput) -> BeforeMCPExecutionOutput:
    """Handle beforeMCPExecution hook events."""
    logger.info(f"beforeMCPExecution hook: {input_data.tool_name} in conversation {input_data.conversation_id}")

    generic_input = mapper.map_before_mcp_execution_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = BeforeMCPExecutionOutput(permission=Permission.ASK)
    result = mapper.map_to_cursor_output(results, default)

    logger.info(f"beforeMCPExecution result: {result.permission}")
    return result


@router.post("/afterFileEdit", response_model=AfterFileEditOutput, response_model_exclude_none=True)
async def after_file_edit_hook(input_data: AfterFileEditInput) -> AfterFileEditOutput:
    """Handle afterFileEdit hook events (observation only, cannot prevent)."""
    logger.info(f"afterFileEdit hook: {input_data.file_path} in conversation {input_data.conversation_id}")

    generic_input = mapper.map_after_file_edit_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = AfterFileEditOutput()
    result = mapper.map_to_cursor_output(results, default)

    return result


@router.post("/beforeReadFile", response_model=BeforeReadFileOutput, response_model_exclude_none=True)
async def before_read_file_hook(input_data: BeforeReadFileInput) -> BeforeReadFileOutput:
    """Handle beforeReadFile hook events."""
    logger.info(f"beforeReadFile hook: {input_data.file_path} in conversation {input_data.conversation_id}")

    generic_input = mapper.map_before_read_file_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = BeforeReadFileOutput(permission=Permission.ALLOW)
    result = mapper.map_to_cursor_output(results, default)

    logger.info(f"beforeReadFile result: {result.permission}")
    return result


@router.post("/beforeSubmitPrompt", response_model=BeforeSubmitPromptOutput, response_model_exclude_none=True)
async def before_submit_prompt_hook(input_data: BeforeSubmitPromptInput) -> BeforeSubmitPromptOutput:
    """Handle beforeSubmitPrompt hook events."""
    logger.info(f"beforeSubmitPrompt hook in conversation {input_data.conversation_id}")

    generic_input = mapper.map_before_submit_prompt_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = BeforeSubmitPromptOutput(permission=Permission.ALLOW)
    result = mapper.map_to_cursor_output(results, default)

    logger.info(f"beforeSubmitPrompt result: {result.permission}")
    return result


@router.post("/stop", response_model=StopOutput, response_model_exclude_none=True)
async def stop_hook(input_data: StopInput) -> StopOutput:
    """Handle stop hook events."""
    logger.info(f"stop hook in conversation {input_data.conversation_id}")

    generic_input = mapper.map_stop_input(input_data)

    results = execute_handlers_generic(generic_input)

    default = StopOutput()
    result = mapper.map_to_cursor_output(results, default)

    return result
