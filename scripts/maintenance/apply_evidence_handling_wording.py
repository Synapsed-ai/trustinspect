#!/usr/bin/env python3
"""Append evidence-handling/privacy wording to README.md and SECURITY.md if missing."""
from __future__ import annotations

from pathlib import Path

README_SECTION = """
## Evidence handling and privacy

TrustInspect reports and evidence files may contain sensitive information collected during an assessment, including prompts, model responses, screenshots, DOM snapshots, target URLs, generated test cases, and target capability profiles.

Review generated reports and evidence artifacts before sharing them outside the assessment team. TrustInspect does not upload reports or evidence by default; generated artifacts are stored locally in the output path selected by the tester.

Use TrustInspect only against systems you own, operate, or are explicitly authorized to test. Public AI challenge targets may change over time and may require selector calibration.
""".strip()

SECURITY_SECTION = """
## Evidence and report handling

TrustInspect is an evidence-based testing tool. Assessment outputs may contain sensitive prompts, model responses, screenshots, DOM snapshots, target URLs, generated dynamic tests, and target capability profiles.

Before sharing reports, sample outputs, screenshots, or evidence folders, reviewers should verify that they do not contain customer data, credentials, secrets, private prompts, internal system prompts, proprietary documents, or other sensitive material.

For release artifacts, do not include local runtime outputs such as `reports/`, `profiles/`, `generated_tests/`, `_archive/`, `.venv/`, `.pytest_cache/`, or `trustinspect.egg-info/`. Build public release archives from Git-tracked files only, for example with `git archive`.
""".strip()


def append_once(path: Path, marker: str, section: str) -> None:
    if not path.exists():
        path.write_text(section + "\n", encoding="utf-8")
        print(f"[+] Created {path}")
        return
    text = path.read_text(encoding="utf-8")
    if marker.lower() in text.lower():
        print(f"[=] {path} already contains {marker}")
        return
    path.write_text(text.rstrip() + "\n\n" + section + "\n", encoding="utf-8")
    print(f"[+] Updated {path}")


def main() -> int:
    append_once(Path("README.md"), "Evidence handling and privacy", README_SECTION)
    append_once(Path("SECURITY.md"), "Evidence and report handling", SECURITY_SECTION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
