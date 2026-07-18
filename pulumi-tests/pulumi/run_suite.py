#!/usr/bin/env python3
"""Run Engine contract coverage via Pulumi Automation API and write HTML report."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from pulumi import automation as auto

WORK_DIR = Path(__file__).resolve().parent
ROOT = WORK_DIR.parent


def main() -> int:
    os.environ.setdefault("PULUMI_CONFIG_PASSPHRASE", "ovirt-lab")
    state_dir = WORK_DIR / ".pulumi-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    backend = os.environ.setdefault("PULUMI_BACKEND_URL", f"file://{state_dir}")
    report_dir = Path(os.environ.setdefault("REPORT_DIR", str(ROOT / "reports")))
    report_dir.mkdir(parents=True, exist_ok=True)

    pythonpath = os.environ.get("PYTHONPATH", "")
    parts = [str(ROOT), str(WORK_DIR)]
    os.environ["PYTHONPATH"] = os.pathsep.join(parts + ([pythonpath] if pythonpath else []))
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if str(WORK_DIR) not in sys.path:
        sys.path.insert(0, str(WORK_DIR))

    from coverage.executor import _FULL_RUN_METHODS, report_to_dict, run_coverage
    from coverage.report import write_reports
    from shared.config import SuiteConfig

    print("Running Engine contract coverage…", flush=True)
    cfg = SuiteConfig.from_env()
    report = run_coverage(cfg)
    payload = report_to_dict(report)
    json_path, html_path = write_reports(payload, report_dir)
    totals = payload["totals"]
    methods = payload.get("methods") or {}
    series_names = [s["series"] for s in payload["series"]]

    summary_path = report_dir / "pulumi-stack-summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "total": totals["total"],
                "passed": totals["passed"],
                "failed": totals["failed"],
                "skipped": totals["skipped"],
                "methods": methods,
                "series": series_names,
                "report_json": str(json_path),
                "report_html": str(html_path),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    subprocess.check_call(["pulumi", "login", backend], cwd=str(WORK_DIR))

    def pulumi_program() -> None:
        import pulumi

        data = json.loads(summary_path.read_text(encoding="utf-8"))
        for key, value in data.items():
            pulumi.export(key, value)

    stack_name = os.environ.get("PULUMI_STACK", "dev")
    stack = auto.create_or_select_stack(
        stack_name=stack_name,
        project_name="ovirt-contract-coverage",
        program=pulumi_program,
    )
    print(f"Publishing results to Pulumi stack {stack_name}…", flush=True)
    result = stack.up(on_output=print)
    outputs = {k: v.value for k, v in result.outputs.items()}
    print(json.dumps({"outputs": outputs}, indent=2), flush=True)

    failed = int(outputs.get("failed") or totals["failed"])
    total = int(outputs.get("total") or totals["total"])
    passed = int(outputs.get("passed") or totals["passed"])
    print(f"SUMMARY total={total} passed={passed} failed={failed}", flush=True)
    print(f"METHODS {json.dumps(methods, sort_keys=True)}", flush=True)
    print(f"HTML report: {html_path}", flush=True)

    full_run = not cfg.smoke_only and not cfg.methods_filter
    missing_methods = sorted(_FULL_RUN_METHODS - set(methods)) if full_run else []
    if missing_methods:
        print(f"MISSING METHODS on full run: {', '.join(missing_methods)}", flush=True)
    if failed or missing_methods:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
