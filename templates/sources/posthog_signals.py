"""PostHog signals source.

Surfaces recent product-analytics signals from PostHog: DAU/WAU
estimates, recent errors captured as events, and any insight you've
configured as a "monitor" (the source can fetch named insights and
check their last value).

Config (in .autoworker/sources.yml):

    posthog_signals:
      host: https://us.posthog.com    # or eu.posthog.com / self-hosted
      project_id: 12345               # your numeric project ID
      monitored_insights:             # optional — names or short IDs
        - daily_active_users
        - weekly_signups
        - error_rate_7d
      drop_threshold_pct: 20          # warn if a monitored insight drops
                                      # by this many % vs prior period

Env (set as repo secrets):
  POSTHOG_API_KEY — a Personal API Key with `insight:read` +
                    `query:read` scopes. (Project API keys are
                    write-only; you want the personal one.)

Docs: https://posthog.com/docs/api/
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def _get(url: str, token: str) -> tuple[int, Any]:
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {token}',
        'User-Agent': 'autoworker-posthog/1',
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8', errors='replace'))
    except urllib.error.HTTPError as e:
        body = (e.read() or b'').decode('utf-8', errors='replace')[:400]
        return e.code, {'error': body}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return 0, {'error': str(e)[:400]}


def collect(config: dict) -> dict:
    host = (config.get('host') or 'https://us.posthog.com').rstrip('/')
    project_id = config.get('project_id')
    monitored = config.get('monitored_insights') or []
    drop_threshold_pct = float(config.get('drop_threshold_pct', 20))

    token = os.environ.get('POSTHOG_API_KEY', '')
    if not token:
        return {
            'summary': 'posthog_signals: POSTHOG_API_KEY not set.',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'posthog_unconfigured',
                'detail': 'Set POSTHOG_API_KEY as a repo secret.',
            }],
        }
    if not project_id:
        return {
            'summary': 'posthog_signals: project_id required.',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'posthog_unconfigured',
                'detail': 'Set `project_id` in the source config.',
            }],
        }

    anomalies: list[dict] = []
    md: list[str] = []
    summary_bits: list[str] = []

    # Pull the project's insights list and look for the monitored ones.
    insights_url = f'{host}/api/projects/{project_id}/insights/?limit=200'
    status, payload = _get(insights_url, token)
    if status != 200 or not isinstance(payload, dict):
        anomalies.append({
            'severity': 'warn',
            'rule': 'posthog_fetch_failed',
            'detail': f'HTTP {status} from insights endpoint',
        })
        return {
            'summary': f'posthog_signals: insights fetch failed (HTTP {status}).',
            'markdown': '',
            'anomalies': anomalies,
        }

    insights = payload.get('results') or []
    md.append(f'### PostHog — {len(insights)} insight(s) in project')

    # Match monitored insights by short_id or name (case-insensitive).
    wanted = {str(w).lower() for w in monitored}
    if wanted:
        for ins in insights:
            short_id = (ins.get('short_id') or '').lower()
            name = (ins.get('name') or '').lower()
            derived_name = (ins.get('derived_name') or '').lower()
            if not (short_id in wanted or name in wanted or derived_name in wanted):
                continue

            # PostHog returns the latest result inline for many insight
            # types. We look at the last two periods to compute a drop.
            result = ins.get('result')
            last_value: float | None = None
            prev_value: float | None = None
            if isinstance(result, list) and result:
                # Trends: each series has `data` array — last two points.
                first = result[0] if result else {}
                data = first.get('data') if isinstance(first, dict) else None
                if isinstance(data, list) and len(data) >= 2:
                    try:
                        last_value = float(data[-1])
                        prev_value = float(data[-2])
                    except (TypeError, ValueError):
                        pass
            elif isinstance(result, dict) and 'count' in result:
                # Some single-value formats.
                try:
                    last_value = float(result['count'])
                except (TypeError, ValueError):
                    pass

            display = ins.get('name') or ins.get('derived_name') or ins.get('short_id')
            if last_value is None:
                md.append(f'- **{display}** — no recent value (insight may be empty or unsupported type)')
                continue

            summary_bits.append(f'{display}={last_value:g}')
            if prev_value is not None and prev_value > 0:
                pct = (last_value - prev_value) / prev_value * 100.0
                md.append(f'- **{display}** — {last_value:g} (Δ {pct:+.1f}% vs prior)')
                if pct <= -abs(drop_threshold_pct):
                    anomalies.append({
                        'severity': 'warn',
                        'rule': 'posthog_insight_dropped',
                        'detail': f'{display} dropped {pct:.1f}% '
                                  f'({prev_value:g} → {last_value:g})',
                    })
            else:
                md.append(f'- **{display}** — {last_value:g}')
    else:
        md.append('- _No insights configured for monitoring. '
                  'Set `monitored_insights:` in the source config to enable._')

    return {
        'summary': ('PostHog: ' + ', '.join(summary_bits)) if summary_bits
                   else f'PostHog: {len(insights)} insight(s) available',
        'markdown': '\n'.join(md),
        'anomalies': anomalies,
    }
