# Data sources

AutoWorker data sources are small Python modules that the ingest cron
runs each tick. Each module:

- Exposes one function: `collect(config: dict) -> dict`
- Returns a dict with optional keys:
  - `summary` — a one-line string for the tracker issue body
  - `markdown` — a markdown block of detail
  - `anomalies` — a list of `{severity, rule, detail}` dicts that get
    promoted to the snapshot's top-level anomalies list (the agent's
    primary signal surface)
- Reads any secrets it needs from `os.environ` (so the GitHub Actions
  workflow can inject them).

Sources live at `.github/scripts/autoworker_sources/<name>.py` in your
target repo. The ingest script (`autoworker_data_ingest.py`) loads each
one by file path and calls `collect()` with the per-source config
block.

## Built-in sources

- **diagnostics_endpoint** — polls an HTTP endpoint, treats the JSON as
  the snapshot. Carries forward the v0 AutoTrader pattern.
- **github_signals** — open issues (especially labelled `bug`,
  `regression`, `urgent`), recently failed CI runs.
- **social_reddit** — public Reddit search for a project name. No auth.
- **browser_usability** — spins up headless Chromium via Playwright and
  runs operator-defined user journeys (load page → click → fill →
  assert). Surfaces failures + slow loads + missing elements as
  anomalies. Saves screenshots; the data ingest workflow uploads them
  as a workflow artifact named `autoworker-browser-screenshots`. Adds
  ~30s overhead per run (only when enabled).
- **sentry_signals** — pulls recent unresolved Sentry issues for a
  project + 24h error event total. Anomalies fire on fatal issues
  with high counts and on error-rate spikes. Needs `SENTRY_AUTH_TOKEN`.
- **posthog_signals** — fetches PostHog insights you flag for
  monitoring; compares the latest value vs the prior period and warns
  on configurable drop thresholds (e.g. WAU drops >20%). Needs
  `POSTHOG_API_KEY`.
- **app_logs** — generic log endpoint poller. Works against any HTTP
  endpoint that returns a JSON list of log entries with level + message
  fields. Counts errors/warns in the window and samples the most recent
  errors into the tracker. Auth header is configurable; env vars
  interpolate via `${VAR_NAME}`.

### `browser_usability` quick example

```yaml
enabled:
  - browser_usability:
      base_url: https://app.example.com
      performance:
        warn_above_ms: 3000
        critical_above_ms: 10000
      journeys:
        - name: homepage_loads
          steps:
            - goto: /
            - wait_for: "h1"
            - assert_text: { selector: "h1", contains: "Welcome" }
            - screenshot: homepage
        - name: signup_flow
          steps:
            - goto: /signup
            - fill: { selector: "[name=email]", value: "test+autoworker@example.com" }
            - fill: { selector: "[name=password]", value: "TestPass123!" }
            - click: "button[type=submit]"
            - wait_for_url: "/verify"
```

Supported step actions: `goto`, `wait_for`, `wait_for_url`, `fill`,
`click`, `assert_visible`, `assert_text`, `assert_url_contains`,
`screenshot`. See `browser_usability.py` docstring for the full
reference.

Best paired with a staging URL — pointing `base_url` at production
means the journeys hit production user state. For destructive flows
(sign-up, purchase), use a dedicated test environment.

**Security note:** `.autoworker/sources.yml` is plain text in the
repo. Don't put real credentials in `fill` values. Use disposable
test accounts on a staging environment. If a journey genuinely
needs a secret, extend `browser_usability.py` to read it from
`os.environ` and inject it via a repo secret in the data ingest
workflow.

## Add your own

Drop `mycustom.py` in this directory. Minimal shape:

```python
import os

def collect(config: dict) -> dict:
    threshold = config.get('threshold', 10)
    # ... do work ...
    return {
        'summary': f'Hello — got {n} events',
        'markdown': '- detail line 1\n- detail line 2',
        'anomalies': [
            {'severity': 'warn', 'rule': 'too_many', 'detail': f'{n} > {threshold}'},
        ],
    }
```

Then enable it in `.autoworker/sources.yml`:

```yaml
enabled:
  - mycustom:
      threshold: 25
```

## Common additions

Likely sources to write yourself:

- **social_x** — needs `X_BEARER_TOKEN`. Skeleton in the X API docs;
  not bundled here because the auth lifecycle and rate limits depend on
  the operator's account tier.
- **support_inbox** — IMAP / email-API ingestion of `support@yourdomain`
  with a sentiment / urgency tag.
- **app_store_reviews** — RSS for iOS / Play Store reviews.
- **product_metrics** — your analytics provider (Mixpanel, Amplitude,
  PostHog) summarised to a dashboard delta.

Keep each source narrow. The agent treats `anomalies` as the action
trigger; everything else is context.
