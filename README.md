# AutoWorker

A template for setting up **recurring scheduled coding agents** that
continuously improve a project across product, tech, security, UX,
marketing, and user-feedback dimensions — driven by **master directives**
you control. Agent-agnostic: works with Claude Code, OpenAI Codex CLI,
or any CLI agent (one adapter file per agent).

```
import AutoWorker  →  ~5 min bootstrap  →  hands-off recurring loop
```

## What it does

- **Data ingest cron** (GitHub Actions) pulls signals into a persistent
  GitHub tracker issue: diagnostics endpoints, GitHub issues + CI
  failures, social media mentions, anything you wire up.
- **Loop cron** (GitHub Actions) fires the coding agent on the same
  cadence. The agent reads master directives + tracker, classifies
  signals, and either comments, opens a PR, or asks the operator —
  per a rule set you control.
- **One PR per pass**, < 200 lines, tests must pass, never crosses the
  `MASTER_DIRECTIVES.md` §8 boundary (your never-autoship hard line).
- Backpressure rails: un-reviewed PRs pause shipping, operator
  pushback triggers a 3-pass cooldown, CI-red on main stops all
  upgrades.

## When to use this

- You have a long-running project (service, SaaS, bot, library, content
  site) and you want a coding agent driving it forward on a schedule
  rather than ad-hoc.
- You have — or are willing to write — a one-page master directives
  document defining goals, guardrails, and signal criteria across the
  dimensions you care about.
- You want this to be agent-agnostic so the choice of CLI doesn't lock
  the architecture.

## When NOT to use this

- The project handles real money and you have no clear policy boundary
  yet. **Write `MASTER_DIRECTIVES.md` §8 first.** Autopilot is unsafe
  without it.
- You want fully unsupervised behaviour with no guardrails. AutoWorker
  is *bounded* autonomy, not full autonomy.
- The project has no observable surface at all (no diagnostics, no
  issues, no metrics). At minimum the `github_signals` source needs
  some inbound issues / CI to chew on.

## Repo layout

```
README.md               # this file
SETUP.md                # manual install reference
BOOTSTRAP_PROMPT.md     # paste into your agent for one-shot install
LOOP_PROMPT.md          # the recurring pass prompt
EXAMPLE_AUTOTRADER.md   # case study: AutoWorker on a production trading bot

adapters/               # one file per supported coding-agent CLI
  README.md
  claude_code.md
  codex.md
  generic.md

templates/              # rendered into your target repo by the bootstrap
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

LICENSE                 # MIT
```

## Fast install

Paste [`BOOTSTRAP_PROMPT.md`](BOOTSTRAP_PROMPT.md) into a fresh agent
session opened in your target repo. The agent asks you ~6 parameters
(project name, repo slug, primary goal, adapter, cron cadence, enabled
sources), renders the templates, creates the tracker issue, opens an
install PR you review and merge.

Manual install: see [`SETUP.md`](SETUP.md).

## Dimensions

AutoWorker treats improvement as multi-dimensional. `MASTER_DIRECTIVES.md`
has a section per dimension; the agent uses them to classify signals
and to evaluate "is this work moving the project forward?":

| §  | Dimension                       | Typical signals                                |
|----|--------------------------------|------------------------------------------------|
| §1 | Goals                          | the top-level outcomes everything ladders to   |
| §2 | Product                        | feature parity gaps, roadmap progress          |
| §3 | Tech                           | perf budgets, code quality, deprecations       |
| §4 | Security                       | CVEs on deps, vuln scans, auth path drift      |
| §5 | UX                             | accessibility gaps, broken flows, copy drift   |
| §6 | Marketing                      | changelog gaps, doc drift, positioning copy    |
| §7 | User feedback                  | issues, social mentions, support themes        |
| §8 | Guardrails (never-autoship)    | the hard boundary                              |
| §9 | Learnings                      | append-only after every PR                     |

Sections are independent: the agent can ship a UX tweak while staying
silent on marketing, or vice versa. You decide what's in scope by what
you fill in.

## Agent-agnostic

Three adapters out of the box:

- [`adapters/claude_code.md`](adapters/claude_code.md) — Anthropic
  Claude Code, via `claude --print` in a GitHub Actions cron (or
  `/loop` locally).
- [`adapters/codex.md`](adapters/codex.md) — OpenAI Codex CLI, via
  `codex exec` in cron.
- [`adapters/generic.md`](adapters/generic.md) — template for any
  other CLI agent; copy, fill in invocation details, PR it back.

The prompts (`BOOTSTRAP_PROMPT.md`, `LOOP_PROMPT.md`) and templates
(`MASTER_DIRECTIVES.md`, `RUNBOOK.md`) are agent-neutral markdown.
Adapter files cover only invocation + the agent-config snippet.

## Acknowledgements

Pattern + safety rails developed during the v1.3 → v1.5 rewrite of
[AutoTrader_Codex](https://github.com/mbansia/autotrader_codex). See
[`EXAMPLE_AUTOTRADER.md`](EXAMPLE_AUTOTRADER.md) for a concrete
deployment. AutoWorker v1 is the generalisation of that pattern.

## License

MIT.
