"""Read bundled runtime resources without depending on the working directory.

Regular pip installs use wheel data. Source/editable installs use the same
allowlisted original files relative to this module, never relative to cwd.
Direct zipimport of an uninstalled wheel is not supported by this Path API.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

_PACKAGE_ROOT = Path(__file__).resolve().parent
RESOURCE_FILES = tuple(json.loads((_PACKAGE_ROOT / "_resource_manifest.json").read_text(encoding="utf-8")))
RESOURCE_ALIASES = {
    "examples/test_suites/owasp_aitg_light.yaml": "suites/owasp/aitg-light.yaml",
    "examples/test_suites/owasp_aitg_full.yaml": "suites/owasp/aitg-full.yaml",
}
RESOURCE_DIRECTORIES = frozenset(str(PurePosixPath(p).parent) for p in RESOURCE_FILES)


def _resource_root() -> Path:
    bundled = _PACKAGE_ROOT / "_data"
    if bundled.is_dir():
        return bundled
    source = _PACKAGE_ROOT.parent
    if (source / "pyproject.toml").is_file() and (source / "setup.py").is_file():
        return source
    raise FileNotFoundError("TrustInspect runtime data is missing. Reinstall the complete distribution.")


def builtin_file(relative: str) -> Path:
    if relative not in RESOURCE_FILES:
        raise ValueError(f"Unknown built-in resource: {relative!r}")
    root = _resource_root().resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise FileNotFoundError(f"Missing built-in TrustInspect resource: {relative}")
    return path


def builtin_directory(relative: str) -> Path:
    if relative not in RESOURCE_DIRECTORIES:
        raise ValueError(f"Unknown built-in resource directory: {relative!r}")
    expected = [p for p in RESOURCE_FILES if str(PurePosixPath(p).parent) == relative]
    # Missing data must fail visibly rather than silently generate zero tests.
    paths = [builtin_file(p) for p in expected]
    return paths[0].parent


def resolve_input_file(path: str | Path) -> Path:
    """Resolve explicit files; known legacy relative resource names are aliases.

    Existing user files take precedence here. Built-in suite IDs bypass this
    function and always load bundled data. Absolute missing files never fall back.
    """
    requested = Path(path).expanduser()
    if requested.is_file():
        return requested
    key = RESOURCE_ALIASES.get(requested.as_posix(), requested.as_posix())
    if not requested.is_absolute() and key in RESOURCE_FILES:
        return builtin_file(key)
    raise FileNotFoundError(f"Input file does not exist: {requested}")


def dynamic_template_directory(path: str | Path | None = None) -> Path:
    if path is None:
        return builtin_directory("examples/dynamic_templates")
    requested = Path(path).expanduser()
    if not requested.is_absolute() and requested.as_posix() == "examples/dynamic_templates":
        return builtin_directory("examples/dynamic_templates")
    if requested.is_dir():
        return requested
    raise FileNotFoundError(f"Dynamic template directory does not exist: {requested}")
