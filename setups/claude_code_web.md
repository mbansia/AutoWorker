# Setup: Claude Code (web) — Routines

**Agent:** Anthropic Claude Code (claude.ai/code).
**Scheduler:** external — the web app's Routines feature.

Pick this when you want a tweakable, browser-based control surface for
the AutoWorker loop. You can change the prompt or cadence on the fly
without editing the repo.

## What gets installed

- `autoworker_data.yml` — data ingest cron (GitHub Actions).
- Source modules under `.github/scripts/autoworker_sources/`.
- `LOOP_PROMPT.md` at repo root — fully rendered, copy-paste-ready.
- `MASTER_DIRECTIVES.md`, `RUNBOOK.md`, `UPGRADE_BACKLOG.md` at root.
- Config snippet appended to `CLAUDE.md`.

**Not installed:** `autoworker_loop.yml`. The web Routine replaces it.

## Secrets to set in the repo

- `GITHUB_TOKEN` is provided automatically; nothing extra needed for
  the data ingest workflow itself.
- For source-specific secrets (only if you enabled the source):
  - `BOT_URL`, `DIAGNOSTICS_TOKEN` (for `diagnostics_endpoint`)
  - `X_BEARER_TOKEN` (for `social_x` if you add it)

## Operator setup steps (after the install PR merges)

1. Open [claude.ai/code](https://claude.ai/code) on the web.
2. Open your project repo's workspace (or connect it if you haven't).
3. Go to **Settings → Routines → New routine**.
4. Configure the routine:
   - **Name:** `AutoWorker loop — <project name>`.
   - **Cadence:** match the `CRON_CADENCE` you chose at install
     (e.g. every 3 hours).
   - **Repository:** your project repo, branch `main`.
   - **Prompt:** open `LOOP_PROMPT.md` from the repo root and copy
     the entire prompt block (between the triple-backtick fences) into
     the routine's prompt field. All `{{...}}` placeholders are
     already substituted by the install procedure.
   - **Permissions:** allow file edits, shell, and GitHub MCP tools
     so the loop can open + merge PRs and comment on the tracker.
5. **Run the routine once manually** to verify the first pass works
   end-to-end. Check that:
   - The tracker issue gets a comment (or stays quiet for an all-clear).
   - No errors appear in the routine's run log.
6. Save. The routine now fires automatically on the cadence.

## Config snippet — append to CLAUDE.md

```markdown
## AutoWorker sessions

If a session is invoked to "do an AutoWorker pass", "run the loop",
"monitor the tracker", or any variant — follow `RUNBOOK.md`. That file
describes the two-part pass: read `MASTER_DIRECTIVES.md` → fetch
tracker issue #{{TRACKER_ISSUE_NUMBER}} → classify per the action
matrix → optional autopilot upgrade from defined surfaces.

## PR autonomy (AutoWorker scope only)

You are pre-authorised to create AND merge pull requests within the
AutoWorker scope without asking. Hard never-list:

- Never push directly to main.
- Never `--no-verify`, force-push, or destructive shell.
- Never touch credentials.
- Never edit `MASTER_DIRECTIVES.md` §§1–§8. Only §9 (learnings) is
  append-only.
- Never cross the never-autoship list in §8.
- Branch names: `autoworker/<short-slug>`.

## Master directives

`MASTER_DIRECTIVES.md` is the binding specification. Read it on every
wake-up before judging signals or planning changes. In particular,
honour:

- **§0.5 — operating persona.** Operate as CTO + Product Manager +
  Founder CEO + QA + Marketer simultaneously. Surface trade-offs when
  the lenses conflict.
- **§0.6 — operating principles.** Respect existing project preferences
  (this file overrides AutoWorker defaults), run a **five-pass persona
  audit** before merging (one independent pass per persona — CTO, PM,
  CEO, QA, Marketer — with the verdicts documented in the PR), new
  branch per piece of work, track work in `[ ]` / `[x]` checklist form.
```

## Notes

- Routines run on Anthropic infrastructure. They use your Anthropic
  account's credentials; no separate API key needs to live in the
  repo for the loop itself.
- If you want the loop to be unattended-by-default and survive any
  web-app changes, prefer `claude_code_github_actions` instead.
- The Routine's prompt is editable from the web — handy for tweaking
  behaviour without a PR. If you edit it, also update `LOOP_PROMPT.md`
  in the repo so the two stay in sync.
