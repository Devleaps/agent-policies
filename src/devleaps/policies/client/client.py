#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import requests

from devleaps.policies.client.config import ConfigManager

CLAUDE_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
CURSOR_HOOKS_PATH = Path.home() / ".cursor" / "hooks.json"

HOOK_CONFIG = {
    "matcher": "*",
    "type": "command",
    "command": "devleaps-policy-client"
}

CLAUDE_HOOK_EVENTS = [
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "Stop",
    "SubagentStop",
    "Notification",
    "PreCompact",
    "SessionStart",
    "SessionEnd"
]

CURSOR_HOOK_EVENTS = [
    "beforeShellExecution",
    "beforeMCPExecution",
    "afterFileEdit",
    "beforeReadFile",
    "beforeSubmitPrompt",
    "stop"
]


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


def install_claude_hooks() -> int:
    """Configure Claude Code hooks."""
    print("Configuring Claude Code hooks...\n")

    # Load existing settings
    settings = {}
    if CLAUDE_SETTINGS_PATH.exists():
        try:
            with open(CLAUDE_SETTINGS_PATH, 'r') as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {CLAUDE_SETTINGS_PATH}", file=sys.stderr)
            settings = {}

    # Ensure hooks section exists
    if "hooks" not in settings:
        settings["hooks"] = {}

    hooks = settings["hooks"]
    changes_made = False

    # Configure each hook event
    for event in CLAUDE_HOOK_EVENTS:
        if event not in hooks:
            hooks[event] = []

        event_hooks = hooks[event] if isinstance(hooks[event], list) else []

        # Check if our hook is already configured
        found = any(
            hook.get("command") == "devleaps-policy-client"
            for group in event_hooks if isinstance(group, dict) and "hooks" in group
            for hook in group["hooks"] if isinstance(hook, dict)
        )

        if not found:
            event_hooks.append({"hooks": [HOOK_CONFIG]})
            changes_made = True
            print(f"  ✓ Added hook for {event}")

        hooks[event] = event_hooks

    # Save settings
    if changes_made:
        CLAUDE_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CLAUDE_SETTINGS_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"\n✓ Configuration saved to {CLAUDE_SETTINGS_PATH}")
        print("\nNext steps:")
        print("  1. Start a policy server: devleaps-policy-example-server")
        print("  2. Launch Claude Code - policies will be enforced automatically")
    else:
        print("✓ All hooks already configured - no changes needed")

    return 0


def install_cursor_hooks() -> int:
    """Configure Cursor hooks."""
    print("Configuring Cursor hooks...\n")

    # Load existing hooks
    hooks_config = {"version": 1, "hooks": {}}
    if CURSOR_HOOKS_PATH.exists():
        try:
            with open(CURSOR_HOOKS_PATH, 'r') as f:
                hooks_config = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {CURSOR_HOOKS_PATH}", file=sys.stderr)
            hooks_config = {"version": 1, "hooks": {}}

    if "hooks" not in hooks_config:
        hooks_config["hooks"] = {}

    hooks = hooks_config["hooks"]
    changes_made = False

    # Configure each hook event
    for event in CURSOR_HOOK_EVENTS:
        if event not in hooks:
            hooks[event] = []

        event_hooks = hooks[event] if isinstance(hooks[event], list) else []

        # Check if our hook is already configured
        found = any(
            hook.get("command") == "devleaps-policy-client"
            for hook in event_hooks if isinstance(hook, dict)
        )

        if not found:
            event_hooks.append({"command": "devleaps-policy-client"})
            changes_made = True
            print(f"  ✓ Added hook for {event}")

        hooks[event] = event_hooks

    # Save hooks
    if changes_made:
        CURSOR_HOOKS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CURSOR_HOOKS_PATH, 'w') as f:
            json.dump(hooks_config, f, indent=2)
        print(f"\n✓ Configuration saved to {CURSOR_HOOKS_PATH}")
        print("\nNext steps:")
        print("  1. Start a policy server: devleaps-policy-example-server")
        print("  2. Launch Cursor - policies will be enforced automatically")
    else:
        print("✓ All hooks already configured - no changes needed")

    return 0


