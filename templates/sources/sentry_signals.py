"""Sentry signals source.

Surfaces recent Sentry issues + event stats for the project. Anomalies
fire when new high-impact issues appear or when the error rate jumps.

Config (in .autoworker/sources.yml):

    sentry_signals:
      org: your-org-slug
      project: your-project-slug
      host: https://sentry.io       # optional; default sentry.io cloud
      issue_limit: 10               # optional
      event_count_threshold: 100    # optional; if recent events > this, warn

Env (set as repo secrets):
  SENTRY_AUTH_TOKEN — a Sentry internal-integration or user-auth token
                      with `project:read` + `event:read` + `org:read` scopes.

Docs: https://docs.sentry.io/api/
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def _get(url: str, token: str) -> tuple[int, Any]:
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {token}',
        'User-Agent': 'autoworker-sentry/1',
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
    org = (config.get('org') or '').strip()
    project = (config.get('project') or '').strip()
    host = (config.get('host') or 'https://sentry.io').rstrip('/')
    limit = int(config.get('issue_limit', 10))
    event_threshold = int(config.get('event_count_threshold', 100))

    token = os.environ.get('SENTRY_AUTH_TOKEN', '')
    if not token:
        return {
            'summary': 'sentry_signals: SENTRY_AUTH_TOKEN not set.',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'sentry_unconfigured',
                'detail': 'Set SENTRY_AUTH_TOKEN as a repo secret.',
            }],
        }
    if not org or not project:
        return {
            'summary': 'sentry_signals: org + project required.',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'sentry_unconfigured',
                'detail': 'Set `org` and `project` in the source config.',
            }],
        }

    anomalies: list[dict] = []
    md: list[str] = []

    # Recent unresolved issues, sorted by frequency.
    issues_url = (
        f'{host}/api/0/projects/{org}/{project}/issues/'
        f'?query=is:unresolved&statsPeriod=24h&limit={limit}&sort=freq'
    )
    status, issues = _get(issues_url, token)
    if status != 200 or not isinstance(issues, list):
        anomalies.append({
            'severity': 'warn',
            'rule': 'sentry_issues_fetch_failed',
            'detail': f'HTTP {status} from issues endpoint: '
                      f'{(issues or {}).get("error", "")[:200] if isinstance(issues, dict) else ""}',
        })
        return {
            'summary': f'sentry_signals: issues fetch failed (HTTP {status}).',
            'markdown': '',
            'anomalies': anomalies,
        }

    md.append(f'### Sentry — {len(issues)} unresolved issue(s) in last 24h')
    for issue in issues[:limit]:
        title = (issue.get('title') or '')[:200]
        count = issue.get('count', '?')
        users = (issue.get('userCount') or 0)
        permalink = issue.get('permalink') or ''
        md.append(f'- [{count} events / {users} users] {title} — {permalink}')
        # Promote any issue with high user impact to a warn anomaly.
        try:
            user_count = int(users)
            event_count = int(count)
        except (TypeError, ValueError):
            user_count = 0
            event_count = 0
        if user_count >= 10 or event_count >= 500:
            anomalies.append({
                'severity': 'warn',
                'rule': 'sentry_high_impact_issue',
                'detail': f'{title} — {event_count} events / {user_count} users',
            })
        # `level: error/fatal` is the strict subset we treat as critical.
        if issue.get('level') in ('fatal',) and event_count >= 50:
            anomalies.append({
                'severity': 'critical',
                'rule': 'sentry_fatal_issue',
                'detail': f'{title} — {event_count} fatal events',
            })

    # Quick event-rate sanity check.
    stats_url = (
        f'{host}/api/0/organizations/{org}/stats_v2/'
        f'?field=sum%28quantity%29&interval=1h&statsPeriod=24h&category=error'
    )
    status, stats = _get(stats_url, token)
    if status == 200 and isinstance(stats, dict):
        # Sum over the returned series for a rough 24h total.
        total = 0
        for group in (stats.get('groups') or []):
            series = group.get('series') or {}
            for arr in series.values():
                if isinstance(arr, list):
                    for v in arr:
                        try:
                            total += int(v)
                        except (TypeError, ValueError):
                            continue
        md.append('')
        md.append(f'- Last-24h error event total: **{total}**')
        if total >= event_threshold:
            anomalies.append({
                'severity': 'warn',
                'rule': 'sentry_event_rate_high',
                'detail': f'{total} error events in 24h (>= {event_threshold} threshold)',
            })

    return {
        'summary': f'{len(issues)} unresolved issue(s)',
        'markdown': '\n'.join(md),
        'anomalies': anomalies,
    }
