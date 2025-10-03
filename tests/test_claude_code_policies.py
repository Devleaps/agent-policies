"""
Claude Code policy tests.

Tests the policy framework with Claude Code hook events,
verifying that policies work correctly for PreToolUse and other hooks.
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


def create_tool_use_event(command: str, tool_name: str = "Bash") -> ToolUseEvent:
    """Create a ToolUseEvent for testing bash commands."""
    return ToolUseEvent(
        session_id="test",
        tool_name=tool_name,
        source_client=SourceClient.CLAUDE_CODE,
        tool_is_bash=(tool_name == "Bash"),
        command=command if tool_name == "Bash" else None,
    )


def check_policy(command: str, expected: PolicyAction) -> None:
    """Test a command against the policy registry."""
    input_data = create_tool_use_event(command)
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


class TestClaudeCodeBasicCommands:
    """Test basic commands that should be allowed."""

    def test_terraform_plan_allowed(self):
        """Test terraform plan is allowed."""
        check_policy("terraform plan", PolicyAction.ALLOW)

    def test_terraform_fmt_allowed(self):
        """Test terraform fmt is allowed."""
        check_policy("terraform fmt", PolicyAction.ALLOW)


class TestClaudeCodeBlockedCommands:
    """Test commands that should be blocked."""

    def test_terraform_apply_denied(self):
        """Test terraform apply is denied."""
        check_policy("terraform apply", PolicyAction.DENY)

    def test_terraform_apply_with_args_denied(self):
        """Test terraform apply with arguments is denied."""
        check_policy("terraform apply -auto-approve", PolicyAction.DENY)


class TestClaudeCodeCommandSplitting:
    """Test bash command splitting middleware."""

    def test_chained_commands_all_allowed(self):
        """Test chained commands where all are allowed."""
        check_policy("terraform plan && terraform fmt", PolicyAction.ALLOW)

    def test_chained_commands_one_denied(self):
        """Test chained commands where one is denied."""
        check_policy("terraform plan && terraform apply", PolicyAction.DENY)
        check_policy("terraform apply && terraform plan", PolicyAction.DENY)


class TestClaudeCodeNonBashTools:
    """Test non-Bash tools don't trigger Bash policies."""

    def test_non_bash_tool_no_policy(self):
        """Test non-Bash tools don't trigger Bash command policies."""
        # Create a non-Bash tool event
        input_data = create_tool_use_event("", tool_name="Read")
        results = list(execute_handlers_generic(input_data))

        # Should return empty or only guidance, no decisions
        decisions = [r for r in results if isinstance(r, PolicyDecision)]
        assert len(decisions) == 0


class TestClaudeCodePolicyReasons:
    """Test that policies provide appropriate reasons."""

    def test_terraform_apply_has_reason(self):
        """Test terraform apply denial includes helpful reason."""
        input_data = create_tool_use_event("terraform apply")
        results = list(execute_handlers_generic(input_data))

        deny_results = [r for r in results if isinstance(r, PolicyDecision) and r.action == PolicyAction.DENY]
        assert len(deny_results) > 0
        assert deny_results[0].reason is not None
        assert "terraform plan" in deny_results[0].reason


class TestClaudeCodeEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_terraform_with_extra_whitespace(self):
        """Test terraform commands with extra whitespace."""
        check_policy("  terraform apply  ", PolicyAction.DENY)
        check_policy("  terraform plan  ", PolicyAction.ALLOW)


    def test_empty_command(self):
        """Test empty command doesn't crash."""
        input_data = create_tool_use_event("")
        results = list(execute_handlers_generic(input_data))
        # Should not crash, just return empty or no blocking decisions
        blocking = [r for r in results if isinstance(r, PolicyDecision) and r.action in [PolicyAction.DENY, PolicyAction.ASK]]
        # Empty commands shouldn't be blocked by our example policies
        assert len(blocking) == 0
