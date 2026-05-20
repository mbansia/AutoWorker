"""Browser-based usability testing.

Spins up a headless Chromium via Playwright and runs operator-defined
user journeys against a deployed (or local) app. Each journey is a
sequence of declarative steps (`goto`, `click`, `fill`, `assert_*`,
`screenshot`). Failures, slow loads, and asserted-but-missing elements
surface as anomalies on the tracker.

Config (in .autoworker/sources.yml):

    browser_usability:
      base_url: https://app.example.com
      viewport: { width: 1280, height: 720 }   # optional
      default_timeout_ms: 10000                # optional, per step
      user_agent: "AutoWorker browser tester"  # optional
      performance:
        warn_above_ms: 3000                    # optional
        critical_above_ms: 10000               # optional
      screenshot_dir: ./autoworker_screenshots # optional, relative to checkout
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
            - click: "button[type=submit]"
            - wait_for_url: "/verify"

Supported step actions:
  - goto: <path>                            # navigate to base_url + path
  - wait_for: <selector>                    # wait for element
  - wait_for_url: <substring>               # wait until URL contains substring
  - fill: { selector, value }               # fill an input
  - click: <selector>                       # click an element
  - assert_visible: <selector>              # assert element is visible
  - assert_text: { selector, contains }     # assert element contains text
  - assert_url_contains: <substring>        # assert current URL contains substring
  - screenshot: <name>                      # save screenshot to screenshot_dir

Requirements:
  - playwright + chromium installed. The data ingest workflow conditionally
    runs `pip install playwright && playwright install chromium --with-deps`
    when this source is enabled in .autoworker/sources.yml.

Notes:
  - Headless only. Browser is closed cleanly even on failure.
  - Each journey runs in a fresh context (isolated cookies / storage).
  - Performance thresholds use `page.goto`'s navigation time (DOMContentLoaded).
"""

from __future__ import annotations

import os
import time
import traceback
from pathlib import Path
from typing import Any


def _normalize_step(raw: Any) -> tuple[str, Any]:
    """Each step is one of:
      - { action_name: arg }                 — the common form
      - { action_name: { ...kwargs... } }    — for actions taking multiple args
      - "shortcut_string"                    — not used here, kept for future
    """
    if isinstance(raw, dict) and len(raw) == 1:
        action, arg = next(iter(raw.items()))
        return action, arg
    raise ValueError(f'malformed step: {raw!r}')


def _run_step(page, base_url: str, action: str, arg: Any, default_timeout: int) -> None:
    """Execute a single journey step. Raises on assertion failure or
    any Playwright error; the journey wrapper turns these into anomalies."""
    if action == 'goto':
        page.goto(base_url + arg, timeout=default_timeout)
    elif action == 'wait_for':
        page.wait_for_selector(arg, timeout=default_timeout)
    elif action == 'wait_for_url':
        page.wait_for_url(lambda url: arg in url, timeout=default_timeout)
    elif action == 'fill':
        page.locator(arg['selector']).fill(arg['value'], timeout=default_timeout)
    elif action == 'click':
        page.locator(arg).click(timeout=default_timeout)
    elif action == 'assert_visible':
        if not page.locator(arg).is_visible():
            raise AssertionError(f'selector {arg!r} not visible')
    elif action == 'assert_text':
        text = page.locator(arg['selector']).inner_text(timeout=default_timeout)
        if arg['contains'] not in text:
            raise AssertionError(
                f'{arg["selector"]!r} text {text!r} does not contain {arg["contains"]!r}'
            )
    elif action == 'assert_url_contains':
        if arg not in page.url:
            raise AssertionError(f'url {page.url!r} does not contain {arg!r}')
    elif action == 'screenshot':
        # Handled by the journey wrapper (it has the dir + name path).
        return arg  # sentinel — caller saves
    else:
        raise ValueError(f'unknown step action: {action!r}')


def _run_journey(
    browser, name: str, steps: list, base_url: str,
    viewport: dict, user_agent: str | None, default_timeout: int,
    screenshot_dir: Path,
) -> dict:
    """Run one journey in a fresh browser context. Returns a result dict."""
    started = time.monotonic()
    result: dict[str, Any] = {
        'name': name,
        'passed': False,
        'duration_ms': 0,
        'error': None,
        'screenshots': [],
        'step_log': [],
    }
    context = browser.new_context(
        viewport=viewport,
        user_agent=user_agent,
    )
    page = context.new_page()
    try:
        for raw_step in steps:
            action, arg = _normalize_step(raw_step)
            step_started = time.monotonic()
            try:
                screenshot_name = _run_step(page, base_url, action, arg, default_timeout)
                if action == 'screenshot' and screenshot_name:
                    screenshot_dir.mkdir(parents=True, exist_ok=True)
                    path = screenshot_dir / f'{name}__{screenshot_name}.png'
                    page.screenshot(path=str(path), full_page=True)
                    result['screenshots'].append(str(path))
                result['step_log'].append({
                    'action': action,
                    'ms': int((time.monotonic() - step_started) * 1000),
                    'ok': True,
                })
            except Exception as e:
                # Capture a screenshot of the failure point.
                try:
                    screenshot_dir.mkdir(parents=True, exist_ok=True)
                    path = screenshot_dir / f'{name}__FAILURE.png'
                    page.screenshot(path=str(path), full_page=True)
                    result['screenshots'].append(str(path))
                except Exception:  # noqa: BLE001 — screenshot is best-effort
                    pass
                result['step_log'].append({
                    'action': action,
                    'ms': int((time.monotonic() - step_started) * 1000),
                    'ok': False,
                    'error': str(e)[:300],
                })
                result['error'] = f'step {action}: {e}'
                return result
        result['passed'] = True
        return result
    finally:
        result['duration_ms'] = int((time.monotonic() - started) * 1000)
        context.close()


