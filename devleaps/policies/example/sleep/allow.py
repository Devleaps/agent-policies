"""
Sleep policy rule - allows sleep commands up to 60 seconds.
"""

import re

from devleaps.policies.server.common.models import (
    PolicyAction,
    PolicyDecision,
    ToolUseEvent,
)


def sleep_duration_rule(input_data: ToolUseEvent):
    """Allows sleep commands with duration <= 60 seconds."""
    if not input_data.tool_is_bash:
        return

    command = input_data.command.strip()
    sleep_match = re.match(r'^sleep\s+(\d+(?:\.\d+)?)', command)

    if not sleep_match:
        return

    duration = float(sleep_match.group(1))

    if duration > 60:
        yield PolicyDecision(
            action=PolicyAction.DENY,
            reason="Sleep durations above 60 seconds are not allowed.\n"
                   "Use a duration of 60 seconds or less."
        )
    else:
        yield PolicyDecision(action=PolicyAction.ALLOW)
