# AI Agent Policies

[![PyPI](https://img.shields.io/pypi/v/devleaps-agent-policies.svg)](https://pypi.org/project/devleaps-agent-policies/)

Policies turn your [Cursor Rules](https://cursor.com/docs/context/rules) or [CLAUDE.md](https://docs.claude.com/en/docs/claude-code/memory) into hard guardrails which an AI Agent cannot simply ignore, or forget. They handle what to do when an agent wants to make a decision, along with other [hooks-supported events](https://github.com/Devleaps/agent-policies/blob/main/devleaps/policies/server/common/models.py). Policies can yield both decisions and guidance.

This framework supports **Claude Code**. Support for **Cursor** is in beta.

## Why Policies

### Automating Decisions

Rule files can be forgotten or ignored completely by LLMs. Policies are unavoidable:

```python
if re.match(r'^terraform\s+apply(?:\s|$)', command):
    yield PolicyDecision(action=PolicyAction.DENY, reason="terraform apply is not allowed. Use `terraform plan` instead.")

if re.match(r'^terraform\s+(fmt|plan)(?:\s|$)', command):
    yield PolicyDecision(action=PolicyAction.ALLOW)
```

> <img width="648" height="133" alt="Screenshot 2025-10-03 at 16 15 29" src="https://github.com/user-attachments/assets/4659a391-2e96-431f-85e7-7d3973f2d101" />

> [!WARNING]  
> Be aware when automatically allowing that Bash tools use strings can invole more than one underlying tool. Consider also commands such as `find` having unsafe options like `-exec`.

### Automating Guidance

Aside from denying and allowing automatically, policies can also provide guidance:

```python
if re.match(r'^python\s+test_', input_data.command):
    yield PolicyGuidance(content="Consider using pytest instead of running test files directly")
```


> <img width="652" height="167" alt="Screenshot 2025-10-03 at 16 15 21" src="https://github.com/user-attachments/assets/5ee865d3-edd3-4c18-92d2-b984dd0582da" />

## Usage

At DevLeaps we developed an internal policy set for AI Agents. To create your own, refer to the [example server](https://github.com/Devleaps/agent-policies/blob/main/devleaps/policies/example/main.py) as a starting point The example server contains:
- A basic server setup demonstrating the use of policies and middleware.
- Rudimentary policies showcasing how to automatically deny, allow and provide guidance.
- Rudimentary middleware showcasing how multi-command tool use could be handled.

**To run the example server:**
```bash
devleaps-policy-example-server
```

This starts a minimal server running just our example policies.

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
