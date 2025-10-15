#!/usr/bin/env python3
import re
from dataclasses import replace

from devleaps.policies.server.common.models import (
    PolicyAction,
    PolicyDecision,
    PolicyGuidance,
    ToolUseEvent,
)
from devleaps.policies.server.server import app, get_registry


def bash_split_middleware(input_data: ToolUseEvent):
    if not input_data.tool_is_bash or not input_data.command:
        yield input_data
        return

    if ' && ' in input_data.command:
        for cmd in input_data.command.split(' && '):
            if cmd.strip():
                yield replace(input_data, command=cmd.strip())
    else:
        yield input_data

def terraform_rule(input_data: ToolUseEvent):
    if not input_data.tool_is_bash:
        return

    command = input_data.command.strip()

    if re.match(r'^terraform\s+apply(?:\s|$)', command):
        yield PolicyDecision(action=PolicyAction.DENY, reason="terraform apply is not allowed. Use `terraform plan` instead.")

    if re.match(r'^terraform\s+(fmt|plan)(?:\s|$)', command):
        yield PolicyDecision(action=PolicyAction.ALLOW)


def python_test_file_rule(input_data: ToolUseEvent):
    if not input_data.tool_is_bash:
        return

    if re.match(r'python3?\s+.*test_.*\.py', input_data.command.strip()):
        yield PolicyDecision(action=PolicyAction.DENY, reason="Use `pytest` to run tests instead of python directly.")
        yield PolicyGuidance(content="Consider using pytest with specific test markers or paths.")


def uv_bundle_rule(input_data: ToolUseEvent):
    if not input_data.tool_is_bash:
        return

    command = input_data.command.strip()

    # Block pip commands, suggest uv
    if re.match(r'^pip(?:\s|$)', command):
        yield PolicyDecision(action=PolicyAction.DENY, reason="Use `uv` instead of pip for package management.")
        yield PolicyGuidance(content="Replace `pip install` with `uv pip install` or `uv add` for dependency management.")
        return

    # Block python -m pip, suggest uv
    if re.match(r'^python3?\s+-m\s+pip(?:\s|$)', command):
        yield PolicyDecision(action=PolicyAction.DENY, reason="Use `uv` instead of python -m pip.")
        return

    # Block direct python usage for scripts, suggest uv run
    if re.match(r'^python3?\s+[^-]', command) and not re.match(r'^python3?\s+.*test', command):
        yield PolicyDecision(action=PolicyAction.DENY, reason="Use `uv run python` to execute scripts.")
        return


if __name__ == "__main__":
    import uvicorn
    registry = get_registry()
    registry.register_middleware(ToolUseEvent, bash_split_middleware)
    registry.register_handler(ToolUseEvent, terraform_rule)
    registry.register_handler(ToolUseEvent, python_test_file_rule)
    # Register the uv bundle rule
    registry.register_handler(ToolUseEvent, uv_bundle_rule, bundle="uv")
    uvicorn.run(app, host="0.0.0.0", port=8338, log_level="info")
