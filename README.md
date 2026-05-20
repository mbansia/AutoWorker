# AutoWorker

A template for setting up **recurring scheduled coding agents** that
continuously improve a project across product, tech, security, UX,
marketing, and user-feedback dimensions — driven by **master directives**
you control. Setup-agnostic: works with Claude Code (web Routines / CLI
`/loop` / GitHub Actions), OpenAI Codex (cloud / CLI), Google
Antigravity, or any CLI agent in cron.

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
- Note which agent you are (Claude Code, Codex, etc.) and roughly
  where you're running (web app, local CLI, GitHub Actions). You'll
  use this to propose a default `SETUP`.

### Step 1 — Read this repo's template files

Fetch from `github.com/mbansia/AutoWorker`:

- `README.md` (this file)
- `SETUP.md`
- `LOOP_PROMPT.md`
- everything under `templates/`
- everything under `setups/`

You can use raw GitHub URLs, `gh api`, or your GitHub MCP tools —
whichever is available.

### Step 2 — Ask the operator parameters, one at a time

Use your "ask user" tool (e.g. `AskUserQuestion`) — one question at a
time, with sensible defaults proposed. **Start with `SETUP`** — every
other parameter follows from it.

| Parameter | Notes |
|---|---|
| `SETUP` | Which (agent + scheduler) combo. One of: `claude_code_web`, `claude_code_cli_loop`, `claude_code_github_actions`, `codex_web`, `codex_cli_github_actions`, `antigravity`, `generic_github_actions`. Read `setups/README.md` for the menu + defaults. Propose the one that matches the agent + runtime running this install; let the operator override. |
| `PROJECT_NAME` | Display name, e.g. "Acme". |
| `REPO_SLUG` | `owner/name`. Autodetect from `git remote -v`. |
| `PRIMARY_GOAL` | One-line outcome (e.g. "grow WAU 10% per quarter"). |
| `CRON_CADENCE` | Cron expression for the data ingest workflow. Default `0 */3 * * *` (every 3 hours). |
| `ENABLED_SOURCES` | Multi-select: `diagnostics_endpoint` (needs `BOT_URL` + `DIAGNOSTICS_TOKEN`), `github_signals` (uses `GITHUB_TOKEN`), `social_reddit` (no auth). Default: `github_signals` only. |
| `HAS_EXISTING_SPEC` | Y/N. If Y, ask `SPEC_PATH` and have `MASTER_DIRECTIVES.md` reference it instead of duplicating content. |

After `SETUP` is chosen, read `setups/<SETUP>.md` end to end. It tells
you which workflows to install, which agent-config file to append to,
which secrets to surface, and what platform-specific steps the
operator needs to do after the install PR merges.

**A setup is "Actions-based"** if its filename ends in
`_github_actions`. Otherwise it uses an external scheduler (web
Routines / CLI `/loop` / Antigravity / Codex cloud).

### Step 3 — Render templates into the target repo

Substitute every occurrence of these placeholders throughout the files
listed below:

- `{{PROJECT_NAME}}`, `{{REPO_SLUG}}`, `{{SETUP}}`,
  `{{CRON_CADENCE}}`, `{{CRON_CADENCE_LOOP}}` (cadence + 5 min offset),
  `{{CRON_CADENCE_HUMAN}}` (e.g. `3h`), `{{TRACKER_ISSUE_NUMBER}}`
  (you'll know this after step 5; for now, leave it as `0` and patch
  later).

**Always-rendered file mappings (every setup):**

| Template (source) | Target path in operator's repo |
|---|---|
| `templates/MASTER_DIRECTIVES.md` | `MASTER_DIRECTIVES.md` |
| `templates/RUNBOOK.md` | `RUNBOOK.md` |
| `templates/UPGRADE_BACKLOG.md` | `UPGRADE_BACKLOG.md` |
| `LOOP_PROMPT.md` | `LOOP_PROMPT.md` |
| `templates/data_ingest.yml` | `.github/workflows/autoworker_data.yml` |
| `templates/data_ingest.py` | `.github/scripts/autoworker_data_ingest.py` |
| `templates/sources/README.md` | `.github/scripts/autoworker_sources/README.md` |
| `templates/sources/<name>.py` (per `ENABLED_SOURCES`) | `.github/scripts/autoworker_sources/<name>.py` |

**Conditional — only for Actions-based setups (`*_github_actions`):**

| Template (source) | Target path in operator's repo |
|---|---|
| `templates/loop_workflow.yml` | `.github/workflows/autoworker_loop.yml` |

For Actions-based setups: substitute the "GitHub Actions invocation"
YAML block from `setups/<SETUP>.md` into `loop_workflow.yml`'s
`{{AGENT_INVOCATION}}` slot.

For external-scheduler setups: **skip the loop workflow entirely**.
The setup file's "Operator setup steps" section tells the operator
how to wire the loop in their platform.

Append the "Config snippet" section from `setups/<SETUP>.md` to the
agent-config file (`CLAUDE.md` / `AGENTS.md` / whatever the setup
file specifies). Create the file if it doesn't exist.

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
setup: {{SETUP}}
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
- Setup: <SETUP> (agent + scheduler)
- Cadence: <CRON_CADENCE>
- Sources enabled: <ENABLED_SOURCES>
- Dimensions tracked: product, tech, security, UX, marketing, feedback
  (per MASTER_DIRECTIVES.md §§1–§7)

