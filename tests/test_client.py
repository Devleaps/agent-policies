"""Tests for the policy client."""

import json
from unittest import mock

from devleaps.policies.client.client import forward_hook
from devleaps.policies.client.config import ConfigManager


def test_forward_hook_successful_response(capsys):
    """forward_hook returns 0 on success and prints response."""
    payload = {"hook_event_name": "PreToolUse", "tool_name": "bash"}
    expected_response = {"continue_": True}

    with mock.patch("devleaps.policies.client.client.requests.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        result = forward_hook("claude-code", ["python-quality"], payload)

        assert result == 0
        captured = capsys.readouterr()
        assert json.dumps(expected_response) in captured.out


def test_forward_hook_sends_correct_payload():
    """forward_hook sends bundles and event in payload."""
    payload = {"hook_event_name": "PreToolUse", "tool_name": "bash"}
    bundles = ["python-quality", "git-workflow"]

    with mock.patch("devleaps.policies.client.client.requests.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"continue_": True}
        mock_post.return_value = mock_response

        forward_hook("claude-code", bundles, payload)

        call_args = mock_post.call_args
        sent_payload = call_args[1]["json"]
        assert sent_payload["bundles"] == bundles
        assert sent_payload["event"] == payload


def test_forward_hook_posts_to_correct_endpoint():
    """forward_hook posts to correct editor and event endpoint."""
    payload = {"hook_event_name": "PreToolUse", "tool_name": "bash"}

    with mock.patch("devleaps.policies.client.client.requests.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"continue_": True}
        mock_post.return_value = mock_response

        forward_hook("claude-code", [], payload)

        call_args = mock_post.call_args
        url = call_args[0][0]
        assert "/policy/claude-code/PreToolUse" in url


def test_forward_hook_multiple_bundles(capsys):
    """forward_hook works with multiple enabled bundles."""
    payload = {"hook_event_name": "PreToolUse", "tool_name": "bash"}
    bundles = ["python-quality", "git-workflow"]

    with mock.patch("devleaps.policies.client.client.requests.post") as mock_post:
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"continue_": True, "reason": "allowed"}
        mock_post.return_value = mock_response

        result = forward_hook("claude-code", bundles, payload)

        assert result == 0
        call_args = mock_post.call_args
        sent_payload = call_args[1]["json"]
        assert len(sent_payload["bundles"]) == 2
