# Adapter: Claude Code

[Claude Code](https://docs.claude.com/en/docs/claude-code) is Anthropic's
official agentic CLI. AutoWorker uses it in two modes:

- **Interactive `/loop`** — fastest path for local development. Paste
  `LOOP_PROMPT.md` into a Claude Code session prefixed with
  `/loop {{CRON_CADENCE_HUMAN}}`. The session keeps running passes on
  the cadence until you stop it.
- **GitHub Actions cron** — recommended for production. The workflow
  invokes `claude --print` against the loop prompt on every tick.

## GitHub Actions invocation

Drop this into `loop_workflow.yml`'s `{{AGENT_INVOCATION}}` slot:

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

The `LOOP_PROMPT.md` in your repo has placeholders already substituted
by the bootstrap (PROJECT_NAME, REPO_SLUG, TRACKER_ISSUE_NUMBER, etc.).
`claude --print` reads it from stdin, runs one pass, prints the final
turn, exits.

## Secrets required

- `ANTHROPIC_API_KEY` — your Anthropic API key, or use a Claude
  subscription auth flow per the docs.

## Config snippet — append to CLAUDE.md

```markdown
## AutoWorker sessions

If a session is invoked to "do an AutoWorker pass", "run the loop",
"monitor the tracker", or any variant — follow `RUNBOOK.md`. That file
describes the two-part pass: read `MASTER_DIRECTIVES.md` → fetch
tracker issue #{{TRACKER_ISSUE_NUMBER}} → classify per the action
matrix → optional autopilot upgrade from defined surfaces.

To run on a schedule locally: `/loop {{CRON_CADENCE_HUMAN}}
"do an AutoWorker pass per RUNBOOK.md"`.

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
  Founder CEO + Marketer simultaneously. Surface trade-offs when
  the lenses conflict.
- **§0.6 — operating principles.** Respect existing project preferences
  (this file overrides AutoWorker defaults), double-audit before
  committing (correctness pass + multi-lens pass), new branch per piece
  of work, track work in `[ ]` / `[x]` checklist form.
```

## Notes

- Claude Code's `mcp__github__*` tools handle issues + PRs without
  needing `gh` installed in the runner.
- For long-running passes that exceed 30 min, raise the workflow's
  `timeout-minutes` and add `--max-turns` to the CLI.
- The `acceptEdits` permission mode is the right balance for unattended
  runs: file edits go through, destructive shell commands still prompt.
