#!/usr/bin/env python3
import json
import sys
from typing import Any, Dict, List

import requests

from devleaps.policies.client.config import ConfigManager


def forward_hook(editor: str, bundles: List[str], payload: Dict[str, Any]) -> int:
    config = ConfigManager.load_config()
    server_url = ConfigManager.get_server_url(config)
    default_behavior = ConfigManager.get_default_policy_behavior(config)
    hook_event_name = payload.get("hook_event_name")

    if not hook_event_name:
        print("Missing hook_event_name in payload", file=sys.stderr)
        return 2

    wrapped_payload = {
        "bundles": bundles,
        "default_policy_behavior": default_behavior,
        "event": payload
    }

    endpoint = f"/policy/{editor}/{hook_event_name}"

    try:
        response = requests.post(
            f"{server_url}{endpoint}",
            json=wrapped_payload
        )

        if response.status_code != 200:
            print(f"Policy server error: HTTP {response.status_code}", file=sys.stderr)
            print(f"Endpoint: {endpoint}", file=sys.stderr)
            return 2

        result = response.json()
        print(json.dumps(result))
        return 0

    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to policy server at {server_url}", file=sys.stderr)
        print("", file=sys.stderr)
        print("To start the server, run: devleaps-policy-server", file=sys.stderr)
        print(f"Or configure server_url in ~/.agent-policies/config.json", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: Unexpected failure communicating with policy server", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print(f"Server: {server_url}", file=sys.stderr)
        return 2


def main():
    config = ConfigManager.load_config()
    editor = ConfigManager.get_editor(config)
    bundles = ConfigManager.get_enabled_bundles(config)

    try:
        hook_json = sys.stdin.read().strip()
        payload = json.loads(hook_json)
        exit_code = forward_hook(editor, bundles, payload)
        sys.exit(exit_code)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in hook payload: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()