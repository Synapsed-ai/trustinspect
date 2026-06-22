from __future__ import annotations

from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path.cwd()
BACKUP = ROOT / "_archive" / "aitg-consolidation" / datetime.utcnow().strftime("%Y%m%d-%H%M%S")
FILES = [
    "trustinspect/reporting/html_report.py",
    "trustinspect/reporting/templates/assessment_report.html.j2",
    "trustinspect/reporting/aitg_visuals.py",
    "trustinspect/core/versions.py",
]


def main() -> None:
    for rel in FILES:
        path = ROOT / rel
        if path.exists():
            dest = BACKUP / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    print(f"[+] Backup created under: {BACKUP}")

    template = ROOT / "trustinspect" / "reporting" / "templates" / "assessment_report.html.j2"
    reporter = ROOT / "trustinspect" / "reporting" / "html_report.py"

    if not template.exists():
        print(f"[!] Missing template: {template}")
    else:
        t = template.read_text(encoding="utf-8")
        checks = {
            "no embedded base64 images": "data:image" not in t,
            "AITG impact overview": "OWASP AITG Impact Overview" in t,
            "no findings summary": "Findings Summary" not in t,
            "layer-based dynamic summary": "Generated Dynamic Tests by OWASP AITG Layer" in t,
        }
        for label, ok in checks.items():
            print(("[+]" if ok else "[!]") + f" Template check: {label}")

    if not reporter.exists():
        print(f"[!] Missing reporter: {reporter}")
    else:
        r = reporter.read_text(encoding="utf-8")
        checks = {
            "suite inference helper": "def _suite_info" in r,
            "duration formatting": "def _duration_human" in r,
            "observation sorting": "CLASSIFICATION_ORDER" in r,
            "AITG official layers": "OFFICIAL_AITG_LAYERS" in r,
        }
        for label, ok in checks.items():
            print(("[+]" if ok else "[!]") + f" Reporter check: {label}")

    print("[+] Run: pip install -e . && pytest -q tests/test_aitg_consolidated_report.py")


if __name__ == "__main__":
    main()
