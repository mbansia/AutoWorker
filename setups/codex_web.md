# Setup: OpenAI Codex (cloud / web tasks)

**Agent:** OpenAI Codex (cloud — typically accessed via ChatGPT's
Codex tasks UI).
**Scheduler:** external — Codex cloud's task scheduler.

Pick this for a ChatGPT-native flow where the loop is configured and
monitored alongside your other Codex tasks.

## What gets installed

- `autoworker_data.yml` — data ingest cron (GitHub Actions).
- Source modules under `.github/scripts/autoworker_sources/`.
- `LOOP_PROMPT.md` at repo root.
- `MASTER_DIRECTIVES.md`, `RUNBOOK.md`, `UPGRADE_BACKLOG.md` at root.
- Config snippet appended to `AGENTS.md`.

**Not installed:** `autoworker_loop.yml`. The Codex cloud task
replaces it.

## Secrets to set in the repo

- Source-specific secrets only (the Codex cloud task uses your
  OpenAI account auth, not a repo secret).

## Operator setup steps (after the install PR merges)

1. Sign in to ChatGPT and open the **Codex** product (under "Tools"
   or the Codex tab in the sidebar — exact location varies as the UI
   evolves).
2. Connect your project repo if it isn't already.
3. Create a new scheduled task / cloud task:
   - **Name:** `AutoWorker loop — <project name>`.
   - **Repository:** your project repo, branch `main`.
   - **Schedule:** match the `CRON_CADENCE` you chose at install.
   - **Prompt:** open `LOOP_PROMPT.md` from the repo and copy the
     entire prompt block (between the triple-backtick fences) into
     the task's prompt field. All `{{...}}` placeholders are already
     substituted.
   - **Sandbox / permissions:** workspace-write (allows file edits +
     git push). Confirm the task is allowed to open + merge PRs.
4. Run the task once manually. Verify:
   - The tracker issue gets an update (or a comment).
   - No errors in the task's run log.
5. Save. The task fires automatically on the schedule.

## Config snippet — append to AGENTS.md

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

- Codex cloud tasks have per-task duration limits; if a pass would
  exceed it, the task fails and the next tick retries from a clean
  state.
- The UI evolves — if a field name changes, the mapping above is
  conceptual (schedule = cron equivalent; prompt = the LOOP_PROMPT
  body; sandbox = workspace-write).
- For unattended-by-default with no UI dependency, prefer
  `codex_cli_github_actions`.
