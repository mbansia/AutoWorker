# Setup: OpenAI Codex CLI — GitHub Actions cron

**Agent:** OpenAI Codex CLI (`codex`).
**Scheduler:** GitHub Actions cron (`autoworker_loop.yml`).

Pick this for unattended Codex-driven production.

## What gets installed

- `autoworker_data.yml` — data ingest cron.
- **`autoworker_loop.yml`** — the agent loop cron.
- Source modules under `.github/scripts/autoworker_sources/`.
- `LOOP_PROMPT.md` at repo root.
- `MASTER_DIRECTIVES.md`, `RUNBOOK.md`, `UPGRADE_BACKLOG.md` at root.
- Config snippet appended to `AGENTS.md`.

## GitHub Actions invocation

The install procedure substitutes this YAML block into
`autoworker_loop.yml`'s `{{AGENT_INVOCATION}}` slot:

```yaml
      - name: Install Codex CLI
        run: npm install -g @openai/codex

      - name: Run one AutoWorker pass
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          codex exec \
            --sandbox workspace-write \
            --skip-git-repo-check \
            "$(cat LOOP_PROMPT.md)"
```

## Secrets required

- `OPENAI_API_KEY` — your OpenAI API key (set as repo secret).
- Source-specific secrets if enabled.

## Operator setup steps (after the install PR merges)

1. Set `OPENAI_API_KEY` as a repo secret:
   Settings → Secrets and variables → Actions → New repository secret.
2. Set any source-specific secrets the install PR description lists.
3. Verify the workflow appears under **Actions** in the GitHub UI.
4. Optional: trigger one pass manually via **Actions → AutoWorker
   loop → Run workflow** to confirm everything's wired.

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

- Codex's `workspace-write` sandbox is the right level for unattended
  runs: writes are allowed in the workspace; network and arbitrary
  shell still require explicit allowlisting.
- For long passes, raise the workflow's `timeout-minutes`.
- To open + merge PRs, the runner uses `gh` (preinstalled on
  GitHub-hosted Ubuntu runners) authenticated via `GH_TOKEN`.
