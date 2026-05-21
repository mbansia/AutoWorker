"""Application logs source.

Pulls recent application logs from any HTTP endpoint that returns
JSON. The shape is intentionally flexible: the operator supplies a URL
and a JSON path expression that points to a list of log entries.
Each entry is then filtered for severity and counted.

Config (in .autoworker/sources.yml):

    app_logs:
      url: https://logs.example.com/api/recent
      auth_header: "Bearer ${APP_LOGS_TOKEN}"   # interpolates env vars
      method: GET                                # GET or POST
      json_body: { hours: 1, severity: ["error", "warn"] }  # if POST
      logs_path: "data.entries"                  # dotted path to list
      level_field: severity                      # field name on each entry
      message_field: message                     # field name on each entry
      timestamp_field: ts                        # field name on each entry
      error_levels: ["error", "fatal", "critical"]
      warn_levels:  ["warn", "warning"]
      error_count_threshold: 10                  # warn anomaly above this
      sample_limit: 8                            # how many sample entries
                                                 # to render

Env (set as repo secrets per `auth_header`):
  APP_LOGS_TOKEN (or whatever you reference in `auth_header`)

Designed to work with a wide range of log services — Logflare,
Better Stack, Loki, Sumo, or a custom `/api/logs` you control. The
contract is: the endpoint returns JSON; somewhere in it is a list of
log entries; each entry has a level + message + timestamp.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


def _interpolate_env(value: str) -> str:
    return re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}',
                  lambda m: os.environ.get(m.group(1), ''),
                  value)


def _walk(payload: Any, path: str) -> Any:
    """Resolve a dotted path against a nested JSON payload."""
    for part in path.split('.'):
        if not part:
            continue
        if isinstance(payload, dict):
            payload = payload.get(part)
        elif isinstance(payload, list):
            try:
                payload = payload[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return payload


def collect(config: dict) -> dict:
    url = config.get('url') or ''
    if not url:
        return {
            'summary': 'app_logs: no url configured.',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'app_logs_unconfigured',
                'detail': 'Set `url` in the source config.',
            }],
        }

    method = (config.get('method') or 'GET').upper()
    auth_header = _interpolate_env(config.get('auth_header') or '')
    json_body = config.get('json_body')
    logs_path = config.get('logs_path') or ''
    level_field = config.get('level_field') or 'level'
    message_field = config.get('message_field') or 'message'
    timestamp_field = config.get('timestamp_field') or 'timestamp'
    error_levels = {str(s).lower() for s in (config.get('error_levels') or
                                              ['error', 'fatal', 'critical'])}
    warn_levels = {str(s).lower() for s in (config.get('warn_levels') or
                                             ['warn', 'warning'])}
    error_threshold = int(config.get('error_count_threshold', 10))
    sample_limit = int(config.get('sample_limit', 8))

    headers = {'User-Agent': 'autoworker-app-logs/1', 'Accept': 'application/json'}
    if auth_header:
        # Common header forms: "Bearer xyz" or "Basic xyz" or
        # "X-Api-Key: xyz". If the operator provides "Header: value",
        # split on the first colon; otherwise assume Authorization.
        if ':' in auth_header and not auth_header.lower().startswith(('bearer ', 'basic ')):
            k, _, v = auth_header.partition(':')
            headers[k.strip()] = v.strip()
        else:
            headers['Authorization'] = auth_header

    data = None
    if method == 'POST' and json_body is not None:
        # Interpolate env vars in any string values inside json_body.
        def _interp(node: Any) -> Any:
            if isinstance(node, str):
                return _interpolate_env(node)
            if isinstance(node, list):
                return [_interp(x) for x in node]
            if isinstance(node, dict):
                return {k: _interp(v) for k, v in node.items()}
            return node
        body = json.dumps(_interp(json_body)).encode('utf-8')
        headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    else:
        req = urllib.request.Request(url, headers=headers, method='GET')

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode('utf-8', errors='replace'))
    except urllib.error.HTTPError as e:
        return {
            'summary': f'app_logs: HTTP {e.code} from {url}',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'app_logs_fetch_failed',
                'detail': f'HTTP {e.code}',
            }],
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return {
            'summary': f'app_logs: fetch failed — {e}',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'app_logs_fetch_failed',
                'detail': str(e)[:200],
            }],
        }

    entries = _walk(payload, logs_path) if logs_path else payload
    if not isinstance(entries, list):
        return {
            'summary': f'app_logs: no log list at path {logs_path!r}',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'app_logs_bad_shape',
                'detail': f'Expected a list at {logs_path!r}; got {type(entries).__name__}',
            }],
        }

    error_count = 0
    warn_count = 0
    samples: list[str] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        level = str(e.get(level_field, '')).lower()
        if level in error_levels:
            error_count += 1
            if len(samples) < sample_limit:
                ts = str(e.get(timestamp_field, ''))[:32]
                msg = str(e.get(message_field, ''))[:300]
                samples.append(f'- `{ts}` [{level.upper()}] {msg}')
        elif level in warn_levels:
            warn_count += 1

    anomalies: list[dict] = []
    if error_count >= error_threshold:
        anomalies.append({
            'severity': 'warn',
            'rule': 'app_logs_error_burst',
            'detail': f'{error_count} error-level entries (>= {error_threshold} threshold)',
        })

    md = [
        f'### App logs — {error_count} error(s), {warn_count} warn(s) in window',
    ]
    if samples:
        md.append('')
        md.append('Recent errors:')
        md.extend(samples)

    return {
        'summary': f'logs: {error_count} error, {warn_count} warn',
        'markdown': '\n'.join(md),
        'anomalies': anomalies,
    }
