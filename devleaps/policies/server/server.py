import logging

from fastapi import FastAPI

from .claude_code import router as claude_code_router
from .cursor import router as cursor_router
from .registry import registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DevLeaps Policy Server", version="1.0.0")
app.include_router(claude_code_router)
app.include_router(cursor_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Agent Policy Server by DevLeaps",
        "version": "1.0.0",
        "editors": ["claude-code", "cursor"],
        "endpoints": {
            "claude-code": [
                "/policy/claude-code/PreToolUse",
                "/policy/claude-code/PostToolUse",
                "/policy/claude-code/UserPromptSubmit",
                "/policy/claude-code/Stop",
                "/policy/claude-code/SubagentStop",
                "/policy/claude-code/Notification",
                "/policy/claude-code/PreCompact",
                "/policy/claude-code/SessionStart",
                "/policy/claude-code/SessionEnd",
            ],
            "cursor": [
                "/policy/cursor/beforeShellExecution",
                "/policy/cursor/beforeMCPExecution",
                "/policy/cursor/afterFileEdit",
                "/policy/cursor/beforeReadFile",
                "/policy/cursor/beforeSubmitPrompt",
                "/policy/cursor/stop",
            ]
        }
    }


def get_registry():
    """Get the global hook registry for registering handlers."""
    return registry