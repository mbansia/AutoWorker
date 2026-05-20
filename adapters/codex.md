# Adapter: OpenAI Codex CLI

[Codex CLI](https://github.com/openai/codex) is OpenAI's agentic coding
CLI. AutoWorker uses it via its non-interactive `exec` mode in a GitHub
Actions cron.

## GitHub Actions invocation

Drop this into `loop_workflow.yml`'s `{{AGENT_INVOCATION}}` slot:

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

`codex exec` runs the agent non-interactively against the prompt,
performs the pass, and exits.

## Secrets required

- `OPENAI_API_KEY` — your OpenAI API key, or sign in via the
  ChatGPT-account flow per the Codex docs and persist the credential.

## Config snippet — append to AGENTS.md

```markdown
## AutoWorker sessions

If a session is invoked to "do an AutoWorker pass", "run the loop",
"monitor the tracker", or any variant — follow `RUNBOOK.md`. The
runbook describes a two-part pass: read `MASTER_DIRECTIVES.md` →
fetch the tracker issue #{{TRACKER_ISSUE_NUMBER}} → classify per the
action matrix → optionally ship one upgrade PR.

## PR autonomy (AutoWorker scope only)

You are pre-authorised to create and merge pull requests within the
AutoWorker scope without prompting. Hard never-list:

- Never push directly to `main`.
- Never `--no-verify`, force-push, or run destructive shell.
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

- Codex's `workspace-write` sandbox is the right level for unattended
  runs: writes are allowed in the workspace; network and arbitrary
  shell still require explicit allowlisting.
- To open + merge PRs, the runner needs the `gh` CLI (preinstalled on
  GitHub-hosted Ubuntu runners) and a token with `pull-requests:
  write`. The workflow grants this in its top-level `permissions:`
  block.
- For long passes, raise the workflow's `timeout-minutes`.
