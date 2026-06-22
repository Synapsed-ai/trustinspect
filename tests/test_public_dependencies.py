from __future__ import annotations

from pathlib import Path
import tomllib


def test_rich_is_declared_as_runtime_dependency():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    deps = data.get("project", {}).get("dependencies", [])
    assert any(str(dep).lower().startswith("rich") for dep in deps)
