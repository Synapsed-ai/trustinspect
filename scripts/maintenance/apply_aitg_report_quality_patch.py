from __future__ import annotations

from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path.cwd()
BACKUP = ROOT / "_archive" / "aitg-report-quality" / datetime.utcnow().strftime("%Y%m%d-%H%M%S")

FILES = [
    "trustinspect/reporting/html_report.py",
    "trustinspect/reporting/templates/assessment_report.html.j2",
    "trustinspect/core/versions.py",
    "trustinspect/ui/terminal.py",
]


def main() -> None:
    for rel in FILES:
        path = ROOT / rel
        if path.exists():
            dest = BACKUP / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    print(f"[+] Backup created under: {BACKUP}")
    print("[+] AITG report quality files are already copied by cp -R.")
    print("[+] Run: pip install -e . && pytest -q tests/test_aitg_report_quality.py")


if __name__ == "__main__":
    main()
