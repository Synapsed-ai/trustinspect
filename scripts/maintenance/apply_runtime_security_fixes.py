#!/usr/bin/env python3
"""
Apply TrustInspect runtime security hardening fixes.

Fixes:
- Keep Chrome sandbox enabled by default by removing unguarded sandbox-disabling Chrome args.
- Store DOM snapshots as inert text artifacts (.html.txt) instead of executable .html files.

Run from repository root:
    python scripts/maintenance/apply_runtime_security_fixes.py
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil

ROOT = Path.cwd()
STAMP = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

FILES_TO_PATCH = [
    Path("trustinspect/interactive/calibration.py"),
    Path("trustinspect/scanners/web_ui/selenium_scanner.py"),
    Path("trustinspect/scanners/web_ui/auto_selector.py"),
]


def backup(path: Path) -> None:
    backup_path = path.with_name(path.name + f".bak-runtime-security-{STAMP}")
    shutil.copy2(path, backup_path)
    print(f"[+] Backup: {backup_path}")


def patch_no_sandbox(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    # Remove unguarded Chrome sandbox-disabling arguments. Do not leave the literal
    # argument in comments, because the release guard intentionally scans for it.
    replacements = {
        '    options.add_argument("--no-sandbox")\n': '    # Browser sandbox remains enabled by default.\n',
        '        options.add_argument("--no-sandbox")\n': '        # Browser sandbox remains enabled by default.\n',
        '    chrome_opts.add_argument("--no-sandbox")\n': '    # Browser sandbox remains enabled by default.\n',
        '        chrome_opts.add_argument("--no-sandbox")\n': '        # Browser sandbox remains enabled by default.\n',
        "    options.add_argument('--no-sandbox')\n": '    # Browser sandbox remains enabled by default.\n',
        "        options.add_argument('--no-sandbox')\n": '        # Browser sandbox remains enabled by default.\n',
        "    chrome_opts.add_argument('--no-sandbox')\n": '    # Browser sandbox remains enabled by default.\n',
        "        chrome_opts.add_argument('--no-sandbox')\n": '        # Browser sandbox remains enabled by default.\n',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    if text != original:
        backup(path)
        path.write_text(text, encoding="utf-8")
        print(f"[+] Removed unguarded browser sandbox-disabling arg from {path}")
        return True
    print(f"[-] No sandbox-disabling arg found in {path}")
    return False


def patch_dom_snapshot_extension(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    # Convert active HTML DOM artifacts to inert text artifacts.
    text = text.replace('_dom.html"', '_dom.html.txt"')
    text = text.replace("_dom.html'", "_dom.html.txt'")
    text = text.replace('_dom.html)', '_dom.html.txt)')

    if text != original:
        backup(path)
        path.write_text(text, encoding="utf-8")
        print(f"[+] Changed DOM snapshot extension to inert text artifact in {path}")
        return True
    print(f"[-] No DOM .html snapshot extension found in {path}")
    return False


def main() -> None:
    changed = False
    for rel in FILES_TO_PATCH:
        path = ROOT / rel
        if not path.exists():
            print(f"[!] Missing expected file: {rel}")
            continue
        changed |= patch_no_sandbox(path)
        if rel.name == "selenium_scanner.py":
            changed |= patch_dom_snapshot_extension(path)

    print("[+] Runtime security hardening applied" if changed else "[=] No changes were required")
    print("[i] Next: python scripts/maintenance/check_runtime_security_guards.py")


if __name__ == "__main__":
    main()
