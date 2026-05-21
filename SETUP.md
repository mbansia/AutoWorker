# Setup

The fast path is to **ask your coding agent to install AutoWorker for
you**. In your target repo, say something like:

> Install AutoWorker from github.com/mbansia/AutoWorker

The agent reads [`README.md`](README.md), which contains the install
procedure it should follow: ask you for `SETUP` + ~5 more parameters,
render templates, create the tracker issue, wire the crons, open a PR
that includes the platform-specific operator steps for the setup you
chose.

This file documents the **manual install** for operators who want to
do it themselves or audit each step.

## Pick your setup first

Open [`setups/README.md`](setups/README.md) and pick the one that
matches your agent + scheduling preference:

| Setup | Agent | Scheduler |
|---|---|---|
| `claude_code_web` | Claude Code | claude.ai/code Routines |
| `claude_code_cli_loop` | Claude Code | local CLI `/loop` |
| `claude_code_github_actions` | Claude Code | GitHub Actions cron |
| `codex_web` | OpenAI Codex | Codex cloud tasks |
| `codex_cli_github_actions` | OpenAI Codex | GitHub Actions cron |
| `antigravity` | Google Antigravity | Antigravity scheduler |
| `generic_github_actions` | any CLI agent | GitHub Actions cron |

Setups ending in `_github_actions` install **both** `autoworker_data.yml`
and `autoworker_loop.yml`. The others install only `autoworker_data.yml`
and rely on your platform's native scheduler for the loop.

## What gets installed in your target repo

```
MASTER_DIRECTIVES.md                            # the binding spec (root)
RUNBOOK.md                                      # operational procedure (root)
UPGRADE_BACKLOG.md                              # operator hint box (root)
LOOP_PROMPT.md                                  # rendered, fed to the agent each pass

CLAUDE.md  / AGENTS.md  (per chosen setup)      # merged or created

.autoworker/
  config.yml                                    # setup + cadence
  sources.yml                                   # enabled data sources

.github/
  workflows/
    autoworker_data.yml                         # data ingest cron (always)
    autoworker_loop.yml                         # only for *_github_actions setups
  scripts/
    autoworker_data_ingest.py                   # ingest dispatcher
    autoworker_sources/
      README.md
      <enabled-sources>.py                      # one per chosen source

A persistent GitHub issue: `[autoworker] Tracker` (label
`autoworker-tracker`).
```

Nothing else. AutoWorker doesn't touch your application code.

## Manual install

