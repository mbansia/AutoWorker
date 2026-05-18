# Setup

The fast path is [`BOOTSTRAP_PROMPT.md`](BOOTSTRAP_PROMPT.md) — paste it
into an agent session in your target repo. The agent renders templates,
creates the tracker issue, wires the crons, and opens a PR. ~5 minutes.

This file documents the manual install for operators who want to do it
themselves or audit each step.

## What gets installed in your target repo

```
MASTER_DIRECTIVES.md                            # the binding spec (root)
RUNBOOK.md                                      # operational procedure (root)
UPGRADE_BACKLOG.md                              # operator hint box (root)
LOOP_PROMPT.md                                  # rendered, fed to the agent each pass

CLAUDE.md  / AGENTS.md  (per chosen adapter)    # merged or created

.autoworker/
  config.yml                                    # adapter + cadence
  sources.yml                                   # enabled data sources

.github/
  workflows/
    autoworker_data.yml                         # data ingest cron
    autoworker_loop.yml                         # agent loop cron
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
ADAPTER="claude_code"           # or codex / generic
CRON_CADENCE='0 */3 * * *'
CRON_CADENCE_LOOP='5 */3 * * *' # 5 min offset; loop also triggers from
                                # data ingest's workflow_run
CRON_CADENCE_HUMAN='3h'
TRACKER_ISSUE_NUMBER="0"        # filled after step 6

substitute() {
  sed \
    -e "s|{{PROJECT_NAME}}|${PROJECT_NAME}|g" \
    -e "s|{{REPO_SLUG}}|${REPO_SLUG}|g" \
    -e "s|{{ADAPTER}}|${ADAPTER}|g" \
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

# 5. Render workflows + scripts
substitute < /tmp/autoworker/templates/data_ingest.yml      > .github/workflows/autoworker_data.yml
cp /tmp/autoworker/templates/data_ingest.py                   .github/scripts/autoworker_data_ingest.py
substitute < /tmp/autoworker/templates/loop_workflow.yml    > .github/workflows/autoworker_loop.yml

# Copy the enabled data source modules
for src in github_signals diagnostics_endpoint social_reddit; do
  cp /tmp/autoworker/templates/sources/${src}.py .github/scripts/autoworker_sources/
done
cp /tmp/autoworker/templates/sources/README.md .github/scripts/autoworker_sources/

# 6. Edit MASTER_DIRECTIVES.md §§1–§8 — especially §8.
#    Autopilot stays in monitor-only mode while §8 is blank.

# 7. Adapter wiring — open adapters/${ADAPTER}.md from the template repo
#    a. Copy the "GitHub Actions invocation" YAML block into the
#       loop_workflow.yml's `{{AGENT_INVOCATION}}` placeholder.
#    b. Append the "Config snippet" section to your agent-config file
#       (CLAUDE.md or AGENTS.md — create if absent).

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
adapter: ${ADAPTER}
cadence: '${CRON_CADENCE}'
EOF

# 9. Create the tracker issue
gh issue create \
  --title "[autoworker] Tracker" \
  --label "autoworker-tracker" \
  --body "Initial — awaiting first ingest run."
# Note the number. Set TRACKER_ISSUE_NUMBER and re-run the substitute
# step against MASTER_DIRECTIVES.md, RUNBOOK.md, LOOP_PROMPT.md, and
# the agent-config snippet.

# 10. Set the secrets you need
#     - Always: agent API key (ANTHROPIC_API_KEY / OPENAI_API_KEY / ...)
#     - diagnostics_endpoint: BOT_URL, DIAGNOSTICS_TOKEN
#     - X social: X_BEARER_TOKEN
gh secret set ANTHROPIC_API_KEY --body "<your-key>"

# 11. Commit + PR
git checkout -b autoworker/install
git add MASTER_DIRECTIVES.md RUNBOOK.md UPGRADE_BACKLOG.md LOOP_PROMPT.md \
        CLAUDE.md AGENTS.md  .autoworker/ .github/
git commit -m "Install AutoWorker"
git push -u origin autoworker/install
gh pr create --fill
```

After the PR merges, the next cron tick runs ingest → tracker update →
loop pass. Operator workload is reviewing the PR stream the agent
opens.

## Prerequisites

- **An agent CLI** — Claude Code, Codex CLI, or any CLI agent you've
  written an adapter for.
- **A coding-agent API key**, set as a repo secret (the adapter docs
  list the name).
- **GitHub Actions enabled** on the repo.
- **A filled MASTER_DIRECTIVES.md §8** — without it the autopilot stays
  in monitor-only mode. (Monitoring still works, but the agent won't
  ship.)
- **Optionally**: a diagnostics endpoint if you want
  `diagnostics_endpoint` source. Otherwise the `github_signals` +
  `social_reddit` sources work standalone.

## What happens after install

- **Data ingest cron** (`autoworker_data.yml`) fires on schedule. Polls
  each enabled source, aggregates results, updates the `[autoworker]
  Tracker` issue body, posts a heartbeat comment.
- **Loop cron** (`autoworker_loop.yml`) triggers on `workflow_run`
  immediately after ingest succeeds (or on its own schedule as a
  fallback). The agent reads directives + tracker, runs one pass,
  comments / opens PR / stays quiet.
- **Operator** reviews the PR stream in their normal workflow. Hints
  go in `UPGRADE_BACKLOG.md`. Directive changes go in
  `MASTER_DIRECTIVES.md` §§1–§8 (the agent honours them on the next
  pass). Pushback (unmerge, disagree-comment, manual revert) triggers
  a 3-pass autopilot cooldown.

## Uninstall

```bash
rm MASTER_DIRECTIVES.md RUNBOOK.md UPGRADE_BACKLOG.md LOOP_PROMPT.md
rm -rf .autoworker
rm .github/workflows/autoworker_data.yml .github/workflows/autoworker_loop.yml
rm -rf .github/scripts/autoworker_sources
rm .github/scripts/autoworker_data_ingest.py

# Remove the AutoWorker section from your agent-config file (keep
# any other operator preferences).

gh issue close <tracker-issue-number>
gh secret delete ANTHROPIC_API_KEY  # whichever agent key you used
```
