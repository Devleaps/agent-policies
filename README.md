# AI Agent Policies

[![PyPI](https://img.shields.io/pypi/v/devleaps-agent-policies.svg)](https://pypi.org/project/devleaps-agent-policies/)

Policies turn your [Cursor Rules](https://cursor.com/docs/context/rules) or [CLAUDE.md](https://docs.claude.com/en/docs/claude-code/memory) into hard guardrails which an AI Agent cannot simply ignore, or forget. They handle what to do when an agent wants to make a decision, along with other [hooks-supported events](https://github.com/Devleaps/agent-policies/blob/main/devleaps/policies/server/common/models.py). Policies can yield both decisions and guidance.

This framework supports **Claude Code**. Support for **Cursor** is in beta.

## Why Policies

Policies are significantly stronger than rules. Rule files can be forgotten or ignored completely, whereas policies are unavoidable:

```python
def rudimentary_terraform_rule(input_data: ToolUseEvent):
    if not input_data.tool_is_bash:
        return

    command = input_data.command.strip()

    if re.match(r'^terraform\s+apply(?:\s|$)', command):
        yield PolicyDecision(action=PolicyAction.DENY, reason="terraform apply is not allowed. Use `terraform plan` instead.")

    if re.match(r'^terraform\s+(fmt|plan)(?:\s|$)', command):
        yield PolicyDecision(action=PolicyAction.ALLOW)
```

Aside from denying and allowing automatically, policies can also provide guidance when it seems agents are going off track or missing standards:

```python
def rudimentary_guidance_for_python(input_data: ToolUseEvent):
    if not input_data.tool_is_bash:
        return

    if re.match(r'^python\s+test_', input_data.command):
        yield PolicyGuidance(content="Consider using pytest instead of running test files directly")
```

Be aware that tool use with bash can contain control operators and separators, moreover, some commands allow execution of others: Consider for example `find` with `-exec`. Be careful what you whitelist, and how you parse Bash. At DevLeaps we also have an internal policy set, which is not included in this project. To create your own, refer to the [example server](https://github.com/Devleaps/agent-policies/blob/main/devleaps/policies/example/main.py) which contains a rudimentary bash middleware to demonstrate what is possible with the framework.

## Examples

### Real World Examples

Policies can prevent Bash dangerous bash commands completely:<br/>

> <img src="https://github.com/user-attachments/assets/ccc775f1-0fb8-4072-bdbe-96fecc5ea2db" />

Policies can provide guidance to agents when they go off track:<br/>

> <img src="https://github.com/user-attachments/assets/a9f26fba-ae26-40ff-ab53-92a9a646428c" />

Policies can automatically allow safe commands without interrupting developers:<br/>

> <img src="https://github.com/user-attachments/assets/da20d0ea-6ba0-4626-bdb0-10dba4f6a0b1" />

## Usage

Have a look at the [example server](https://github.com/Devleaps/agent-policies/blob/main/devleaps/policies/example/main.py) as a starting point!

It contains:
- A complete example server with policies and middleware.
- Rudimentary policies on how to automatically deny, allow and provide guidance.
- Rudimentary middleware demonstrating how multi-command tool use could be handled.

**To run the example server:**
```bash
devleaps-policy-example-server
```

This starts a minimal server with just these example policies.

## Architecture

```mermaid
graph TB
    subgraph "Developer Machine"
      Editor[Claude Code / Cursor]
        Client[devleaps-policy-client]
    end

    subgraph "Policy Server"
        Server[HTTP API]
        Policies[Your policies<br/>kubectl, terraform, git, python, etc.]
    end

    Editor -->|Hooks| Client
    Client --> Server
    Server -->|Events| Policies
    Policies -->|Decision and Guidance| Server
    Server --> Client
    Client -->|Decision and Guidance| Editor
```

## Quick Start

### Installation

Update your local profile with;

```bash
# Add the bin directory to $PATH
export PATH="$PATH:/path/to/agent-policies/bin/"
```

### Running an Example Server

```bash
devleaps-policy-example-server
```

The example server runs on port 8338 by default and serves endpoints for both Claude Code and Cursor.

### Configure Claude Code

Add `devleaps-policy-client` to your Claude Code hooks configuration in `~/.claude/settings.json`:

<details>
<summary>Click to expand Claude Code configuration</summary>

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "matcher": "*",
            "type": "command",
            "command": "devleaps-policy-client claude-code"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "matcher": "*",
            "type": "command",
            "command": "devleaps-policy-client claude-code"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "matcher": "*",
            "type": "command",
            "command": "devleaps-policy-client claude-code"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "matcher": "*",
            "type": "command",
            "command": "devleaps-policy-client claude-code"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "matcher": "*",
            "type": "command",
            "command": "devleaps-policy-client claude-code"
          }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {
            "matcher": "*",
            "type": "command",
            "command": "devleaps-policy-client claude-code"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "matcher": "*",
            "type": "command",
            "command": "devleaps-policy-client claude-code"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "matcher": "*",
            "type": "command",
            "command": "devleaps-policy-client claude-code"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "matcher": "*",
            "type": "command",
            "command": "devleaps-policy-client claude-code"
          }
        ]
      }
    ]
  }
}
```

</details>

### Configure Cursor

Create or edit `~/.cursor/hooks.json`:

<details>
<summary>Click to expand Cursor configuration</summary>

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      { "command": "devleaps-policy-client cursor" }
    ],
    "beforeMCPExecution": [
      { "command": "devleaps-policy-client cursor" }
    ],
    "afterFileEdit": [
      { "command": "devleaps-policy-client cursor" }
    ],
    "beforeReadFile": [
      { "command": "devleaps-policy-client cursor" }
    ],
    "beforeSubmitPrompt": [
      { "command": "devleaps-policy-client cursor" }
    ],
    "stop": [
      { "command": "devleaps-policy-client cursor" }
    ]
  }
}
```

The `devleaps-policy-client cursor` command will forward hook events to the policy server running on `localhost:8338`.

</details>

## Development

This project is built with [uv](https://docs.astral.sh/uv/).
