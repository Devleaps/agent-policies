#!/usr/bin/env python3
import uvicorn
from dataclasses import replace

from devleaps.policies.server.common.models import (
    PolicyAction,
    PolicyDecision,
    PolicyGuidance,
    PostToolUseEvent,
    ToolUseEvent,
)
from devleaps.policies.server.server import app, get_registry


def bash_split_middleware(input_data: ToolUseEvent):
    """Split compound bash commands on && for independent evaluation."""
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
    """Example policy: Block terraform apply, allow terraform plan."""
    if not input_data.tool_is_bash:
        return

    command = input_data.command.strip()

    if command == "terraform apply":
        yield PolicyDecision(
            action=PolicyAction.DENY,
            reason="terraform apply is not allowed. Use `terraform plan` instead."
        )

    if command == "terraform plan":
        yield PolicyDecision(action=PolicyAction.ALLOW)


def pip_rule(input_data: ToolUseEvent):
    """Example policy: Block pip install."""
    if not input_data.tool_is_bash:
        return

    command = input_data.command.strip()

    if command == "pip install":
        yield PolicyDecision(
            action=PolicyAction.DENY,
            reason="pip install is not allowed."
        )


if __name__ == "__main__":
    registry = get_registry()
    registry.register_middleware(ToolUseEvent, bash_split_middleware)
    registry.register_handler(ToolUseEvent, terraform_rule)
    registry.register_handler(ToolUseEvent, pip_rule)
    uvicorn.run(app, host="0.0.0.0", port=8338, log_level="info")
