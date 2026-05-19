# Adapter: generic CLI agent

A template for wiring any agentic coding CLI to AutoWorker. Copy this
file to `adapters/<your-agent>.md` and fill in the bracketed slots.

## What the agent must do

One pass = one execution of the agent CLI against `LOOP_PROMPT.md` as
the system / user prompt. The agent needs to be able to:

- Read files in the checkout (RUNBOOK.md, MASTER_DIRECTIVES.md,
  UPGRADE_BACKLOG.md).
- Run shell commands (the project's test command, git).
- Read and write GitHub issues + PRs (via `gh` CLI, MCP, or its own
  GitHub integration).
- Stop after one pass — no auto-restart inside the agent itself; the
  scheduler is GitHub Actions cron.

## GitHub Actions invocation

Drop this into `loop_workflow.yml`'s `{{AGENT_INVOCATION}}` slot:

```yaml
      - name: Install <your agent CLI>
        run: |
          # e.g. curl -L https://example.com/install.sh | sh
          # or:  npm install -g <pkg>

      - name: Run one AutoWorker pass
        env:
          <YOUR_AGENT_API_KEY>: ${{ secrets.<YOUR_AGENT_API_KEY> }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          <your-agent-cli> \
            --non-interactive \
            --prompt-file LOOP_PROMPT.md \
            --allow-tools "shell,fs,git,github" \
            --single-pass
```

Replace flags with whatever your CLI accepts. The contract:

| Need                                        | How                                       |
|--------------------------------------------|-------------------------------------------|
| Run non-interactively                      | A flag like `--exec`, `--print`, `--ci`. |
| Pass the loop prompt                       | Stdin redirect, `--prompt-file`, or arg. |
| Permit file edits + shell                  | Permission flag (`--allow-edits`, sandbox).|
| Exit after one pass                        | Some CLIs loop; ensure single-pass mode.   |

## Secrets required

- `<YOUR_AGENT_API_KEY>` — whatever the agent needs.

## Config snippet — append to your agent-config file

Most agents read a project-local config file (`AGENTS.md`, `CLAUDE.md`,
or similar). Append this:

```markdown
## AutoWorker sessions

If a session is invoked to "do an AutoWorker pass", "run the loop",
or "monitor the tracker" — follow `RUNBOOK.md`. The runbook describes
a two-part pass: read `MASTER_DIRECTIVES.md` → fetch tracker issue
#{{TRACKER_ISSUE_NUMBER}} → classify per the action matrix → optional
single-PR upgrade.

## PR autonomy (AutoWorker scope only)

Pre-authorised to create + merge PRs within AutoWorker scope. Hard
never-list:

- Never push directly to `main`.
- Never `--no-verify`, force-push, or destructive shell.
- Never touch credentials.
- Never edit `MASTER_DIRECTIVES.md` §§1–§8 (only §9 is append-only).
- Never cross §8's never-autoship list.
- Branch names: `autoworker/<short-slug>`.

## Master directives

`MASTER_DIRECTIVES.md` is binding. Read on every wake-up before
acting. In particular, honour:

- **§0.5 — operating persona.** Operate as CTO + Product Manager +
  Founder CEO + Marketer simultaneously. Surface trade-offs when
  the lenses conflict.
- **§0.6 — operating principles.** Respect existing project preferences
  (this file overrides AutoWorker defaults), double-audit before
  committing (correctness pass + multi-lens pass), new branch per piece
  of work, track work in `[ ]` / `[x]` checklist form.
```

## Things to verify before tagging your adapter ready

- A dry-run pass against a non-critical repo completes without
  prompting for input.
- The agent respects the `MASTER_DIRECTIVES.md` §8 boundary (test by
  putting "do not autoship X" in §8 and seeing the agent skip).
- The agent exits cleanly (returns to shell) — no zombie processes.
- `git push` + PR creation succeed inside the runner.
