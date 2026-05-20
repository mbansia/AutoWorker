# Example deployment: AutoTrader_Codex

A concrete deployment of AutoWorker against a production trading bot.
[`mbansia/autotrader_codex`](https://github.com/mbansia/autotrader_codex)
is a Python / FastAPI funding-rate arbitrage bot — three venues
(Binance, KuCoin, Hyperliquid), SQLite, single-instance, real money.
The v0 of this pattern was developed during the bot's v1.3 → v1.5
rewrite; v1 (AutoWorker as a general template) is the generalisation.

## Install parameters

| Parameter            | Value                                |
|----------------------|--------------------------------------|
| PROJECT_NAME         | AutoTrader_Codex                     |
| REPO_SLUG            | mbansia/autotrader_codex             |
| SETUP                | claude_code_github_actions           |
| CRON_CADENCE         | `0 */3 * * *` (every 3 hours)        |
| ENABLED_SOURCES      | diagnostics_endpoint, github_signals |
| TRACKER_ISSUE_NUMBER | 28                                   |
| PRIMARY_GOAL         | "Stay solvent. Ship correct changes only." |

The bot's spec doc (`docs/SYSTEM.md`, ~1900 lines) predates AutoWorker
and is referenced from `MASTER_DIRECTIVES.md` as the project's deeper
SSOT. The directives file at the root cites it section-by-section.

## Master directives — sections used

`MASTER_DIRECTIVES.md` references AutoTrader's existing spec:

| Directive §            | Maps to                                        |
|------------------------|------------------------------------------------|
| §1 goals               | "no insolvent state, fees-covered basis only"  |
| §3 tech                | refs `docs/SYSTEM.md` §3.1 SOP + math, §4 config |
| §4 security            | API-key rotation policy + venue auth paths     |
| §7 feedback signals    | GitHub issues + `[autoworker] Tracker`         |
| §8 never autoship      | (see below — verbatim)                         |
| §9 learnings           | append-only — also mirrored into `docs/SYSTEM.md` §16 |

## §8 verbatim — the never-autoship list

```
- docs/SYSTEM.md §3.1 math — gates, basis, APY, fees, deferral, exit triggers
- docs/SYSTEM.md §4 active fields + defaults
- docs/SYSTEM.md §7.1.1 schema beyond additive (no renames, drops, reshapes)
- docs/SYSTEM.md §8.1 frozen `/api/diagnostics` JSON contract
- Venue gateways' order placement paths (`place_market_fok`, rollback)
- docs/SYSTEM.md spec sections (§0, §3, §4, §7.1.1, §8.1).
    Allowed: §16 append-only learnings, §18 closing existing TODO rows.
- Credentials, env-var names, auth paths
```

Note the careful scoping: §16 (learnings) and §18 (open implementation
gaps) are explicitly allowed for autopilot because they're append-only
and operator-acknowledged. Everything else in the spec is policy.

## What the loop ships (representative sample)

From the bot's PR history under v0 (single-purpose monitor + autopilot;
v1 of AutoWorker preserves the same shipping discipline):

- **#51** — fix v1.5 startup against legacy v1.3 DB + KuCoin passphrase
  env var. Anomaly-driven: ingest flagged `endpoint_returned_error`, a
  prior pass diagnosed it, the next pass shipped the migration fix.
- **#49** — parity harness in-process mode + boot-time account-id
  assertion. Closed an `UPGRADE_BACKLOG.md` hint.
- **#43** — remove `max_hold_hours`; add
  `basis_dislocation_exit_bps`. Required explicit operator decision
  (touched §4 active fields → never-autoship → loop asked).

## Cadence

3-hour passes. At a typical cadence the loop does ~5–10 passes per day,
ships 0–2 PRs depending on the backlog. Most passes are heartbeat
acknowledgements: "no anomalies, no work surface yielded a candidate,
see you in 3h".

## What the operator does

- Reviews the PR stream (typically once a day).
- Adds hints to `UPGRADE_BACKLOG.md` when there's something specific to
  prioritise.
- Updates `MASTER_DIRECTIVES.md` §§1–§7 directly when direction needs
  to change. The loop honours the new boundary on the next pass.
- Slams the brakes by leaving a "no" comment on a recent `autoworker/*`
  PR or by reverting one — triggers the 3-pass cooldown.

That's the entire human workload. The loop handles everything else.
