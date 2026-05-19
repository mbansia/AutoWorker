# AutoWorker

A template for setting up **recurring scheduled coding agents** that
continuously improve a project across product, tech, security, UX,
marketing, and user-feedback dimensions — driven by **master directives**
you control. Agent-agnostic: works with Claude Code, OpenAI Codex CLI,
or any CLI agent.

## Install

In your target repo, ask your coding agent:

> Install AutoWorker from github.com/mbansia/AutoWorker

(or "incorporate AutoWorker", "import AutoWorker", "set up AutoWorker
in this repo".) The agent reads this README, asks you ~6 questions,
and opens an install PR. ~5 minutes.

After the PR merges, two GitHub Actions crons run on schedule: data
ingest builds a snapshot of signals into a tracker issue, then the
agent runs one pass against the tracker + master directives.

For a manual install you can drive yourself, see [`SETUP.md`](SETUP.md).

---

## For your coding agent — install procedure

> **Agent: if a user has asked you to install / incorporate / import /
> set up AutoWorker in their repo, follow this procedure verbatim.**
> The procedure is self-contained; you don't need to ask the user to
> paste anything else. Do not touch the operator's application code.

### Step 0 — Sanity checks before asking anything

- Confirm you're in a git repo. If not, ask the user to `git init`
  first.
- Confirm there's a remote. If not, ask the user to add one.
- Note which agent you are (Claude Code, Codex, etc.). You'll use this
  to pick the default adapter.

### Step 1 — Read this repo's template files

Fetch from `github.com/mbansia/AutoWorker`:

- `README.md` (this file)
- `SETUP.md`
- `LOOP_PROMPT.md`
- everything under `templates/`
- everything under `adapters/`

You can use raw GitHub URLs, `gh api`, or your GitHub MCP tools —
whichever is available.

### Step 2 — Ask the operator parameters, one at a time

Use your "ask user" tool (e.g. `AskUserQuestion`) — one question at a
time, with sensible defaults proposed:

| Parameter | Notes |
|---|---|
| `PROJECT_NAME` | Display name, e.g. "Acme". |
| `REPO_SLUG` | `owner/name`. Autodetect from `git remote -v`. |
| `PRIMARY_GOAL` | One-line outcome (e.g. "grow WAU 10% per quarter"). |
| `ADAPTER` | One of `claude_code`, `codex`, `generic`. Default: whichever agent is running this (e.g. `claude_code` if you're Claude Code). |
| `CRON_CADENCE` | Cron expression for the data ingest workflow. Default `0 */3 * * *` (every 3 hours). |
| `ENABLED_SOURCES` | Multi-select: `diagnostics_endpoint` (needs `BOT_URL` + `DIAGNOSTICS_TOKEN`), `github_signals` (uses `GITHUB_TOKEN`), `social_reddit` (no auth). Default: `github_signals` only. |
| `HAS_EXISTING_SPEC` | Y/N. If Y, ask `SPEC_PATH` and have `MASTER_DIRECTIVES.md` reference it instead of duplicating content. |

### Step 3 — Render templates into the target repo

Substitute every occurrence of these placeholders throughout the files
listed below:

- `{{PROJECT_NAME}}`, `{{REPO_SLUG}}`, `{{ADAPTER}}`,
  `{{CRON_CADENCE}}`, `{{CRON_CADENCE_LOOP}}` (cadence + 5 min offset),
  `{{CRON_CADENCE_HUMAN}}` (e.g. `3h`), `{{TRACKER_ISSUE_NUMBER}}`
  (you'll know this after step 5; for now, leave it as `0` and patch
  later).

File mappings:

| Template (source) | Target path in operator's repo |
|---|---|
| `templates/MASTER_DIRECTIVES.md` | `MASTER_DIRECTIVES.md` |
| `templates/RUNBOOK.md` | `RUNBOOK.md` |
| `templates/UPGRADE_BACKLOG.md` | `UPGRADE_BACKLOG.md` |
| `LOOP_PROMPT.md` | `LOOP_PROMPT.md` |
| `templates/data_ingest.yml` | `.github/workflows/autoworker_data.yml` |
| `templates/data_ingest.py` | `.github/scripts/autoworker_data_ingest.py` |
| `templates/loop_workflow.yml` | `.github/workflows/autoworker_loop.yml` |
| `templates/sources/README.md` | `.github/scripts/autoworker_sources/README.md` |
| `templates/sources/<name>.py` (per `ENABLED_SOURCES`) | `.github/scripts/autoworker_sources/<name>.py` |

For `loop_workflow.yml`'s `{{AGENT_INVOCATION}}` slot: substitute the
"GitHub Actions invocation" YAML block from `adapters/<ADAPTER>.md`.

Append the "Config snippet" section from `adapters/<ADAPTER>.md` to
the agent-config file (`CLAUDE.md` for claude_code, `AGENTS.md` for
codex, etc.). Create the file if it doesn't exist.

### Step 4 — Write the config files

`.autoworker/sources.yml` — generated from `ENABLED_SOURCES`. Example:

```yaml
enabled:
  - github_signals:
      labels: [bug, regression, urgent]
  # add diagnostics_endpoint or social_reddit here if enabled
```

`.autoworker/config.yml`:

```yaml
adapter: {{ADAPTER}}
cadence: {{CRON_CADENCE}}
```

### Step 5 — Create the persistent tracker issue

Use your GitHub tool (e.g. `mcp__github__issue_write`, or `gh issue
create`):

- Title: `[autoworker] Tracker`
- Labels: `autoworker-tracker` (create label if needed, colour `0e8a16`)
- Body: `Initial — awaiting first ingest run.`

Record the issue number. Re-render `MASTER_DIRECTIVES.md`, `RUNBOOK.md`,
`LOOP_PROMPT.md`, and the agent-config snippet with the real
`{{TRACKER_ISSUE_NUMBER}}`.

### Step 6 — Open an install PR

Branch: `autoworker/install`. Title: `Install AutoWorker`. Body:

```markdown
## Summary
- Agent adapter: <ADAPTER>
- Cadence: <CRON_CADENCE>
- Sources enabled: <ENABLED_SOURCES>
- Dimensions tracked: product, tech, security, UX, marketing, feedback
  (per MASTER_DIRECTIVES.md §§1–§7)

## Operator next-steps (before merging)
1. **Fill `MASTER_DIRECTIVES.md` §§1–§8.** Especially §8 (never-autoship).
   Autopilot will stay in monitor-only mode until §8 is non-default.
2. Set repo secrets:
   - `<AGENT_API_KEY>` (per `adapters/<ADAPTER>.md`)
   - <source-specific secrets if any>
3. Merge. The next scheduled tick runs ingest → tracker update → loop
   pass. Review PRs the agent opens on `autoworker/*` branches.

Tracker issue: #<TRACKER_ISSUE_NUMBER>
```

### Step 7 — Final summary to the operator

Output a short message:

- "Created tracker issue #X."
- "Opened install PR #Y."
- "Secrets to set after merge: ..." (list per chosen adapter + sources)
- "First scheduled run: <approx time based on cadence>."

### Constraints — agent must obey

- **Do NOT push directly to main.** Branch + PR only.
- **Do NOT touch the operator's application code.** Only AutoWorker
  files.
- **If `MASTER_DIRECTIVES.md` §8 is left at defaults**, post a loud
  warning comment on the install PR: "Autopilot will not run until §8
  is filled. The loop will stay in monitor-only mode."
- **If the operator selected `diagnostics_endpoint`** but doesn't have
  a service running, ask them to confirm or downgrade to
  `github_signals` only.
- **Do NOT skip the tracker issue creation.** The loop has no input
  surface without it.

---

## What it does (after install)

- **Data ingest cron** (`autoworker_data.yml`) fires on the configured
  cadence. Polls each enabled data source, aggregates results,
  updates the `[autoworker] Tracker` issue body, posts a heartbeat
  comment.
- **Loop cron** (`autoworker_loop.yml`) triggers immediately after on
  `workflow_run` (or via its own schedule as fallback). The agent
  reads `MASTER_DIRECTIVES.md` + tracker, runs one pass per
  `RUNBOOK.md`: classifies signals, comments on the tracker, optionally
  opens ONE PR from defined safe surfaces.
- **One PR per pass**, `<` 200 lines, tests must pass before commit,
  never crosses `MASTER_DIRECTIVES.md` §8.
- **Backpressure**: un-reviewed PRs pause shipping; operator pushback
  (unmerge, disagree, revert) triggers a 3-pass cooldown; CI red on
  main stops all upgrades.

## When to use this

- A long-running project (service, SaaS, bot, library, content site)
  you want an agent driving forward on a schedule.
- You're willing to write a one-page master directives document with
  goals, guardrails, and signal criteria.
- You want agent-agnosticism so the CLI choice doesn't lock the setup.

## When NOT to use this

- The project handles real money and has no clear policy boundary yet.
  **Fill `MASTER_DIRECTIVES.md` §8 first.** Autopilot is unsafe
  without it.
- You want unsupervised autonomy with no guardrails. AutoWorker is
  *bounded* autonomy, not full autonomy.
- The project has no observable surface (no diagnostics, no issues, no
  metrics). The `github_signals` source needs something to chew on.

## Dimensions

`MASTER_DIRECTIVES.md` has a section per dimension. The agent uses
them to classify signals and to evaluate "does this work move the
project forward?":

| §  | Dimension                       | Typical signals                                |
|----|--------------------------------|------------------------------------------------|
| §1 | Goals                          | top-level outcomes everything ladders to       |
| §2 | Product                        | feature parity gaps, roadmap progress          |
| §3 | Tech                           | perf budgets, code quality, deprecations       |
| §4 | Security                       | CVEs on deps, vuln scans, auth path drift      |
| §5 | UX                             | accessibility gaps, broken flows, copy drift   |
| §6 | Marketing                      | changelog gaps, doc drift, positioning copy   |
| §7 | User feedback                  | issues, social mentions, support themes        |
| §8 | Guardrails (never-autoship)    | the hard boundary                              |
| §9 | Learnings                      | append-only after every PR                     |

You decide what's in scope by what you fill in. Sections are
independent — the agent can ship a UX tweak while staying silent on
marketing.

## Agent-agnostic

Three adapters out of the box:

- [`adapters/claude_code.md`](adapters/claude_code.md) — Anthropic
  Claude Code, via `claude --print` in cron (or `/loop` locally).
- [`adapters/codex.md`](adapters/codex.md) — OpenAI Codex CLI, via
  `codex exec` in cron.
- [`adapters/generic.md`](adapters/generic.md) — template for any
  other CLI agent.

Prompts (`LOOP_PROMPT.md`) and templates (`MASTER_DIRECTIVES.md`,
`RUNBOOK.md`) are agent-neutral markdown. Adapter files cover only
invocation + the agent-config snippet.

## Repo layout

```
README.md               # this file — entry point + agent procedure
SETUP.md                # manual install reference for humans
LOOP_PROMPT.md          # the recurring pass prompt (rendered into target)
EXAMPLE_AUTOTRADER.md   # case study: AutoWorker on a production trading bot
LICENSE                 # MIT

adapters/               # one file per supported coding-agent CLI
  README.md
  claude_code.md
  codex.md
  generic.md

templates/              # rendered into target repo by the install procedure
  MASTER_DIRECTIVES.md    # the binding spec (§§1–§9)
  RUNBOOK.md              # operational procedure for a pass
  UPGRADE_BACKLOG.md      # operator hint box (hints / hold / shipped)
  data_ingest.yml         # GitHub Actions cron: data ingest
  data_ingest.py          # cron dispatcher: loads + runs enabled sources
  loop_workflow.yml       # GitHub Actions cron: agent loop pass
  sources/                # built-in data source modules
    README.md
    diagnostics_endpoint.py
    github_signals.py
    social_reddit.py
```

## Acknowledgements

Pattern + safety rails developed during the v1.3 → v1.5 rewrite of
[AutoTrader_Codex](https://github.com/mbansia/autotrader_codex). See
[`EXAMPLE_AUTOTRADER.md`](EXAMPLE_AUTOTRADER.md) for a concrete
deployment.

## License

MIT.
