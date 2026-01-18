#!/usr/bin/env python3
import uvicorn

from devleaps.policies.server.common.models import (
    PolicyAction,
    PolicyDecision,
    ToolUseEvent,
)
from devleaps.policies.server.server import app, get_registry


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
    registry.register_handler(ToolUseEvent, terraform_rule)
    registry.register_handler(ToolUseEvent, pip_rule)
    uvicorn.run(app, host="0.0.0.0", port=8338, log_level="info")
