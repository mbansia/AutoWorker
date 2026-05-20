# Setup: any CLI agent — GitHub Actions cron

**Agent:** any coding-agent CLI not covered above.
**Scheduler:** GitHub Actions cron (`autoworker_loop.yml`).

Use this as a template when adding a new agent. Copy this file to
`setups/<your-agent>_github_actions.md` and fill in the brackets.

## What gets installed

- `autoworker_data.yml` — data ingest cron.
- **`autoworker_loop.yml`** — the agent loop cron.
- Source modules under `.github/scripts/autoworker_sources/`.
- `LOOP_PROMPT.md` at repo root.
- `MASTER_DIRECTIVES.md`, `RUNBOOK.md`, `UPGRADE_BACKLOG.md` at root.
- Config snippet appended to your agent's project config file.

## What the agent needs to do per pass

One pass = one execution of your CLI against `LOOP_PROMPT.md`. The
agent must be able to:

- Read files (`RUNBOOK.md`, `MASTER_DIRECTIVES.md`, `UPGRADE_BACKLOG.md`).
- Run shell commands (the project's test command, `git`).
- Open + merge GitHub PRs (via `gh`, MCP, or its own GitHub integration).
- Exit after one pass — no internal restart loop; GitHub Actions cron
  is the only scheduler.

## GitHub Actions invocation — fill in

The install procedure substitutes this YAML block (with your edits)
into `autoworker_loop.yml`'s `{{AGENT_INVOCATION}}` slot:

```yaml
      - name: Install <your CLI>
        run: |
          # e.g. npm install -g <pkg>
          # or:  curl -L https://example.com/install.sh | sh

      - name: Run one AutoWorker pass
        env:
          <YOUR_AGENT_API_KEY>: ${{ secrets.<YOUR_AGENT_API_KEY> }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          <your-cli> \
            --non-interactive \
            --prompt-file LOOP_PROMPT.md \
            --allow-tools "shell,fs,git,github" \
            --single-pass
```

Replace flags with whatever your CLI accepts. The contract:

| Need | How |
|---|---|
| Run non-interactively | A flag like `--exec`, `--print`, `--ci`. |
| Pass the loop prompt | Stdin redirect, `--prompt-file`, or arg. |
| Permit file edits + shell | A permission flag or sandbox mode. |
| Exit after one pass | Some CLIs loop internally; ensure single-pass mode. |

## Secrets required

- `<YOUR_AGENT_API_KEY>` — whatever your agent needs.
- Source-specific secrets if enabled.

## Operator setup steps (after the install PR merges)

1. Set `<YOUR_AGENT_API_KEY>` as a repo secret.
2. Set source-specific secrets per the install PR description.
3. Optional: trigger one pass manually via **Actions → AutoWorker
   loop → Run workflow**.

## Config snippet — append to your agent's project config file

```markdown
## AutoWorker sessions

If a session is invoked to "do an AutoWorker pass", "run the loop",
or "monitor the tracker" — follow `RUNBOOK.md`. The runbook describes
a two-part pass: read `MASTER_DIRECTIVES.md` → fetch tracker issue
#{{TRACKER_ISSUE_NUMBER}} → classify per the action matrix → optional
single-PR upgrade.

## PR autonomy (AutoWorker scope only)

Pre-authorised to create + merge PRs within AutoWorker scope without
asking. Hard never-list:

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

## Verification checklist before tagging your setup ready

- [ ] A dry-run pass against a non-critical repo completes without
      hanging or prompting for input.
- [ ] The agent honours `MASTER_DIRECTIVES.md` §8 (put "do not touch
      X" in §8 and verify the agent skips).
- [ ] The agent exits cleanly (no zombie processes).
- [ ] `git push` + PR creation + merge succeed inside the runner.
- [ ] The agent posts the five-pass persona audit verdicts in the
      PR description.
