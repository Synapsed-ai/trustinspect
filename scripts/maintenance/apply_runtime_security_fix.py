#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path.cwd()

NO_SANDBOX_FILES = [
    ROOT / "trustinspect" / "interactive" / "calibration.py",
    ROOT / "trustinspect" / "scanners" / "web_ui" / "selenium_scanner.py",
    ROOT / "trustinspect" / "scanners" / "web_ui" / "auto_selector.py",
]

DOM_SNAPSHOT_FILE = ROOT / "trustinspect" / "scanners" / "web_ui" / "selenium_scanner.py"


def patch_no_sandbox(path: Path) -> bool:
    if not path.exists():
        print(f"[!] Missing file: {path}")
        return False

    original = path.read_text(encoding="utf-8")
    updated = re.sub(
        r'(?m)^(?P<indent>\s*)options\.add_argument\(["\']--no-sandbox["\']\)\s*(?:#.*)?$',
        r'\g<indent># Chrome sandbox intentionally remains enabled by default.',
        original,
    )

    if updated != original:
        backup = path.with_suffix(path.suffix + ".bak_runtime_security")
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
        path.write_text(updated, encoding="utf-8")
        print(f"[+] Removed default --no-sandbox from {path}")
        return True

    if "--no-sandbox" in original:
        print(f"[!] {path} still contains --no-sandbox but no known pattern was patched")
    else:
        print(f"[=] No --no-sandbox default found in {path}")
    return False


def patch_dom_snapshot_extension(path: Path) -> bool:
    if not path.exists():
        print(f"[!] Missing file: {path}")
        return False

    original = path.read_text(encoding="utf-8")
    updated = original

    # Common exact form used by TrustInspect.
    updated = updated.replace(
        'f"{safe_target}_{idx:03d}_{safe_case}_dom.html"',
        'f"{safe_target}_{idx:03d}_{safe_case}_dom.html.txt"',
    )
    updated = updated.replace(
        "f'{safe_target}_{idx:03d}_{safe_case}_dom.html'",
        "f'{safe_target}_{idx:03d}_{safe_case}_dom.html.txt'",
    )

    # Defensive fallback for similar f-string patterns.
    updated = re.sub(
        r'(?P<prefix>_dom)\.html(?P<quote>["\'])',
        r'\g<prefix>.html.txt\g<quote>',
        updated,
    )

    if updated != original:
        backup = path.with_suffix(path.suffix + ".bak_dom_snapshot_ext")
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
        path.write_text(updated, encoding="utf-8")
        print(f"[+] Changed DOM snapshot extension to .html.txt in {path}")
        return True

    print(f"[=] No DOM .html snapshot pattern found in {path}")
    return False


def main() -> int:
    print("TrustInspect runtime security fix")
    print("================================")

    for path in NO_SANDBOX_FILES:
        patch_no_sandbox(path)

    patch_dom_snapshot_extension(DOM_SNAPSHOT_FILE)

    print("\n[+] Patch completed. Now run:")
    print("    python scripts/maintenance/check_runtime_security_guards.py")
    print("    python -m pytest -q")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
