#!/usr/bin/env python3
"""
cleanup.py — hapus generated spec, report, dan screenshot untuk tiket.
Triggered by /automation <id> cleanup command.

Usage:
    python scripts/cleanup.py --id 7434

Behavior:
    - Delete spec file(s): specs/generated/wp-<id>-*.spec.ts
    - Delete report JSON: reports/wp-<id>-ui-verify.json
    - Delete screenshot(s): test-results/**/wp-<id>-*.png
    - Output JSON to stdout dengan detail files deleted
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SPEC_DIR = REPO / 'specs' / 'generated'
REPORT_DIR = REPO.parent / 'reports'
TEST_RESULTS_DIR = REPO / 'test-results'


def cleanup_spec(ticket_id: int) -> list:
    """Delete spec file(s) for ticket."""
    deleted = []
    if SPEC_DIR.exists():
        for spec_file in SPEC_DIR.glob(f'wp-{ticket_id}-*.spec.ts'):
            spec_file.unlink()
            deleted.append(str(spec_file.name))
    return deleted


def cleanup_report(ticket_id: int) -> list:
    """Delete report JSON for ticket."""
    deleted = []
    report_path = REPORT_DIR / f'wp-{ticket_id}-ui-verify.json'
    if report_path.exists():
        report_path.unlink()
        deleted.append(str(report_path.name))
    return deleted


def cleanup_screenshots(ticket_id: int) -> list:
    """Delete screenshot file(s) for ticket."""
    deleted = []
    if TEST_RESULTS_DIR.exists():
        for screenshot in TEST_RESULTS_DIR.glob(f'**/wp-{ticket_id}-*.png'):
            screenshot.unlink()
            deleted.append(str(screenshot.relative_to(REPO)))
    return deleted


def cleanup_all(ticket_id: int) -> dict:
    """Cleanup all artifacts for ticket."""
    return {
        'ticket_id': ticket_id,
        'specs': cleanup_spec(ticket_id),
        'reports': cleanup_report(ticket_id),
        'screenshots': cleanup_screenshots(ticket_id)
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--id', type=int, required=True, help='OpenProject work_package id')
    args = p.parse_args()

    result = cleanup_all(args.id)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