def uninstall_claude_hooks() -> int:
    """Remove Claude Code hooks."""
    print("Removing Claude Code hooks...\n")

    if not CLAUDE_SETTINGS_PATH.exists():
        print(f"✓ No Claude Code configuration found at {CLAUDE_SETTINGS_PATH}")
        return 0

    try:
        with open(CLAUDE_SETTINGS_PATH, 'r') as f:
            settings = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse {CLAUDE_SETTINGS_PATH}", file=sys.stderr)
        return 1

    if "hooks" not in settings:
        print("✓ No hooks configured - nothing to remove")
        return 0

    hooks = settings["hooks"]
    changes_made = False

    for event in CLAUDE_HOOK_EVENTS:
        if event not in hooks:
            continue

        event_hooks = hooks[event] if isinstance(hooks[event], list) else []
        original_count = len(event_hooks)

        # Remove all groups containing our hook
        event_hooks = [
            group for group in event_hooks
            if not (isinstance(group, dict) and "hooks" in group and any(
                hook.get("command") == "devleaps-policy-client"
                for hook in group["hooks"] if isinstance(hook, dict)
            ))
        ]

        if len(event_hooks) < original_count:
            hooks[event] = event_hooks
            changes_made = True
            print(f"  ✓ Removed hook for {event}")

    if changes_made:
        with open(CLAUDE_SETTINGS_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"\n✓ Configuration updated at {CLAUDE_SETTINGS_PATH}")
    else:
        print("✓ No devleaps-policy-client hooks found - nothing to remove")

    return 0


def uninstall_cursor_hooks() -> int:
    """Remove Cursor hooks."""
    print("Removing Cursor hooks...\n")

    if not CURSOR_HOOKS_PATH.exists():
        print(f"✓ No Cursor configuration found at {CURSOR_HOOKS_PATH}")
        return 0

    try:
        with open(CURSOR_HOOKS_PATH, 'r') as f:
            hooks_config = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse {CURSOR_HOOKS_PATH}", file=sys.stderr)
        return 1

    if "hooks" not in hooks_config:
        print("✓ No hooks configured - nothing to remove")
        return 0

    hooks = hooks_config["hooks"]
    changes_made = False

    for event in CURSOR_HOOK_EVENTS:
        if event not in hooks:
            continue

        event_hooks = hooks[event] if isinstance(hooks[event], list) else []
        original_count = len(event_hooks)

        # Remove our hooks
        event_hooks = [
            hook for hook in event_hooks
            if not (isinstance(hook, dict) and hook.get("command") == "devleaps-policy-client")
        ]

        if len(event_hooks) < original_count:
            hooks[event] = event_hooks
            changes_made = True
            print(f"  ✓ Removed hook for {event}")

    if changes_made:
        with open(CURSOR_HOOKS_PATH, 'w') as f:
            json.dump(hooks_config, f, indent=2)
        print(f"\n✓ Configuration updated at {CURSOR_HOOKS_PATH}")
    else:
        print("✓ No devleaps-policy-client hooks found - nothing to remove")

    return 0


def cmd_install(args: List[str]) -> int:
    """Install hooks for Claude Code or Cursor."""
    if len(args) == 0 or args[0] == "claude-code":
        return install_claude_hooks()
    elif args[0] == "cursor":
        return install_cursor_hooks()
    else:
        print(f"Unknown editor: {args[0]}", file=sys.stderr)
        print("Usage: devleaps-policy-client install [claude-code|cursor]", file=sys.stderr)
        return 1


def cmd_uninstall(args: List[str]) -> int:
    """Uninstall hooks for Claude Code or Cursor."""
    if len(args) == 0 or args[0] == "claude-code":
        return uninstall_claude_hooks()
    elif args[0] == "cursor":
        return uninstall_cursor_hooks()
    else:
        print(f"Unknown editor: {args[0]}", file=sys.stderr)
        print("Usage: devleaps-policy-client uninstall [claude-code|cursor]", file=sys.stderr)
        return 1


def show_help() -> int:
    """Show help message."""
    print("devleaps-policy-client - Policy enforcement client for AI agents")
    print()
    print("Usage:")
    print("  devleaps-policy-client install [claude-code|cursor]")
    print("      Configure hooks for the specified editor (default: claude-code)")
    print()
    print("  devleaps-policy-client uninstall [claude-code|cursor]")
    print("      Remove hooks for the specified editor (default: claude-code)")
    print()
    print("  devleaps-policy-client")
    print("      Process hook events from stdin (used by editor hooks)")
    print()
    print("Examples:")
    print("  devleaps-policy-client install              # Install Claude Code hooks")
    print("  devleaps-policy-client install cursor       # Install Cursor hooks")
    print("  devleaps-policy-client uninstall            # Uninstall Claude Code hooks")
    print("  devleaps-policy-client uninstall cursor     # Uninstall Cursor hooks")
    return 0


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "install":
            sys.exit(cmd_install(sys.argv[2:]))
        elif command == "uninstall":
            sys.exit(cmd_uninstall(sys.argv[2:]))
        elif command in ["--help", "-h", "help"]:
            sys.exit(show_help())
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            print("Run 'devleaps-policy-client --help' for usage", file=sys.stderr)
            sys.exit(1)

    # Default behavior: forward hook from stdin
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