#!/usr/bin/env python3
import json
import os
import sys
from typing import Any, Dict

import requests

DEFAULT_SERVER_URL = "http://localhost:8338"
TIMEOUT_SECONDS = 30


def get_server_url() -> str:
    return os.environ.get("HOOK_SERVER_URL", DEFAULT_SERVER_URL)


def forward_hook(editor: str, payload: Dict[str, Any]) -> int:
    server_url = get_server_url()
    hook_event_name = payload.get("hook_event_name")

    if not hook_event_name:
        print("Missing hook_event_name in payload", file=sys.stderr)
        return 2

    # Direct path mapping: /policy/{editor}/{hook_event_name}
    endpoint = f"/policy/{editor}/{hook_event_name}"

    try:
        response = requests.post(
            f"{server_url}{endpoint}",
            json=payload,
            timeout=TIMEOUT_SECONDS
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
        print(f"Or set HOOK_SERVER_URL environment variable to point to your server", file=sys.stderr)
        return 2
    except requests.exceptions.Timeout:
        print(f"Error: Policy server timeout after {TIMEOUT_SECONDS} seconds", file=sys.stderr)
        print(f"Server: {server_url}", file=sys.stderr)
        print("", file=sys.stderr)
        print("The server may be overloaded or the policy evaluation is taking too long.", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: Unexpected failure communicating with policy server", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print(f"Server: {server_url}", file=sys.stderr)
        return 2


def main():
    if len(sys.argv) < 2:
        print("Usage: client.py <editor> (e.g., claude-code or cursor)", file=sys.stderr)
        sys.exit(2)

    editor = sys.argv[1]

    try:
        hook_json = sys.stdin.read().strip()
        payload = json.loads(hook_json)
        exit_code = forward_hook(editor, payload)
        sys.exit(exit_code)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in hook payload: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()