```bash
# 1. Clone the template repo somewhere
git clone https://github.com/mbansia/AutoWorker.git /tmp/autoworker

# 2. In your target repo
cd <your-target-repo>

# 3. Parameters
PROJECT_NAME="MyService"
REPO_SLUG="myorg/myrepo"
SETUP="claude_code_github_actions"   # see setups/README.md
CRON_CADENCE='0 */3 * * *'
CRON_CADENCE_LOOP='5 */3 * * *'      # 5 min offset (loop also triggers
                                     # from data ingest's workflow_run)
CRON_CADENCE_HUMAN='3h'
TRACKER_ISSUE_NUMBER="0"             # filled after step 6

substitute() {
  sed \
    -e "s|{{PROJECT_NAME}}|${PROJECT_NAME}|g" \
    -e "s|{{REPO_SLUG}}|${REPO_SLUG}|g" \
    -e "s|{{SETUP}}|${SETUP}|g" \
    -e "s|{{CRON_CADENCE}}|${CRON_CADENCE}|g" \
    -e "s|{{CRON_CADENCE_LOOP}}|${CRON_CADENCE_LOOP}|g" \
    -e "s|{{CRON_CADENCE_HUMAN}}|${CRON_CADENCE_HUMAN}|g" \
    -e "s|{{TRACKER_ISSUE_NUMBER}}|${TRACKER_ISSUE_NUMBER}|g"
}

# 4. Render core docs
mkdir -p .github/workflows .github/scripts/autoworker_sources .autoworker
substitute < /tmp/autoworker/templates/MASTER_DIRECTIVES.md > MASTER_DIRECTIVES.md
substitute < /tmp/autoworker/templates/RUNBOOK.md           > RUNBOOK.md
substitute < /tmp/autoworker/templates/UPGRADE_BACKLOG.md   > UPGRADE_BACKLOG.md
substitute < /tmp/autoworker/LOOP_PROMPT.md                 > LOOP_PROMPT.md

# 5. Render the data ingest workflow + script (always)
substitute < /tmp/autoworker/templates/data_ingest.yml      > .github/workflows/autoworker_data.yml
cp /tmp/autoworker/templates/data_ingest.py                   .github/scripts/autoworker_data_ingest.py

# 5b. If SETUP ends in "_github_actions", render the loop workflow too.
case "$SETUP" in
  *_github_actions)
    substitute < /tmp/autoworker/templates/loop_workflow.yml > .github/workflows/autoworker_loop.yml
    # Then open setups/${SETUP}.md and paste the "GitHub Actions
    # invocation" YAML block into the {{AGENT_INVOCATION}} slot in
    # the rendered .github/workflows/autoworker_loop.yml.
    ;;
esac

# Copy the enabled data source modules
for src in github_signals diagnostics_endpoint social_reddit; do
  cp /tmp/autoworker/templates/sources/${src}.py .github/scripts/autoworker_sources/
done
cp /tmp/autoworker/templates/sources/README.md .github/scripts/autoworker_sources/

# 6. Edit MASTER_DIRECTIVES.md §§1–§8 — especially §8.
#    Autopilot stays in monitor-only mode while §8 is blank.

# 7. Append setups/${SETUP}.md's "Config snippet" section to your
#    agent-config file (CLAUDE.md for Claude Code setups, AGENTS.md for
#    Codex / Antigravity setups). Create the file if absent.

# 8. Configure data sources
cat > .autoworker/sources.yml <<'EOF'
enabled:
  - github_signals:
      labels: [bug, regression, urgent]
  # - diagnostics_endpoint:
  #     endpoint: /api/diagnostics
  # - social_reddit:
  #     query: "MyService"
EOF

cat > .autoworker/config.yml <<EOF
setup: ${SETUP}
cadence: '${CRON_CADENCE}'
archive_branch: false   # set true to push pre-deletion snapshots of
                        # autopilot-removed code to the autoworker-archive
                        # branch in addition to normal git history.
EOF

# 9. Create the tracker issue
gh issue create \
  --title "[autoworker] Tracker" \
  --label "autoworker-tracker" \
  --body "Initial — awaiting first ingest run."
# Note the number. Set TRACKER_ISSUE_NUMBER and re-run the substitute
# step against MASTER_DIRECTIVES.md, RUNBOOK.md, LOOP_PROMPT.md, and
# the agent-config snippet.

# 10. Set repo secrets per setups/${SETUP}.md.
#     - Actions-based setups always need the agent API key
#       (ANTHROPIC_API_KEY / OPENAI_API_KEY / ...).
#     - External-scheduler setups (web Routines, CLI /loop, Codex
#       cloud, Antigravity) use the platform's account auth, so no
#       agent key in the repo.
#     - Source-specific: BOT_URL + DIAGNOSTICS_TOKEN, X_BEARER_TOKEN, etc.
gh secret set ANTHROPIC_API_KEY --body "<your-key>"  # example

# 11. Commit + PR
git checkout -b autoworker/install
git add MASTER_DIRECTIVES.md RUNBOOK.md UPGRADE_BACKLOG.md LOOP_PROMPT.md \
        CLAUDE.md AGENTS.md .autoworker/ .github/
git commit -m "Install AutoWorker"
git push -u origin autoworker/install
gh pr create --fill

# 12. For external-scheduler setups: after the PR merges, follow the
# "Operator setup steps" section in setups/${SETUP}.md to wire the
# loop in your platform's scheduler (claude.ai/code Routines, Codex
# cloud task, Antigravity scheduled task, or local /loop session).
```

After the PR merges:

- Actions-based setups: the next cron tick runs ingest → tracker
  update → agent loop pass. Done.
- External-scheduler setups: follow the platform-specific steps in
  `setups/<SETUP>.md` to register the loop. Once registered, the data
  ingest cron and the platform's scheduler both fire on cadence.

Operator workload from then on: review the PR stream the agent opens.

## Prerequisites

- **An agent** — Claude Code, Codex (CLI or cloud), Antigravity, or any
  CLI agent you've written a setup for.
- **API key / account auth** — depends on chosen setup; check
  `setups/<SETUP>.md` for what's needed.
- **GitHub Actions enabled** on the repo (for at least the data
  ingest workflow; Actions-based setups need it for the loop too).
- **A filled `MASTER_DIRECTIVES.md` §8** — without it the autopilot
  stays in monitor-only mode.
- **Optionally**: a diagnostics endpoint if you enable
  `diagnostics_endpoint`. Otherwise the `github_signals` +
  `social_reddit` sources work standalone.

## Uninstall

```bash
rm MASTER_DIRECTIVES.md RUNBOOK.md UPGRADE_BACKLOG.md LOOP_PROMPT.md
rm -rf .autoworker
rm .github/workflows/autoworker_data.yml
rm -f .github/workflows/autoworker_loop.yml   # only if installed
rm -rf .github/scripts/autoworker_sources
rm .github/scripts/autoworker_data_ingest.py

# Remove the AutoWorker section from your agent-config file (keep any
# other operator preferences).

# If you wired an external scheduler (web Routine, Codex cloud task,
# Antigravity task, local /loop session) — stop / delete it there too.

gh issue close <tracker-issue-number>
gh secret delete ANTHROPIC_API_KEY   # whichever keys you set
```
