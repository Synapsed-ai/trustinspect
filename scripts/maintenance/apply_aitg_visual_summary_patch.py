from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()


def main() -> None:
    print("[+] AITG visual summary patch uses the supplied html_report.py and assessment_report.html.j2 files.")
    template = ROOT / "trustinspect" / "reporting" / "templates" / "assessment_report.html.j2"
    reporter = ROOT / "trustinspect" / "reporting" / "html_report.py"
    if not template.exists():
        print(f"[!] Missing template: {template}")
    else:
        text = template.read_text(encoding="utf-8")
        if "OWASP AITG Impact Overview" in text and "Findings Summary" not in text:
            print("[+] Template OK: AITG visual overview present, Findings Summary removed.")
        else:
            print("[!] Template may not be updated as expected. Re-copy patch files and retry.")
    if not reporter.exists():
        print(f"[!] Missing reporter: {reporter}")
    else:
        text = reporter.read_text(encoding="utf-8")
        if "_aitg_visual_summary" in text and "by_aitg_layer" in text:
            print("[+] Reporter OK: AITG visual summary context present.")
        else:
            print("[!] Reporter may not be updated as expected. Re-copy patch files and retry.")


if __name__ == "__main__":
    main()
