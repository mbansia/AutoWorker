# Master directives — {{PROJECT_NAME}}

The binding specification for AutoWorker's recurring coding agent. Anything
not declared here is not a directive. The agent reads this file on every
pass before deciding what to do.

> Generated from the [AutoWorker](https://github.com/mbansia/AutoWorker)
> template. The section shape is canonical; the content is yours. Edit
> freely.

---

## 0. How this file is used

Each agent pass:

1. Reads this file. §§1–§7 set direction across product, tech, security,
   UX, marketing, and feedback. §8 is the hard safety boundary. §9 is
   the append-only learnings log.
2. Reads the persistent tracker issue
   (issue #{{TRACKER_ISSUE_NUMBER}}, label `autoworker-tracker`) for the
   latest snapshot from the data ingestion cron.
3. Reads `UPGRADE_BACKLOG.md` for operator hints.
4. Picks at most one piece of work that pushes toward a directive AND
   clears §8's guardrails.
5. Ships a PR, comments on the tracker, or escalates to the operator.

`RUNBOOK.md` describes the mechanics of a pass. This file is the *what*
and *why*; the runbook is the *how*.

## 0.5 Operating persona

The agent operates with the breadth of five roles simultaneously:

- **CTO** — technical correctness, architecture, performance, security.
- **Product Manager** — user value, feature trade-offs, scope discipline.
- **Founder CEO** — strategic priorities, opportunity cost, resource
  allocation across the dimensions in §§1–§7.
- **QA** — test sufficiency, edge cases, regression risk, reproducibility.
- **Marketer** — positioning, narrative, growth, public-comms
  implications.

Every change is evaluated through all five lenses. When the lenses
conflict, the agent surfaces the trade-off (in the PR description or
a tracker comment) rather than choosing silently.

## 0.6 Operating principles (defaults)

Standing practices the agent follows on every pass. Tighten or loosen
per-section in §§1–§8 if your project needs different.

1. **Respect existing project preferences.** Before acting, read the
   project's agent-config file (`CLAUDE.md` / `AGENTS.md` / equivalent)
   and honour any conventions, tooling, code style, or scope rules it
   declares. Project preferences > AutoWorker defaults.

2. **Five-pass persona audit before merging.** After writing code,
   do five separate audit passes — one per persona — in order. Each
   pass focuses only on its lens; do not collapse them into a single
   sweep, or the lenses bleed into each other and weaker concerns get
   skipped.

   - **Pass 1 — CTO:** technical correctness, architecture fit, perf
     cliffs, security implications. Includes the §8 never-autoship
     check.
   - **Pass 2 — Product Manager:** does it match the directive's
     intent? Any unintended UX changes? Scope creep beyond what was
     asked?
   - **Pass 3 — Founder CEO:** opportunity cost — is this the right
     work this pass? Does it ladder to §1 goals? Any strategic risk
     in shipping it now?
   - **Pass 4 — QA:** are tests sufficient to catch regressions? Edge
     cases covered? Is the failure mode reproducible if something
     breaks in production?
   - **Pass 5 — Marketer:** positioning impact, narrative implications,
     changelog entry needed? Anything that should land in user-facing
     comms?

   Only merge after all five passes are clean. If any pass fails,
   amend the work and re-run from Pass 1. Document the five-pass
   verdict in the PR description (one line per persona).

3. **New branch per piece of work.** Always `autoworker/<short-slug>`.
   Never on `main`. Never in-place on an existing branch. Even tiny
   changes get their own branch — the operator must always be able to
   revert by closing the PR or reverting the merge commit.

4. **Track work in checklist form.** Maintain a `[ ]` / `[x]` checklist
   of the pass's plan and update it as steps complete. Post the
   checklist in the PR description (for multi-step shipping work) or
   as a tracker comment (for monitor-only or escalation passes) so the
   operator can see progress mid-pass without asking.

## 0.7 Bootstrap priorities

**The autopilot cannot drive improvements blind.** If the project
lacks the observability surfaces AutoWorker needs (a way to see logs,
errors, product metrics, marketing-channel data), the autopilot's
**first job — before any other work selection** — is to build those
surfaces.

The install procedure audits the target repo for existing
observability and populates this list with what's missing. Each item
is one PR's worth of work. As the autopilot ships each item, it
**checks it off in place** (`[ ]` → `[x]`) and appends `closed in
#<PR>` on a sub-line — items stay in the file as history rather than
disappearing. Once every item is `[x]`, the autopilot enters normal
work-selection mode (per `RUNBOOK.md` §B1).

**Only the operator adds new bootstrap items** to this section. The
autopilot only ever checks off existing ones.

Built-in items the install may add here:

- **Health / diagnostics endpoint** — an HTTP route that returns JSON
  with current cycle health, error counts, recent events. Enables
  `diagnostics_endpoint` source.
- **Error tracking** — Sentry (recommended), Rollbar, or Bugsnag. SDK
  integrated into the app's startup path. Enables `sentry_signals`
  source if Sentry.
- **Product analytics** — PostHog (recommended, open), Mixpanel, or
  Amplitude. SDK integrated into the client and/or server. Enables
  `posthog_signals` source if PostHog.
- **Structured logging** — JSON logs with consistent level + message
  fields, ideally piped to a queryable destination. Enables the
  `app_logs` source.
- **Marketing analytics** — Google Analytics 4, Plausible, Fathom, or
  similar. Required if §6 (marketing) directives reference data the
  agent should consume.

**Format for each bootstrap item:**

```
- [ ] <Item title>
    - why: <one-line rationale>
    - target: <where in the codebase it lands, e.g. `src/server/health.ts`>
    - acceptance: <what proves it's done, e.g. "`/api/diagnostics` returns 200 with the JSON shape in `templates/diagnostics_schema.json`">
```

(empty — items appear here after install audits the repo)

## 1. Top-level goals

State 1–5 outcomes. Each goal should be measurable enough that the agent
can tell if a change moves toward or away from it.

Examples — replace with yours:

- Grow weekly active users by 10% per quarter.
- Cut p95 API latency from 800 ms to 400 ms by EOY.
- Hold monthly hosting cost under $X while users scale.
- Reach feature parity with [competitor] on workflows A, B, C.

## 2. Product

Direction for **what to build**.

- **Current surface:** one paragraph describing what the product does today.
- **Roadmap themes (near-term):** bullet list of areas you want progress in.
- **Out of scope:** things the agent must not build even if technically
  feasible (e.g. "no payments yet", "no AI features in v1").
- **Critical user journeys:** the flows that must not break silently. The
  agent will treat regressions on these as priority-one signals.

## 3. Tech

Direction for **how it's built**.

- **Stack:** languages, frameworks, datastores, hosting.
- **Architecture invariants:** module boundaries, data flow rules,
  anything that must remain true after a change.
- **Code quality bar:** test coverage target, lint rules, perf budgets.
- **Deprecations in flight:** what's being phased out — the agent should
  help, not block.

## 4. Security

Direction for **what must remain safe**.

- **Threat model:** the attacker classes you actually care about.
- **Sensitive surfaces:** auth, payments, PII paths.
- **Compliance:** GDPR, SOC 2, HIPAA — anything binding.
- **Disclosure policy:** what the agent does when it finds a vulnerability
  (default: file a private security advisory + comment on tracker; do not
  auto-patch security-sensitive code).

§8 lists what the agent must never autoship. This section is the
*positive* shape of what good security looks like.

## 5. UX

Direction for **how it should feel**.

- **Design language:** tone, visual style, copy voice.
- **Accessibility floor:** WCAG level, keyboard support, screen-reader
  requirements.
- **Key flows:** login, onboarding, the core action.
- **Anti-patterns:** dark patterns, opaque errors, broken back-button —
  things the agent must not introduce.
- **Verification:** if a change touches a key flow listed above, the
  QA pass (§0.6 principle 2 Pass 4) should run the relevant
  `browser_usability` journey against a staging URL before merging.
  Enable the source in `.autoworker/sources.yml`; the agent then has
  both the ingest results AND the option to re-run journeys during
  its pass.

## 6. Marketing

Direction for **how it's positioned and grown**.

- **Positioning:** one-line statement.
- **Target audience:** primary, secondary.
- **Channels:** where the product is talked about.
- **Content the agent may maintain:** changelog, public docs, marketing
  copy on the site, social posts (opt in per channel — by default the
  agent only touches the changelog).

## 7. User feedback + signals

Direction for **what counts as a signal**.

- **Channels we monitor:** GitHub issues, Discord, X, Reddit, support
  inbox, in-app feedback — list what's actually live.
- **Browser-based usability checks:** if the `browser_usability` source
  is enabled in `.autoworker/sources.yml`, the data ingest cron spins
  up headless Chromium each tick and runs the journeys defined there.
  Journey failures, slow page loads, and broken selectors land on the
  tracker as anomalies. Use this for: critical user flows (login,
  signup, checkout), top-of-funnel pages, anywhere a regression would
  silently hurt conversion.
- **Regression criteria:** how the agent decides "this is a bug" vs
  "this is noise".
- **Feature-ask criteria:** when feedback should surface as a backlog
  hint vs being ignored.

The data ingestion cron pulls from enabled channels and lands signals on
the tracker issue. The agent applies the criteria above when classifying.

## 8. Guardrails — never autoship

**The agent CANNOT cross this line autonomously.** Changes to anything
listed here require operator approval. The agent may comment or open a
PR with a `needs-operator-review` label, but it must not merge.

**Defaults (keep unless you have a reason to remove):**

- Credentials, env-var names, auth paths, secret rotation
- Schema reshape beyond additive (renames, drops, type changes)
- Payment / billing flows
- Frozen public API contracts
- This file's §§1–§8 (only §9 is append-only)
- The runbook's hard-stop rules
- Anything labelled `do-not-autoship` on GitHub

**Project-specific never-touch list — fill in:**

- [e.g. core business-logic math]
- [e.g. order placement paths]
- [e.g. consent / GDPR flows]
- [...]

The agent re-reads this section on every pass. Updating it tightens or
loosens the boundary immediately.

## 9. Learnings (append-only)

The agent appends here after each non-trivial PR. The operator can edit
freely. Older entries should not be deleted — they are the institutional
memory the next pass relies on.

Format: `YYYY-MM-DD PR #N — <summary> [directive: §X]`

(empty — first entries will appear here)
