# Setups

A **setup** is one (AI agent + scheduler) pair. The install procedure
asks the operator to pick one; each setup file below is self-contained
(which workflows to install, which platform steps to take after the
install PR merges, secrets needed, config snippet).

## Available setups

| Setup | Agent | Scheduler | Recommended for |
|---|---|---|---|
| [`claude_code_web`](claude_code_web.md) | Claude Code | claude.ai/code Routines | tweakable, web-based control |
| [`claude_code_cli_loop`](claude_code_cli_loop.md) | Claude Code | local CLI `/loop` (interactive) | dev / testing on your machine |
| [`claude_code_github_actions`](claude_code_github_actions.md) | Claude Code | GitHub Actions cron | unattended production |
| [`codex_web`](codex_web.md) | OpenAI Codex | Codex cloud tasks | ChatGPT-native flow |
| [`codex_cli_github_actions`](codex_cli_github_actions.md) | OpenAI Codex | GitHub Actions cron | unattended production |
| [`antigravity`](antigravity.md) | Google Antigravity | Antigravity scheduler | Google-native flow |
| [`generic_github_actions`](generic_github_actions.md) | any CLI agent | GitHub Actions cron | template for new agents |

## How to pick

The install procedure proposes a default based on the agent running it:

- Claude Code on the web → `claude_code_web`
- Claude Code CLI on a laptop / dev box → `claude_code_cli_loop`
- Claude Code in a cloud / remote session → `claude_code_github_actions`
- Codex on the web → `codex_web`
- Codex CLI → `codex_cli_github_actions`
- Antigravity → `antigravity`
- Anything else with a CLI → `generic_github_actions`

You can override at install time by saying "use `<setup>`".

## What each setup installs

**All setups install the data ingest workflow** (`autoworker_data.yml`)
and its source modules. Cron is the natural place for signal
collection; this part doesn't change across setups.

**Setups differ in the loop:**

- **`*_github_actions` setups** also install `autoworker_loop.yml` so
  the agent runs unattended in GitHub Actions cron.
- **External-scheduler setups** (web Routines / CLI `/loop` /
  Antigravity / Codex cloud) skip the loop workflow. The operator
  wires the loop in their platform's scheduler after merging — the
  setup file gives the exact steps and the prompt to paste.

## Adding a new setup

Copy any existing setup file and adjust:

- Top of file: declare `Scheduler: Actions` or `Scheduler: external`
  — the install procedure reads this to decide whether to install
  `autoworker_loop.yml`.
- The platform-specific operator steps.
- The config snippet (which file it appends to — `CLAUDE.md`,
  `AGENTS.md`, etc.).
- The secrets list.

Open a PR and we'll review.