## Operator next-steps (before merging)
1. **Fill `MASTER_DIRECTIVES.md` §§1–§8.** Especially §8 (never-autoship).
   Autopilot will stay in monitor-only mode until §8 is non-default.
2. Set repo secrets per `setups/<SETUP>.md`:
   - <agent API key, source-specific secrets if any>
3. Merge.

## Operator next-steps (after merging)
<inline-quote the "Operator setup steps" section from
 setups/<SETUP>.md here so the operator sees the exact platform
 actions to take next>

Tracker issue: #<TRACKER_ISSUE_NUMBER>
```

### Step 7 — Final summary to the operator

Output a short message:

- "Setup chosen: <SETUP>."
- "Created tracker issue #X."
- "Opened install PR #Y."
- "Secrets to set after merge: ..." (list per chosen setup + sources)
- "After merge, follow the 'Operator setup steps' block in the PR
  description (also in `setups/<SETUP>.md`) to finish wiring the
  loop in your platform." (Skip this line for `*_github_actions`
  setups — those are fully unattended after merge.)
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
- **Do NOT install `autoworker_loop.yml`** for external-scheduler
  setups — it would clash with the scheduler the operator's platform
  will run.

---

## What it does (after install)

- **Data ingest cron** (`autoworker_data.yml`, always installed) fires
  on the configured cadence. Polls each enabled data source, aggregates
  results, updates the `[autoworker] Tracker` issue body, posts a
  heartbeat comment.
- **Agent loop** runs the same cadence — either via the
  `autoworker_loop.yml` GitHub Actions workflow (for `*_github_actions`
  setups) or via your platform's native scheduler (Claude Code web
  Routines, CLI `/loop`, Codex cloud, Antigravity, etc.). The agent
  reads `MASTER_DIRECTIVES.md` + tracker, runs one pass per
  `RUNBOOK.md`: classifies signals, comments on the tracker,
  optionally opens ONE PR from defined safe surfaces.
- **One PR per pass**, `<` 200 lines, tests must pass before commit,
  five-pass persona audit before merge, never crosses
  `MASTER_DIRECTIVES.md` §8.
- **Backpressure**: un-reviewed PRs pause shipping; operator pushback
  (unmerge, disagree, revert) triggers a 3-pass cooldown; CI red on
  main stops all upgrades.

## Defaults the agent ships with

`MASTER_DIRECTIVES.md` includes two operating sections out of the box,
both editable per project:

- **§0.5 — Operating persona.** The agent thinks as a master **CTO +
  Product Manager + Founder CEO + QA + Marketer** simultaneously. Every
  change is evaluated through all five lenses; trade-offs are surfaced,
  not silently chosen.
- **§0.6 — Operating principles.** Respect existing project preferences
  (your `CLAUDE.md` / `AGENTS.md` overrides AutoWorker defaults).
  **Five-pass persona audit before merging** — one independent pass
  per persona (CTO → PM → CEO → QA → Marketer), verdicts documented in
  the PR. New branch per piece of work, always. Track work in `[ ]` /
  `[x]` checklist form for mid-pass visibility.

These travel with every install. Tighten or loosen them per project.

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

## Setups (agent + scheduler)

A **setup** is one (agent + scheduler) pair. Pick one at install time.
Seven ship out of the box (see [`setups/README.md`](setups/README.md)
for the menu):

| Setup | Agent | Scheduler |
|---|---|---|
| [`claude_code_web`](setups/claude_code_web.md) | Claude Code | claude.ai/code Routines |
| [`claude_code_cli_loop`](setups/claude_code_cli_loop.md) | Claude Code | local CLI `/loop` |
| [`claude_code_github_actions`](setups/claude_code_github_actions.md) | Claude Code | GitHub Actions cron |
| [`codex_web`](setups/codex_web.md) | OpenAI Codex | Codex cloud tasks |
| [`codex_cli_github_actions`](setups/codex_cli_github_actions.md) | OpenAI Codex | GitHub Actions cron |
| [`antigravity`](setups/antigravity.md) | Google Antigravity | Antigravity scheduler |
| [`generic_github_actions`](setups/generic_github_actions.md) | any CLI agent | GitHub Actions cron |

Prompts (`LOOP_PROMPT.md`) and templates (`MASTER_DIRECTIVES.md`,
`RUNBOOK.md`) are agent-neutral markdown. Setup files cover only
invocation, scheduler-specific wiring, and the agent-config snippet.

## Repo layout

```
README.md               # this file — entry point + agent procedure
SETUP.md                # manual install reference for humans
LOOP_PROMPT.md          # the recurring pass prompt (rendered into target)
EXAMPLE_AUTOTRADER.md   # case study: AutoWorker on a production trading bot
LICENSE                 # MIT

setups/                 # one file per (agent + scheduler) combo
  README.md
  claude_code_web.md
  claude_code_cli_loop.md
  claude_code_github_actions.md
  codex_web.md
  codex_cli_github_actions.md
  antigravity.md
  generic_github_actions.md

templates/              # rendered into target repo by the install procedure
  MASTER_DIRECTIVES.md    # the binding spec (§§1–§9)
  RUNBOOK.md              # operational procedure for a pass
  UPGRADE_BACKLOG.md      # operator hint box (hints / hold / shipped)
  data_ingest.yml         # GitHub Actions cron: data ingest (always installed)
  data_ingest.py          # cron dispatcher: loads + runs enabled sources
  loop_workflow.yml       # GitHub Actions cron: only for *_github_actions setups
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
