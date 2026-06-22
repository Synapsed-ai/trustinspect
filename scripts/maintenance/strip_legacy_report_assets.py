#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "trustinspect" / "reporting" / "templates" / "assessment_report.html.j2"


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect legacy embedded report assets.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not TEMPLATE.exists():
        print(f"Template not found: {TEMPLATE}")
        return 1

    text = TEMPLATE.read_text(encoding="utf-8", errors="ignore")
    bad = []
    for marker in ["data:image", "base64,", "ti-report-hero img"]:
        if marker in text:
            bad.append(marker)

    if bad:
        print("Legacy report asset markers found:")
        for marker in bad:
            print(f"  - {marker}")
        print("Use the lightweight CSS report template before public release.")
        return 1 if args.check else 0

    print("OK: no embedded image markers found in report template")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
