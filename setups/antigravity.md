# Setup: Google Antigravity

**Agent:** Google Antigravity.
**Scheduler:** external — Antigravity's native task scheduler.

Pick this for a Google-native flow.

## What gets installed

- `autoworker_data.yml` — data ingest cron (GitHub Actions).
- Source modules under `.github/scripts/autoworker_sources/`.
- `LOOP_PROMPT.md` at repo root.
- `MASTER_DIRECTIVES.md`, `RUNBOOK.md`, `UPGRADE_BACKLOG.md` at root.
- Config snippet appended to your Antigravity project's agent-config
  file (typically `AGENTS.md` at the repo root or the equivalent the
  product uses — verify in the current Antigravity docs).

**Not installed:** `autoworker_loop.yml`. The Antigravity scheduled
task replaces it.

## Secrets to set

- Antigravity uses your Google account auth for the agent; no separate
  API key needs to live in the repo.
- Source-specific secrets only (if you enabled sources that need
  them).

## Operator setup steps (after the install PR merges)

1. Open Antigravity (sign in with your Google account).
2. Connect your project repo to Antigravity if it isn't already.
3. Create a scheduled / recurring task:
   - **Name:** `AutoWorker loop — <project name>`.
   - **Repository:** your project repo, branch `main`.
   - **Cadence:** match the `CRON_CADENCE` from install.
   - **Prompt:** open `LOOP_PROMPT.md` from the repo and copy the
     entire prompt block (between the triple-backtick fences) into
     the task's prompt field.
   - **Permissions:** allow file edits, git commit + push, and PR
     creation + merge on `autoworker/*` branches.
4. Run once manually to verify the first pass.
5. Save and let it run on schedule.

## Config snippet — append to AGENTS.md (or the file Antigravity reads)

```markdown
## AutoWorker sessions

If a session is invoked to "do an AutoWorker pass", "run the loop",
"monitor the tracker", or any variant — follow `RUNBOOK.md`. The
runbook describes the two-part pass: read `MASTER_DIRECTIVES.md` →
fetch tracker issue #{{TRACKER_ISSUE_NUMBER}} → classify per the
action matrix → optional autopilot upgrade.

## PR autonomy (AutoWorker scope only)

Pre-authorised to create and merge pull requests within AutoWorker
scope without prompting. Hard never-list:

- Never push directly to `main`.
- Never `--no-verify`, force-push, or destructive shell.
- Never touch credentials.
- Never edit `MASTER_DIRECTIVES.md` §§1–§8 (only §9 is append-only).
- Never cross §8's never-autoship list.
- Branch names: `autoworker/<short-slug>`.

## Master directives

`MASTER_DIRECTIVES.md` is binding. Honour §0.5 (CTO + PM + CEO + QA +
Marketer persona) and §0.6 (respect project prefs, five-pass persona
audit before merging, new branch always, `[ ]` / `[x]` checklists)
on every pass.
```

## Notes

- Antigravity's UI evolves; the operator steps above are conceptual.
  If a field name differs, the mapping is: schedule = cron equivalent;
  prompt = the LOOP_PROMPT body; permissions = file write + git push +
  GitHub PR write.
- Confirm in the current Antigravity docs which agent-config file the
  product reads. Some installs use `AGENTS.md`; others have a
  project-level `.agents/` directory.
