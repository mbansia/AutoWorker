# Adapters

AutoWorker's install procedure (in `README.md`), recurring prompt
(`LOOP_PROMPT.md`), and templates (`MASTER_DIRECTIVES.md`, `RUNBOOK.md`)
are all agent-neutral markdown. The only agent-specific concern is
**invocation**: how the prompt is handed to the agent on a schedule,
and what config snippet the agent expects.

Each adapter is one file in this directory. It contains:

1. The CLI command(s) that run one pass.
2. The GitHub Actions step(s) to drop into `loop_workflow.yml`'s
   `{{AGENT_INVOCATION}}` slot.
3. The agent-config snippet (e.g. `CLAUDE.md`, `AGENTS.md`) that
   pre-authorises AutoWorker's PR autonomy.

## Available

| Adapter        | Agent              | Status          |
|----------------|--------------------|-----------------|
| `claude_code`  | Anthropic Claude Code | ✅ ready       |
| `codex`        | OpenAI Codex CLI   | ✅ ready        |
| `generic`      | Any CLI agent      | ✅ template     |

## Picking one

The install procedure in `README.md` asks the operator for an
`ADAPTER` parameter. Default = whichever agent is running the install
(e.g. `claude_code` if Claude Code is doing the install). The agent
then:

- Substitutes the adapter's invocation block into `loop_workflow.yml`.
- Appends the adapter's config snippet to your agent-config file.
- Records the chosen adapter in `.autoworker/config.yml` so future
  passes know.

## Adding a new adapter

Copy `adapters/generic.md` to `adapters/<your-agent>.md` and fill in:

- The exact CLI command — including any flags the agent needs to run
  non-interactively, accept a prompt from a file, and exit cleanly.
- Any auth setup (API keys, login flow).
- A config snippet that grants the agent permission to: read repo,
  create branches `autoworker/*`, push, open and merge PRs (within
  the `MASTER_DIRECTIVES.md` §8 boundary).

Open a PR with the new adapter. Maintainers will sanity-check the
invocation works in a dry run before tagging it ready.
