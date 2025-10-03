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


@pytest.fixture(scope="session", autouse=True)
def setup_example_policies():
    """Setup example policies before running tests."""
    from devleaps.policies.example.main import (
        bash_split_middleware,
        terraform_rule,
        python_test_file_rule,
    )

    registry = get_registry()
    registry.register_middleware(ToolUseEvent, bash_split_middleware)
    registry.register_handler(ToolUseEvent, terraform_rule)
    registry.register_handler(ToolUseEvent, python_test_file_rule)


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

    def test_terraform_fmt_allowed(self):
        """Test terraform fmt is allowed in Cursor."""
        check_cursor_policy("terraform fmt", PolicyAction.ALLOW)


class TestCursorBlockedCommands:
    """Test commands that should be blocked in Cursor."""

    def test_terraform_apply_denied(self):
        """Test terraform apply is denied in Cursor."""
        check_cursor_policy("terraform apply", PolicyAction.DENY)

    def test_terraform_apply_with_auto_approve_denied(self):
        """Test terraform apply with flags is denied in Cursor."""
        check_cursor_policy("terraform apply -auto-approve", PolicyAction.DENY)


class TestCursorCommandChaining:
    """Test command chaining with && in Cursor."""

    def test_chained_safe_commands(self):
        """Test chained commands that are all safe."""
        check_cursor_policy("terraform plan && terraform fmt", PolicyAction.ALLOW)

    def test_chained_with_unsafe_command(self):
        """Test chained commands with one unsafe command."""
        check_cursor_policy("terraform plan && terraform apply", PolicyAction.DENY)
        check_cursor_policy("terraform apply && terraform plan", PolicyAction.DENY)


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
        """Test commands with various whitespace."""
        check_cursor_policy("  terraform apply  ", PolicyAction.DENY)
        check_cursor_policy("\tterraform plan\t", PolicyAction.ALLOW)

    def test_case_sensitivity(self):
        """Test that commands are case-sensitive."""
        # Lowercase should match
        check_cursor_policy("terraform apply", PolicyAction.DENY)
        # Uppercase should not match our regex
        input_data = create_cursor_shell_event("TERRAFORM APPLY")
        results = list(execute_handlers_generic(input_data))
        deny_results = [r for r in results if isinstance(r, PolicyDecision) and r.action == PolicyAction.DENY]
        # Our regex uses lowercase, so this shouldn't match
        assert len(deny_results) == 0

    def test_partial_command_match(self):
        """Test that partial matches don't trigger policies."""
        # Commands that start with terraform but aren't exact matches
        input_data = create_cursor_shell_event("terraform_backup apply")
        results = list(execute_handlers_generic(input_data))
        deny_results = [r for r in results if isinstance(r, PolicyDecision) and r.action == PolicyAction.DENY]
        # Should not match terraform policy
        assert len(deny_results) == 0


class TestCursorMultipleMiddleware:
    """Test that middleware processes commands correctly for Cursor."""

    def test_middleware_splits_commands(self):
        """Test that command splitting middleware works for Cursor."""
        # When we have "cmd1 && cmd2", middleware should split and evaluate both
        check_cursor_policy("terraform plan && terraform fmt", PolicyAction.ALLOW)

    def test_middleware_preserves_order(self):
        """Test that first blocking command determines result."""
        # First command blocks
        check_cursor_policy("terraform apply && terraform plan", PolicyAction.DENY)
        # Second command blocks
        check_cursor_policy("terraform plan && terraform apply", PolicyAction.DENY)
