#!/usr/bin/env python3
"""
Phase 4.1 — Standalone Validation Harness CLI Runner
====================================================
Executes the MetrologyMitra 16 golden validation scenarios,
verifies legal traceability and safety boundaries, and
outputs terminal summaries and CI-compatible JSON.

Usage:
    python scripts/run_validation.py
    python scripts/run_validation.py --json
    python scripts/run_validation.py --scenario SCENARIO-01
"""

import argparse
import asyncio
import json
import sys
from typing import Optional

from app.validation.runner import ValidationRunner
from app.validation.scenarios import GOLDEN_SCENARIOS


async def main_async(scenario_id: Optional[str] = None, json_mode: bool = False) -> int:
    scenarios_to_run = GOLDEN_SCENARIOS
    if scenario_id:
        scenarios_to_run = [s for s in GOLDEN_SCENARIOS if s.scenario_id.upper() == scenario_id.upper()]
        if not scenarios_to_run:
            print(f"Error: Scenario '{scenario_id}' not found in GOLDEN_SCENARIOS.")
            return 1

    runner = ValidationRunner(scenarios=scenarios_to_run)
    summary = await runner.run_all()

    if json_mode:
        print(json.dumps(summary.to_dict(), indent=2))
        return 0 if summary.failed == 0 else 1

    # Pretty Terminal Output
    print("=" * 84)
    print("       METROLOGYMITRA PHASE 4.1 — VALIDATION HARNESS EXECUTION SUMMARY")
    print("=" * 84)
    print(f" {'ID':<13} | {'STATUS':<6} | {'TIME(ms)':<8} | {'TITLE'}")
    print("-" * 84)

    for r in summary.results:
        status_color = "\033[92mPASS\033[0m" if r.status == "PASS" else "\033[91mFAIL\033[0m"
        print(f" {r.scenario_id:<13} | {status_color:<15} | {r.duration_ms:<8.1f} | {r.title}")
        if r.error_message:
            print(f"   -> ERROR: {r.error_message}")

    print("-" * 84)
    print(f" TOTAL SCENARIOS : {summary.total}")
    print(f" PASSED          : {summary.passed}")
    print(f" FAILED          : {summary.failed}")
    print(f" SUCCESS RATE    : {summary.success_rate_percent}%")
    print("=" * 84)

    if summary.failed == 0:
        print("OVERALL VALIDATION: PASS (100% SUCCESS)\n")
        return 0
    else:
        print(f"OVERALL VALIDATION: FAIL ({summary.failed} scenarios failed)\n")
        return 1


def main():
    parser = argparse.ArgumentParser(description="MetrologyMitra Phase 4.1 Validation Runner")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--scenario", type=str, default=None, help="Run specific scenario by ID (e.g. SCENARIO-01)")
    args = parser.parse_args()

    exit_code = asyncio.run(main_async(scenario_id=args.scenario, json_mode=args.json))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

