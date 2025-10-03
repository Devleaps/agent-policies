"""
Bash command splitting middleware.

Splits commands on '&&' to allow each command to be evaluated independently.
"""

from dataclasses import replace

from devleaps.policies.server.common.models import ToolUseEvent


def split_commands_middleware(input_data: ToolUseEvent):
    """Split commands on '&&' and yield each command separately."""
    if not input_data.tool_is_bash:
        yield input_data
        return

    command = input_data.command
    if not command:
        yield input_data
        return

    if ' && ' in command:
        commands = [cmd.strip() for cmd in command.split(' && ') if cmd.strip()]
        for cmd in commands:
            yield replace(input_data, command=cmd)
    else:
        yield input_data
