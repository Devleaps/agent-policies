"""
Python test file policy - prevents running test files directly with python.
"""

import re

from devleaps.policies.server.common.models import (
    PolicyAction,
    PolicyDecision,
    PolicyGuidance,
    ToolUseEvent,
)


def python_test_file_rule(input_data: ToolUseEvent):
    """Denies running python directly on test files, provides guidance."""
    if not input_data.tool_is_bash:
        return

    command = input_data.command.strip()

    if re.match(r'python3?\s+.*test_.*\.py', command):
        yield PolicyDecision(
            action=PolicyAction.DENY,
            reason="Running python directly on test files is not allowed.\n"
                   "Use `pytest` to run tests properly."
        )
        yield PolicyGuidance(
            content="Consider using pytest with specific test markers or paths for better test isolation."
        )