def collect(config: dict) -> dict:
    base_url = (config.get('base_url') or '').rstrip('/')
    journeys = config.get('journeys') or []

    if not base_url:
        return {
            'summary': 'browser_usability: no base_url configured.',
            'anomalies': [{
                'severity': 'warn',
                'rule': 'browser_usability_unconfigured',
                'detail': 'Set `base_url` in the source config.',
            }],
        }
    if not journeys:
        return {
            'summary': 'browser_usability: no journeys configured.',
            'anomalies': [{
                'severity': 'info',
                'rule': 'browser_usability_no_journeys',
                'detail': 'Add at least one journey to .autoworker/sources.yml.',
            }],
        }

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return {
            'summary': 'browser_usability: playwright not installed.',
            'anomalies': [{
                'severity': 'critical',
                'rule': 'playwright_missing',
                'detail': 'The data ingest workflow should `pip install '
                          'playwright && playwright install chromium`. Check '
                          'the workflow logs for the install step.',
            }],
        }

    viewport = config.get('viewport') or {'width': 1280, 'height': 720}
    user_agent = config.get('user_agent')
    default_timeout = int(config.get('default_timeout_ms', 10000))
    screenshot_dir = Path(config.get('screenshot_dir', './autoworker_screenshots'))
    perf = config.get('performance') or {}
    warn_above = int(perf.get('warn_above_ms', 0))
    critical_above = int(perf.get('critical_above_ms', 0))

    results: list[dict] = []
    anomalies: list[dict] = []
    md_lines: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                for j in journeys:
                    name = j.get('name', 'unnamed')
                    steps = j.get('steps') or []
                    res = _run_journey(
                        browser, name, steps, base_url, viewport,
                        user_agent, default_timeout, screenshot_dir,
                    )
                    results.append(res)

                    if res['passed']:
                        md_lines.append(
                            f'- ✅ **{name}** — {res["duration_ms"]}ms '
                            f'({len(res["step_log"])} steps)'
                        )
                    else:
                        md_lines.append(
                            f'- ❌ **{name}** — failed after '
                            f'{res["duration_ms"]}ms: {res["error"]}'
                        )
                        anomalies.append({
                            'severity': 'critical',
                            'rule': 'browser_journey_failed',
                            'detail': f'{name}: {res["error"]}',
                        })
                    if res['screenshots']:
                        for shot in res['screenshots']:
                            md_lines.append(f'  - screenshot: `{shot}`')

                    if critical_above and res['duration_ms'] >= critical_above:
                        anomalies.append({
                            'severity': 'critical',
                            'rule': 'browser_journey_slow',
                            'detail': f'{name} took {res["duration_ms"]}ms '
                                      f'(>= {critical_above}ms critical threshold)',
                        })
                    elif warn_above and res['duration_ms'] >= warn_above:
                        anomalies.append({
                            'severity': 'warn',
                            'rule': 'browser_journey_slow',
                            'detail': f'{name} took {res["duration_ms"]}ms '
                                      f'(>= {warn_above}ms warn threshold)',
                        })
            finally:
                browser.close()
    except Exception as e:  # noqa: BLE001 — top-level safety net
        return {
            'summary': f'browser_usability: harness crashed — {e}',
            'markdown': '```\n' + traceback.format_exc()[:2000] + '\n```',
            'anomalies': [{
                'severity': 'critical',
                'rule': 'browser_harness_crashed',
                'detail': str(e)[:300],
            }],
        }

    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    summary = f'{passed}/{total} journeys passed ({sum(r["duration_ms"] for r in results)}ms total)'

    # Surface screenshot dir if anything was captured.
    any_screenshots = any(r['screenshots'] for r in results)
    if any_screenshots:
        md_lines.append('')
        md_lines.append(
            f'_Screenshots saved to `{screenshot_dir}` — uploaded as a '
            f'workflow artifact named `autoworker-browser-screenshots`._'
        )

    return {
        'summary': summary,
        'markdown': '\n'.join(md_lines),
        'anomalies': anomalies,
    }
