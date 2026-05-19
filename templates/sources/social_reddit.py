"""Public Reddit search source.

Surfaces recent Reddit mentions of a query (typically the project
name). Uses the public JSON search endpoint — no auth required, but
rate limits apply.

Config:

    social_reddit:
      query: "MyProject"
      subreddit: all              # optional, defaults to all
      limit: 10
      promote_to_anomaly: false   # if true, mentions become 'warn' anomalies

Env: none.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


def collect(config: dict) -> dict:
    query = (config.get('query') or '').strip()
    if not query:
        return {
            'summary': 'social_reddit: no query configured.',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'social_reddit_unconfigured',
                'detail': 'Set `query` in the source config.',
            }],
        }
    sub = config.get('subreddit', 'all')
    limit = int(config.get('limit', 10))
    promote = bool(config.get('promote_to_anomaly', False))

    url = (
        f'https://www.reddit.com/r/{sub}/search.json?'
        + urllib.parse.urlencode({
            'q': query, 'sort': 'new', 'restrict_sr': 'false', 'limit': limit,
        })
    )
    req = urllib.request.Request(url, headers={
        'User-Agent': 'autoworker-social-reddit/1 (operator-configured)',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='replace'))
    except urllib.error.HTTPError as e:
        return {
            'summary': f'Reddit search returned HTTP {e.code}.',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'reddit_http_error',
                'detail': f'HTTP {e.code}',
            }],
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return {
            'summary': f'Reddit search failed: {e}.',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'reddit_failed',
                'detail': str(e)[:200],
            }],
        }

    children = (data.get('data') or {}).get('children') or []
    md = [f'### Reddit mentions of "{query}" — {len(children)} hit(s)']
    anomalies: list[dict] = []
    for c in children[:limit]:
        d = c.get('data') or {}
        title = (d.get('title') or '')[:160]
        sr = d.get('subreddit_name_prefixed', '')
        permalink = f'https://reddit.com{d.get("permalink", "")}'
        score = d.get('score', 0)
        md.append(f'- [{sr}] {title} (score {score}) — {permalink}')
        if promote:
            anomalies.append({
                'severity': 'warn',
                'rule': 'social_mention',
                'detail': f'{sr}: {title}',
            })
    return {
        'summary': f'{len(children)} Reddit mention(s) for "{query}"',
        'markdown': '\n'.join(md),
        'anomalies': anomalies,
    }
