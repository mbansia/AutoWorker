# Setup: Claude Code (CLI) — `/loop`

**Agent:** Anthropic Claude Code, local CLI (`claude`).
**Scheduler:** external — the CLI's built-in `/loop` skill (interactive
session must stay alive).

Pick this for dev / testing on your own machine. The loop dies when
the CLI session closes, so it's not ideal for unattended production.
For production prefer `claude_code_github_actions`.

## What gets installed

- `autoworker_data.yml` — data ingest cron (GitHub Actions).
- Source modules under `.github/scripts/autoworker_sources/`.
- `LOOP_PROMPT.md` at repo root.
- `MASTER_DIRECTIVES.md`, `RUNBOOK.md`, `UPGRADE_BACKLOG.md` at root.
- Config snippet appended to `CLAUDE.md`.

**Not installed:** `autoworker_loop.yml`. The local `/loop` session
replaces it.

## Secrets to set

- Local Anthropic auth (run `claude` once and sign in).
- Repo: same as `claude_code_web` (`GITHUB_TOKEN` auto-provided;
  source-specific secrets only if you enabled them).

## Operator setup steps (after the install PR merges)

1. Clone or `cd` into your project repo locally.
2. Start Claude Code: `claude` (then sign in if you haven't).
3. At the Claude Code prompt, run:

   ```
   /loop {{CRON_CADENCE_HUMAN}}
   ```

   Then paste the entire prompt block from `LOOP_PROMPT.md` (the
   content between the triple-backtick fences).

   `{{CRON_CADENCE_HUMAN}}` is the human form of your cadence
   (`3h`, `30m`, `6h`, etc.) that the install procedure substituted
   for you.

4. The session runs the first pass immediately, then sleeps until
   the next tick. Keep the terminal open.

5. To stop the loop: `Ctrl-C` or `/exit`. To resume, re-run the
   `/loop` command.

## Config snippet — append to CLAUDE.md

```markdown
## AutoWorker sessions

If a session is invoked to "do an AutoWorker pass", "run the loop",
"monitor the tracker", or any variant — follow `RUNBOOK.md`. The
runbook describes the two-part pass: read `MASTER_DIRECTIVES.md` →
fetch tracker issue #{{TRACKER_ISSUE_NUMBER}} → classify per the
action matrix → optional autopilot upgrade.

## PR autonomy (AutoWorker scope only)

Pre-authorised to create AND merge pull requests within the
AutoWorker scope without asking. Hard never-list:

- Never push directly to main.
- Never `--no-verify`, force-push, or destructive shell.
- Never touch credentials.
- Never edit `MASTER_DIRECTIVES.md` §§1–§8 (only §9 is append-only).
- Never cross the never-autoship list in §8.
- Branch names: `autoworker/<short-slug>`.

## Master directives

`MASTER_DIRECTIVES.md` is binding. Honour §0.5 (CTO + PM + CEO + QA +
Marketer persona) and §0.6 (respect project prefs, five-pass persona
audit before merging, new branch always, `[ ]` / `[x]` checklists)
on every pass.
```

## Notes

- The session uses your local file system to commit and push — make
  sure your `git` is configured with credentials that can push to
  `autoworker/*` branches and open + merge PRs.
- If your machine sleeps or reboots, the loop pauses. Restart with
  the same `/loop` command.
- The `acceptEdits` permission mode is recommended (file edits go
  through automatically; destructive shell still prompts).
