# Setup: Claude Code — GitHub Actions cron

**Agent:** Anthropic Claude Code (CLI mode).
**Scheduler:** GitHub Actions cron (`autoworker_loop.yml`).

Pick this for unattended production. The loop survives machine
reboots, doesn't depend on a session staying open, and runs entirely
on GitHub-managed infrastructure.

## What gets installed

- `autoworker_data.yml` — data ingest cron.
- **`autoworker_loop.yml`** — the agent loop cron (this is the
  setup-defining file).
- Source modules under `.github/scripts/autoworker_sources/`.
- `LOOP_PROMPT.md` at repo root (the workflow feeds it to `claude
  --print` on every tick).
- `MASTER_DIRECTIVES.md`, `RUNBOOK.md`, `UPGRADE_BACKLOG.md` at root.
- Config snippet appended to `CLAUDE.md`.

## GitHub Actions invocation

The install procedure substitutes this YAML block into
`autoworker_loop.yml`'s `{{AGENT_INVOCATION}}` slot:

```yaml
      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code

      - name: Run one AutoWorker pass
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          claude --print \
            --permission-mode acceptEdits \
            --allowed-tools "Bash,Read,Edit,Write,Grep,Glob,mcp__github__*" \
            < LOOP_PROMPT.md
```

## Secrets required

- `ANTHROPIC_API_KEY` — your Anthropic API key (set as repo secret).
- Source-specific secrets if enabled (`BOT_URL`, `DIAGNOSTICS_TOKEN`,
  `X_BEARER_TOKEN`, etc.).

## Operator setup steps (after the install PR merges)

1. Set `ANTHROPIC_API_KEY` as a repo secret:
   Settings → Secrets and variables → Actions → New repository secret.
2. Set any source-specific secrets the install PR description lists.
3. Verify the workflow appears under **Actions** in the GitHub UI.
4. Optional: trigger one pass manually via **Actions → AutoWorker
   loop → Run workflow** to confirm everything's wired before the
   first scheduled tick.

That's it — no other platform to configure. The next scheduled tick
runs data ingest → tracker update → agent loop pass.

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

- Claude Code's `mcp__github__*` tools handle issues + PRs without
  needing `gh` installed in the runner.
- For long passes (>30 min), raise the workflow's `timeout-minutes`
  and add `--max-turns` to the CLI.
- The `acceptEdits` permission mode is the right balance for
  unattended runs: file edits go through, destructive shell commands
  still prompt (and in CI mode, the workflow fails rather than
  hanging — which is the correct behaviour).
