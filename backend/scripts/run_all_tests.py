#!/usr/bin/env python3
"""
MetrologyMitra (SIH26034) — Master Regression Test Battery
==========================================================
Executes all 19 test suites sequentially and reports status, timing, and error details.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent
    tests_dir = base_dir / "tests"
    
    test_files = sorted([
        f for f in tests_dir.glob("test_*.py")
        if f.is_file()
    ])

    print("=" * 80)
    print(f"METROLOGYMITRA (SIH26034) — MASTER TEST SUITE ({len(test_files)} SUITES)")
    print("=" * 80)

    results = []
    total_start = time.time()

    for idx, test_file in enumerate(test_files, 1):
        rel_name = test_file.name
        print(f"[{idx:02d}/{len(test_files):02d}] Running {rel_name}...", end=" ", flush=True)
        
        t0 = time.time()
        res = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=str(base_dir),
            env=dict(os.environ, PYTHONPATH=str(base_dir)),
            capture_output=True,
            text=True,
        )
        elapsed = time.time() - t0

        if res.returncode == 0:
            print(f"PASS ({elapsed:.2f}s)")
            results.append((rel_name, "PASS", elapsed, ""))
        else:
            print(f"FAIL ({elapsed:.2f}s)")
            err_summary = res.stderr.strip() or res.stdout.strip()
            last_lines = "\n".join(err_summary.splitlines()[-6:])
            results.append((rel_name, "FAIL", elapsed, last_lines))

    total_time = time.time() - total_start

    print("\n" + "=" * 80)
    print("TEST EXECUTION SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for _, status, _, _ in results if status == "PASS")
    failed_count = len(results) - passed_count

    for name, status, elapsed, err in results:
        status_str = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"{status_str} {name:<45} {elapsed:6.2f}s")
        if err:
            print("       " + "\n       ".join(err.splitlines()))

    print("=" * 80)
    print(f"TOTAL SUITES: {len(results)} | PASSED: {passed_count} | FAILED: {failed_count} | TIME: {total_time:.2f}s")
    print("=" * 80)

    if failed_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
