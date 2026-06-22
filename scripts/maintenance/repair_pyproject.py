from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import re

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"


def _extract(pattern: str, text: str, default: str) -> str:
    m = re.search(pattern, text, re.MULTILINE)
    return m.group(1).strip() if m else default


def main() -> int:
    if not PYPROJECT.exists():
        raise SystemExit(f"pyproject.toml not found at {PYPROJECT}")

    current = PYPROJECT.read_text(encoding="utf-8", errors="replace")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = PYPROJECT.with_suffix(f".toml.bak-repair-{stamp}")
    backup.write_text(current, encoding="utf-8")

    version = _extract(r'^version\s*=\s*["\']([^"\']+)["\']', current, "0.2.0")
    description = _extract(
        r'^description\s*=\s*["\']([^"\']+)["\']',
        current,
        "Evidence-Based Trustworthy AI Testing for LLM and Agentic Applications",
    )

    clean = f'''[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "trustinspect"
version = "{version}"
description = "{description}"
readme = "README.md"
requires-python = ">=3.10"
license = {{ text = "Apache-2.0" }}
authors = [
  {{ name = "Synapsed AI Lab" }}
]
keywords = [
  "trustworthy-ai",
  "llm-security",
  "ai-testing",
  "prompt-injection",
  "owasp",
]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Intended Audience :: Developers",
  "Intended Audience :: Information Technology",
  "License :: OSI Approved :: Apache Software License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Topic :: Security",
]
dependencies = [
  "jinja2>=3.1.2",
  "pyyaml>=6.0.1",
  "rich>=13.7.0",
  "selenium>=4.20.0",
  "webdriver-manager>=4.0.2",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
]

[project.scripts]
trustinspect = "trustinspect.cli:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["trustinspect*"]

[tool.setuptools.package-data]
trustinspect = [
  "reporting/templates/*.j2",
]
'''

    PYPROJECT.write_text(clean, encoding="utf-8")
    print(f"[+] Backed up broken pyproject.toml to {backup.name}")
    print("[+] Wrote clean pyproject.toml")
    print("[+] Runtime dependencies include rich>=13.7.0")
    print("[+] Dev extras include pytest>=8.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
