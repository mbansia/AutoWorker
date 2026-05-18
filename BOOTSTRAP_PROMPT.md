# Bootstrap prompt — `import AutoWorker`

Paste the block below into a fresh agent session opened in your target
repo (Claude Code, Codex CLI, or any other CLI agent you're using).
The agent fetches this template, asks you a handful of parameters,
renders templates into your repo, sets up two crons + a tracker issue,
and opens a PR you can review + merge.

The bootstrap is a one-time operation per target repo. After it merges,
day-to-day operation is automatic — the data ingest cron and the loop
cron run on their schedule and the agent ships PRs you review at your
own pace.

---

```
You are installing the AutoWorker pattern into THIS repo.
Template source: https://github.com/mbansia/AutoWorker

Steps:

1. Fetch the template. Read README, SETUP.md, LOOP_PROMPT.md, every
   file under templates/, and every file under adapters/.

2. Ask the operator the following parameters, ONE at a time, using
   the AskUserQuestion tool (or your agent's equivalent), with sensible
   defaults proposed:

   - PROJECT_NAME (display name, e.g. "Acme")
   - REPO_SLUG (owner/name; autodetect from `git remote -v` if possible)
   - PRIMARY_GOAL (one-line outcome, e.g. "grow WAU 10% per quarter")
   - ADAPTER (one of: claude_code, codex, generic). Default: whichever
     agent is running this prompt.
   - CRON_CADENCE (cron expression for the data ingest workflow).
     Default: '0 */3 * * *' (every 3 hours). Loop workflow runs
     immediately after via workflow_run.
   - ENABLED_SOURCES (multi-select):
       * diagnostics_endpoint (needs BOT_URL + DIAGNOSTICS_TOKEN)
       * github_signals (no secrets needed beyond GITHUB_TOKEN)
       * social_reddit (no secrets needed)
       Default: github_signals only (safest minimum).
   - HAS_EXISTING_DIRECTIVES_DOC (Y/N). If Y, ask SSOT_PATH and have
     the agent reference it FROM MASTER_DIRECTIVES.md instead of
     duplicating. If N, the agent scaffolds MASTER_DIRECTIVES.md fresh
     and tells the operator to fill §§1–§8.

3. Render the templates with those parameters into the target repo:

   templates/MASTER_DIRECTIVES.md  → MASTER_DIRECTIVES.md
   templates/RUNBOOK.md            → RUNBOOK.md
   templates/UPGRADE_BACKLOG.md    → UPGRADE_BACKLOG.md
   templates/data_ingest.yml       → .github/workflows/autoworker_data.yml
   templates/data_ingest.py        → .github/scripts/autoworker_data_ingest.py
   templates/loop_workflow.yml     → .github/workflows/autoworker_loop.yml
   templates/sources/<name>.py     → .github/scripts/autoworker_sources/<name>.py
                                     (one per ENABLED_SOURCES)
   templates/sources/README.md     → .github/scripts/autoworker_sources/README.md

   Substitute throughout:
     {{PROJECT_NAME}}, {{REPO_SLUG}}, {{CRON_CADENCE}},
     {{CRON_CADENCE_HUMAN}}, {{CRON_CADENCE_LOOP}},
     {{TRACKER_ISSUE_NUMBER}}, {{ADAPTER}}

   For {{CRON_CADENCE_LOOP}}, use the same cron as CRON_CADENCE but
   offset by 5 minutes (the data ingest workflow's `workflow_run`
   event will trigger the loop on success regardless).

   Append the chosen adapter's config snippet (`adapters/<ADAPTER>.md`,
   "Config snippet" section) to the operator's agent-config file
   (CLAUDE.md for claude_code, AGENTS.md for codex, etc.). Create the
   file if absent.

   Substitute the adapter's "GitHub Actions invocation" YAML into the
   loop_workflow.yml's `{{AGENT_INVOCATION}}` slot.

4. Render `.autoworker/sources.yml` from ENABLED_SOURCES. Example:

       enabled:
         - github_signals:
             labels: [bug, regression, urgent]

   Also write `.autoworker/config.yml` recording the chosen adapter:

       adapter: {{ADAPTER}}
       cadence: {{CRON_CADENCE}}

5. Render LOOP_PROMPT.md (this template repo's root file) with all
   placeholders substituted, save it at the target repo's root as
   LOOP_PROMPT.md. The cron workflow reads it on every tick.

6. Create the persistent tracker issue via the agent's GitHub tool:
       title: "[autoworker] Tracker"
       labels: ["autoworker-tracker"]
       body: "Initial — awaiting first ingest run."
   Record the issue number. Substitute {{TRACKER_ISSUE_NUMBER}} into
   the rendered RUNBOOK.md, MASTER_DIRECTIVES.md, LOOP_PROMPT.md, and
   the agent-config snippet.

7. Open a PR (branch `autoworker/install`) with everything from steps
   3–5. Title: "Install AutoWorker". Body:
   - Summary: agent name, dimensions enabled, cadence, sources.
   - Operator next-steps:
       a. Set repo secrets (which depends on chosen adapter + sources).
       b. Fill MASTER_DIRECTIVES.md §§1–§8 (especially the §8
          never-autoship list — autopilot is unsafe without it).
       c. Merge this PR. The crons start on the next scheduled tick.

8. Output a short summary to the operator:
   - "Created tracker issue #X."
   - "Opened install PR #Y."
   - "After merge, set these secrets: ..."
   - "First scheduled run: <time>."

Constraints:
- Do NOT install anything that touches the operator's application
  code. Only AutoWorker files.
- Do NOT push directly to main. PR only.
- If the target repo has neither a CLAUDE.md / AGENTS.md nor a
  directives doc and the operator selected ENABLED_SOURCES that
  include diagnostics_endpoint, STOP and ask: "Diagnostics endpoint
  requires a service to poll. Do you have one running? If not, prefer
  github_signals + social_reddit only."
- If MASTER_DIRECTIVES.md §8 is left blank after rendering, post a
  loud warning comment on the install PR: "Autopilot will not run
  until §8 is filled. The loop will stay in monitor-only mode."
```
