"""
Cursor policy tests.

Tests the policy framework with Cursor hook events,
verifying that policies work correctly for beforeShellExecution and other hooks.
"""

import pytest

from devleaps.policies.server.common.enums import SourceClient
from devleaps.policies.server.common.models import (
    PolicyAction,
    PolicyDecision,
    ToolUseEvent,
)
from devleaps.policies.server.executor import execute_handlers_generic
from devleaps.policies.server.server import get_registry


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


@pytest.fixture(scope="session", autouse=True)
def setup_example_policies():
    """Setup example policies before running tests."""
    registry = get_registry()
    registry.register_handler(ToolUseEvent, terraform_rule)
    registry.register_handler(ToolUseEvent, pip_rule)


def create_cursor_shell_event(command: str) -> ToolUseEvent:
    """Create a ToolUseEvent for Cursor shell execution."""
    return ToolUseEvent(
        session_id="cursor-conversation-123",
        tool_name="Bash",
        source_client=SourceClient.CURSOR,
        tool_is_bash=True,
        command=command,
    )


def check_cursor_policy(command: str, expected: PolicyAction) -> None:
    """Test a Cursor shell command against the policy registry."""
    input_data = create_cursor_shell_event(command)
    results = execute_handlers_generic(input_data)

    # Convert generator to list
    result_list = list(results)

    # Determine actual action based on results
    actual = None
    for result in result_list:
        if isinstance(result, PolicyDecision):
            actual = result.action
            # First blocking result wins
            if actual in [PolicyAction.DENY, PolicyAction.ASK]:
                break

    assert actual == expected, f"Command '{command}' returned {actual}, expected {expected}"


class TestCursorBasicCommands:
    """Test basic shell commands in Cursor."""

    def test_terraform_plan_allowed(self):
        """Test terraform plan is allowed in Cursor."""
        check_cursor_policy("terraform plan", PolicyAction.ALLOW)


class TestCursorBlockedCommands:
    """Test commands that should be blocked in Cursor."""

    def test_terraform_apply_denied(self):
        """Test terraform apply is denied in Cursor."""
        check_cursor_policy("terraform apply", PolicyAction.DENY)

    def test_pip_install_denied(self):
        """Test pip install is denied in Cursor."""
        check_cursor_policy("pip install", PolicyAction.DENY)


class TestCursorPolicyReasons:
    """Test that Cursor policies provide appropriate reasons."""

    def test_terraform_apply_has_helpful_reason(self):
        """Test terraform apply denial includes alternative suggestion."""
        input_data = create_cursor_shell_event("terraform apply")
        results = list(execute_handlers_generic(input_data))

        deny_results = [r for r in results if isinstance(r, PolicyDecision) and r.action == PolicyAction.DENY]
        assert len(deny_results) > 0
        assert deny_results[0].reason is not None
        # Should suggest using terraform plan instead
        assert "plan" in deny_results[0].reason.lower()



class TestCursorEdgeCases:
    """Test edge cases specific to Cursor integration."""

    def test_whitespace_handling(self):
        """Test commands with various whitespace are normalized."""
        check_cursor_policy("  terraform apply  ", PolicyAction.DENY)
        check_cursor_policy("\tterraform plan\t", PolicyAction.ALLOW)
