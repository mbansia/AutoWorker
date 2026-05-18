"""GitHub signals source.

Surfaces open issues with operator-chosen labels (default `bug`,
`regression`, `urgent`), plus the last few failed workflow runs on
main.

Config:

    github_signals:
      labels: [bug, regression, urgent]
      failed_run_limit: 5
      stale_issue_days: 14   # warn if any matching issue is older

Env:
  GH_TOKEN  — provided by the workflow's GITHUB_TOKEN
  REPO      — owner/name
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone


def _gh_json(args: list[str]) -> list[dict] | dict | None:
    res = subprocess.run(['gh', *args], capture_output=True, text=True)
    if res.returncode != 0:
        return None
    try:
        return json.loads(res.stdout or 'null')
    except json.JSONDecodeError:
        return None


def collect(config: dict) -> dict:
    repo = os.environ['REPO']
    labels = config.get('labels', ['bug', 'regression', 'urgent'])
    failed_limit = int(config.get('failed_run_limit', 5))
    stale_days = int(config.get('stale_issue_days', 14))

    anomalies: list[dict] = []
    md: list[str] = []

    # Open issues matching any of the labels.
    label_flag = ','.join(labels)
    issues = _gh_json([
        'issue', 'list', '--repo', repo, '--state', 'open',
        '--label', label_flag, '--limit', '20',
        '--json', 'number,title,labels,createdAt,url',
    ]) or []
    if issues:
        md.append(f'### Open issues ({len(issues)}, labels: {label_flag})')
        cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
        for it in issues:
            created = datetime.fromisoformat(it['createdAt'].replace('Z', '+00:00'))
            stale = created < cutoff
            md.append(f'- #{it["number"]} {it["title"]} ({it["url"]})'
                      + ('  ⏳ stale' if stale else ''))
            if stale:
                anomalies.append({
                    'severity': 'warn',
                    'rule': 'stale_labeled_issue',
                    'detail': f'#{it["number"]} {it["title"]} open > {stale_days}d',
                })
    else:
        md.append(f'### Open issues — none with labels: {label_flag}')

    # Recent workflow runs on main: report failures.
    runs = _gh_json([
        'run', 'list', '--repo', repo, '--branch', 'main',
        '--limit', str(failed_limit * 2), '--status', 'completed',
        '--json', 'conclusion,name,headBranch,createdAt,url',
    ]) or []
    failed = [r for r in runs if r.get('conclusion') == 'failure'][:failed_limit]
    if failed:
        md.append('')
        md.append(f'### Failed runs on main (latest {len(failed)})')
        for r in failed:
            md.append(f'- {r["name"]} @ {r["createdAt"]}  ({r["url"]})')
        anomalies.append({
            'severity': 'critical' if len(failed) >= 3 else 'warn',
            'rule': 'ci_failures_on_main',
            'detail': f'{len(failed)} failed run(s) on main, latest: {failed[0]["name"]}',
        })

    summary = (
        f'{len(issues)} labeled issue(s) · '
        f'{len(failed)} failed run(s) on main'
    )
    return {
        'summary': summary,
        'markdown': '\n'.join(md),
        'anomalies': anomalies,
    }
