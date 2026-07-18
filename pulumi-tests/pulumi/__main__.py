"""Pulumi project marker. Coverage is driven by run_suite.py (Automation API)."""

from __future__ import annotations

import pulumi

pulumi.export("hint", "Use python run_suite.py / make pulumi-tests")
