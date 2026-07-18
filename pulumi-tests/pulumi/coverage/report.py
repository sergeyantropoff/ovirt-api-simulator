"""Write JSON + self-contained HTML coverage reports."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def write_reports(payload: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "pulumi-contract-coverage.json"
    html_path = report_dir / "pulumi-contract-coverage.html"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(payload), encoding="utf-8")
    return json_path, html_path


def render_html(payload: dict[str, Any]) -> str:
    totals = payload.get("totals") or {}
    methods = payload.get("methods") or {}
    series_rows = []
    for s in payload.get("series") or []:
        series_rows.append(
            "<tr>"
            f"<td>{html.escape(str(s.get('series')))}</td>"
            f"<td>{html.escape(str(s.get('api_version')))}</td>"
            f"<td>{s.get('total', 0)}</td>"
            f"<td class='ok'>{s.get('passed', 0)}</td>"
            f"<td class='bad'>{s.get('failed', 0)}</td>"
            f"<td>{s.get('skipped', 0)}</td>"
            f"<td>{s.get('duration_ms', 0):.0f} ms</td>"
            "</tr>"
        )

    method_rows = []
    for method, count in sorted(methods.items()):
        method_rows.append(
            "<tr>"
            f"<td>{html.escape(str(method))}</td>"
            f"<td>{count}</td>"
            "</tr>"
        )
    if not method_rows:
        method_rows.append("<tr><td colspan='2'>No methods recorded.</td></tr>")

    failed = [r for r in (payload.get("results") or []) if r.get("status") == "failed"]
    fail_rows = []
    for r in failed[:500]:
        fail_rows.append(
            "<tr>"
            f"<td>{html.escape(str(r.get('series')))}</td>"
            f"<td><code>{html.escape(str(r.get('operation_id')))}</code></td>"
            f"<td>{html.escape(str(r.get('method')))}</td>"
            f"<td><code>{html.escape(str(r.get('path_template')))}</code></td>"
            f"<td>{html.escape(str(r.get('http_status')))}</td>"
            f"<td><code>{html.escape(str(r.get('detail') or '')[:180])}</code></td>"
            "</tr>"
        )
    if not fail_rows:
        fail_rows.append("<tr><td colspan='6'>No failures.</td></tr>")

    # Compact sample of passed ops (first 100) for confidence
    passed = [r for r in (payload.get("results") or []) if r.get("status") == "passed"]
    pass_sample = []
    for r in passed[:100]:
        pass_sample.append(
            "<tr>"
            f"<td>{html.escape(str(r.get('series')))}</td>"
            f"<td><code>{html.escape(str(r.get('operation_id')))}</code></td>"
            f"<td>{html.escape(str(r.get('method')))}</td>"
            f"<td>{html.escape(str(r.get('http_status')))}</td>"
            f"<td>{r.get('duration_ms', 0)}</td>"
            "</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>oVirt Pulumi contract coverage</title>
  <style>
    :root {{
      --bg: #0f1419;
      --panel: #1d2226;
      --text: #f0f3f5;
      --muted: #9aa3a8;
      --ok: #3f9c35;
      --bad: #c9190b;
      --accent: #0076b6;
      --line: #2d363c;
    }}
    body {{
      margin: 0; padding: 32px;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background: linear-gradient(160deg, #0f1419, #16202a 45%, #1a2733);
      color: var(--text);
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .sub {{ color: var(--muted); margin-bottom: 24px; }}
    .cards {{ display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; margin-bottom: 28px; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); padding: 16px; border-radius: 8px; }}
    .card .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
    .card .value {{ font-size: 28px; margin-top: 6px; font-weight: 600; }}
    .card.ok .value {{ color: var(--ok); }}
    .card.bad .value {{ color: var(--bad); }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--line); margin-bottom: 28px; }}
    th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; font-size: 13px; }}
    th {{ color: var(--muted); font-weight: 600; background: #161b1f; }}
    code {{ font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 12px; }}
    .ok {{ color: var(--ok); }}
    .bad {{ color: var(--bad); }}
    h2 {{ font-size: 18px; margin: 0 0 12px; color: var(--accent); }}
  </style>
</head>
<body>
  <h1>oVirt Pulumi contract coverage</h1>
  <div class="sub">
    Generated {html.escape(str(payload.get('generated_at')))}
    · Engine {html.escape(str(payload.get('engine_url')))}
  </div>
  <div class="cards">
    <div class="card"><div class="label">Total</div><div class="value">{totals.get('total', 0)}</div></div>
    <div class="card ok"><div class="label">Passed</div><div class="value">{totals.get('passed', 0)}</div></div>
    <div class="card bad"><div class="label">Failed</div><div class="value">{totals.get('failed', 0)}</div></div>
    <div class="card"><div class="label">Skipped</div><div class="value">{totals.get('skipped', 0)}</div></div>
  </div>

  <h2>By HTTP method</h2>
  <table>
    <thead><tr><th>Method</th><th>Count</th></tr></thead>
    <tbody>
      {''.join(method_rows)}
    </tbody>
  </table>

  <h2>By series</h2>
  <table>
    <thead><tr><th>Series</th><th>API</th><th>Total</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Duration</th></tr></thead>
    <tbody>
      {''.join(series_rows)}
    </tbody>
  </table>

  <h2>Failures (up to 500)</h2>
  <table>
    <thead><tr><th>Series</th><th>Operation</th><th>Method</th><th>Path</th><th>HTTP</th><th>Detail</th></tr></thead>
    <tbody>
      {''.join(fail_rows)}
    </tbody>
  </table>

  <h2>Passed sample (first 100)</h2>
  <table>
    <thead><tr><th>Series</th><th>Operation</th><th>Method</th><th>HTTP</th><th>ms</th></tr></thead>
    <tbody>
      {''.join(pass_sample) if pass_sample else '<tr><td colspan="5">No passed operations.</td></tr>'}
    </tbody>
  </table>
</body>
</html>
"""
