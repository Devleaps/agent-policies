"""
Terraform policy rule - blocks destructive operations.
"""

import re

from devleaps.policies.server.common.models import (
    PolicyAction,
    PolicyDecision,
    ToolUseEvent,
)


def terraform_rule(input_data: ToolUseEvent):
    """Blocks terraform apply, allows safe commands like plan and fmt."""
    if not input_data.tool_is_bash:
        return

    command = input_data.command.strip()

    if re.match(r'^terraform\s+apply(?:\s|$)', command):
        yield PolicyDecision(
            action=PolicyAction.DENY,
            reason="terraform apply is not allowed.\n"
                   "Use `terraform plan` to review changes without applying them."
        )

    if re.match(r'^terraform\s+(fmt|plan)(?:\s|$)', command):
        yield PolicyDecision(action=PolicyAction.ALLOW)
