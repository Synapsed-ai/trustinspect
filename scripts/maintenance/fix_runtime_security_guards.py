from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil

ROOT = Path.cwd()
STAMP = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
ARCHIVE = ROOT / "_archive" / "runtime-security-fix" / STAMP

BAD_ARG = "--" + "no-sandbox"

NO_SANDBOX_FILES = [
    ROOT / "trustinspect" / "interactive" / "calibration.py",
    ROOT / "trustinspect" / "scanners" / "web_ui" / "selenium_scanner.py",
    ROOT / "trustinspect" / "scanners" / "web_ui" / "auto_selector.py",
]

DOM_FILE = ROOT / "trustinspect" / "scanners" / "web_ui" / "selenium_scanner.py"


def archive_file(path: Path) -> None:
    if not path.exists():
        return
    dst = ARCHIVE / path.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)


def remove_no_sandbox(path: Path) -> bool:
    if not path.exists():
        print(f"[!] Missing file: {path}")
        return False

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    new_lines = []
    changed = False

    for line in lines:
        compact = line.replace("'", '"')
        if "add_argument" in compact and BAD_ARG in compact:
            changed = True
            print(f"[+] Removed insecure Chrome option from {path.relative_to(ROOT)}")
            continue
        new_lines.append(line)

    if changed:
        archive_file(path)
        path.write_text("".join(new_lines), encoding="utf-8")
    return changed


def patch_dom_snapshot_extension(path: Path) -> bool:
    if not path.exists():
        print(f"[!] Missing file: {path}")
        return False

    text = path.read_text(encoding="utf-8")
    updated = text
    replacements = {
        'f"{safe_target}_{idx:03d}_{safe_case}_dom.html"': 'f"{safe_target}_{idx:03d}_{safe_case}_dom.html.txt"',
        "f'{safe_target}_{idx:03d}_{safe_case}_dom.html'": "f'{safe_target}_{idx:03d}_{safe_case}_dom.html.txt'",
        'f"{safe_target}_{idx:03d}_{safe_case}_dom.html"': 'f"{safe_target}_{idx:03d}_{safe_case}_dom.html.txt"',
    }

    for old, new in replacements.items():
        updated = updated.replace(old, new)

    if updated != text:
        archive_file(path)
        path.write_text(updated, encoding="utf-8")
        print(f"[+] Changed DOM snapshot evidence extension to .html.txt in {path.relative_to(ROOT)}")
        return True

    if "_dom.html.txt" in text:
        print(f"[=] DOM snapshot extension already safe in {path.relative_to(ROOT)}")
        return False

    print(f"[!] Could not find DOM snapshot filename pattern in {path.relative_to(ROOT)}")
    return False


def main() -> int:
    changed = False
    for path in NO_SANDBOX_FILES:
        changed = remove_no_sandbox(path) or changed

    changed = patch_dom_snapshot_extension(DOM_FILE) or changed

    if changed:
        print(f"[+] Backups written under: {ARCHIVE}")
    else:
        print("[=] No runtime security guard changes required.")

    print("[+] Next: python scripts/maintenance/check_runtime_security_guards.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
