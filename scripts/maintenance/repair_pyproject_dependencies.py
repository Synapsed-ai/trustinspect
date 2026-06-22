from __future__ import annotations

import re
import shutil
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
PYPROJECT = ROOT / "pyproject.toml"

REQUIRED_DEPS = [
    "jinja2>=3.1.2",
    "pyyaml>=6.0.1",
    "selenium>=4.20.0",
    "webdriver-manager>=4.0.2",
    "rich>=13.7.0",
]
DEV_DEPS = ["pytest>=8.0"]


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _is_valid_toml(text: str) -> bool:
    try:
        tomllib.loads(text)
        return True
    except Exception:
        return False


def _read_valid_source() -> tuple[str, Path | None]:
    """Return valid pyproject text and the source path used.

    If the current pyproject is broken, try local backups before falling back
    to a clean TrustInspect v0.3-alpha pyproject.
    """
    if PYPROJECT.exists():
        text = PYPROJECT.read_text(encoding="utf-8")
        if _is_valid_toml(text):
            return text, PYPROJECT

    candidates = []
    candidates.extend(sorted(ROOT.glob("pyproject.toml.bak*"), key=lambda p: p.stat().st_mtime, reverse=True))
    candidates.extend(sorted(ROOT.glob("_archive/**/pyproject.toml*"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True))

    for candidate in candidates:
        if candidate.is_file():
            text = candidate.read_text(encoding="utf-8", errors="ignore")
            if _is_valid_toml(text):
                return text, candidate

    fallback = '''[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "trustinspect"
version = "0.2.0"
description = "Evidence-Based Trustworthy AI Testing for LLM and Agentic Applications"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "Apache-2.0" }
authors = [{ name = "Synapsed AI Lab" }]
dependencies = [
  "jinja2>=3.1.2",
  "pyyaml>=6.0.1",
  "selenium>=4.20.0",
  "webdriver-manager>=4.0.2",
  "rich>=13.7.0",
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

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
norecursedirs = [
  ".git",
  ".venv",
  "build",
  "dist",
  "_archive",
  "reports",
  "profiles",
  "generated_tests",
  "targets/local",
  "targets/disabled",
  "*.egg-info",
  "__pycache__",
]
filterwarnings = [
  "ignore:cannot collect test class 'TestCase':pytest.PytestCollectionWarning",
]
'''
    return fallback, None


def _normalize_dep_name(dep: str) -> str:
    return re.split(r"[<>=!~;\[]", dep.strip().strip('"').strip("'"), maxsplit=1)[0].lower()


def _format_array(values: list[str], indent: str = "  ") -> str:
    return "[\n" + "\n".join(f'{indent}"{v}",' for v in values) + "\n]"


def _ensure_dependencies(text: str) -> str:
    match = re.search(r"(?ms)^dependencies\s*=\s*\[(.*?)^\]", text)
    if not match:
        # Add dependencies at the end of [project] before the next table.
        project_match = re.search(r"(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)", text)
        deps_block = "dependencies = " + _format_array(REQUIRED_DEPS) + "\n\n"
        if project_match:
            insert_at = project_match.end(1)
            return text[:insert_at] + "\n" + deps_block + text[insert_at:]
        return text + "\n[project]\n" + deps_block

    raw_items = re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))
    by_name = {_normalize_dep_name(item): item for item in raw_items}
    for dep in REQUIRED_DEPS:
        by_name.setdefault(_normalize_dep_name(dep), dep)

    ordered_names = []
    for item in raw_items + REQUIRED_DEPS:
        name = _normalize_dep_name(item)
        if name not in ordered_names:
            ordered_names.append(name)
    new_values = [by_name[name] for name in ordered_names]
    new_block = "dependencies = " + _format_array(new_values)
    return text[:match.start()] + new_block + text[match.end():]


def _ensure_dev_extra(text: str) -> str:
    if not re.search(r"(?m)^\[project\.optional-dependencies\]", text):
        return text.rstrip() + "\n\n[project.optional-dependencies]\ndev = " + _format_array(DEV_DEPS) + "\n"

    dev_match = re.search(r"(?ms)^dev\s*=\s*\[(.*?)^\]", text)
    if not dev_match:
        section_match = re.search(r"(?ms)^\[project\.optional-dependencies\]\s*(.*?)(?=^\[|\Z)", text)
        insert_at = section_match.end(1) if section_match else len(text)
        return text[:insert_at] + "\ndev = " + _format_array(DEV_DEPS) + "\n" + text[insert_at:]

    raw_items = re.findall(r"['\"]([^'\"]+)['\"]", dev_match.group(1))
    by_name = {_normalize_dep_name(item): item for item in raw_items}
    for dep in DEV_DEPS:
        by_name.setdefault(_normalize_dep_name(dep), dep)

    ordered_names = []
    for item in raw_items + DEV_DEPS:
        name = _normalize_dep_name(item)
        if name not in ordered_names:
            ordered_names.append(name)
    new_values = [by_name[name] for name in ordered_names]
    new_block = "dev = " + _format_array(new_values)
    return text[:dev_match.start()] + new_block + text[dev_match.end():]


def _ensure_console_script(text: str) -> str:
    if not re.search(r"(?m)^\[project\.scripts\]", text):
        return text.rstrip() + "\n\n[project.scripts]\ntrustinspect = \"trustinspect.cli:main\"\n"
    if "trustinspect.cli:main" not in text:
        # Add command in project.scripts section.
        section_match = re.search(r"(?ms)^\[project\.scripts\]\s*(.*?)(?=^\[|\Z)", text)
        insert_at = section_match.end(1) if section_match else len(text)
        return text[:insert_at] + "\ntrustinspect = \"trustinspect.cli:main\"\n" + text[insert_at:]
    return text


def main() -> int:
    if not PYPROJECT.exists():
        print("[!] pyproject.toml not found in current directory", file=sys.stderr)
        return 1

    current = PYPROJECT.read_text(encoding="utf-8", errors="ignore")
    backup = PYPROJECT.with_name(f"pyproject.toml.bak-repair-{_stamp()}")
    backup.write_text(current, encoding="utf-8")
    print(f"[+] Backed up current pyproject.toml to {backup.name}")

    text, source = _read_valid_source()
    if source and source != PYPROJECT:
        print(f"[+] Restoring valid base from {source}")
    elif source == PYPROJECT:
        print("[+] Current pyproject.toml is valid; enriching dependencies")
    else:
        print("[!] No valid backup found; using clean fallback pyproject.toml")

    text = _ensure_dependencies(text)
    text = _ensure_dev_extra(text)
    text = _ensure_console_script(text)

    try:
        tomllib.loads(text)
    except Exception as exc:
        print(f"[!] Repaired pyproject is still invalid: {exc}", file=sys.stderr)
        return 2

    PYPROJECT.write_text(text, encoding="utf-8")
    print("[+] Repaired pyproject.toml")
    print("[+] Ensured runtime dependency: rich>=13.7.0")
    print("[+] Ensured dev extra: pytest>=8.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
