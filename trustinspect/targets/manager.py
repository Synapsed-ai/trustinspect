from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import shutil
import yaml


@dataclass
class DisabledTargetResult:
    target_id: str
    moved_files: List[str]
    disabled_dir: str


def _candidate_target_dirs(
    builtin_dir: str | Path = "targets/builtin",
    local_dir: str | Path = "targets/local",
    legacy_builtin_dir: str | Path = "examples/targets",
) -> List[Path]:
    """Return target config directories that may exist in old or new layouts."""
    dirs: List[Path] = []
    for value in [local_dir, builtin_dir, legacy_builtin_dir]:
        path = Path(value)
        if path.exists() and path.is_dir() and path not in dirs:
            dirs.append(path)
    return dirs


def _read_target_id(path: Path) -> Optional[str]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("id")
    return str(value) if value else None


def find_target_files_by_id(
    target_id: str,
    *,
    builtin_dir: str | Path = "targets/builtin",
    local_dir: str | Path = "targets/local",
    legacy_builtin_dir: str | Path = "examples/targets",
) -> List[Path]:
    """Find YAML files defining a target id across builtin/local target stores.

    This intentionally does not inspect targets/disabled, so disabling is idempotent.
    """
    target_id = str(target_id).strip()
    matches: List[Path] = []
    for directory in _candidate_target_dirs(builtin_dir, local_dir, legacy_builtin_dir):
        for path in sorted(directory.glob("*.y*ml")):
            if _read_target_id(path) == target_id:
                matches.append(path)
    return matches


def disable_target_by_id(
    target_id: str,
    *,
    reason: str | None = None,
    disabled_root: str | Path = "targets/disabled",
    builtin_dir: str | Path = "targets/builtin",
    local_dir: str | Path = "targets/local",
    legacy_builtin_dir: str | Path = "examples/targets",
) -> DisabledTargetResult:
    """Disable a target by moving its YAML file(s) to targets/disabled/<timestamp>/.

    The function does not delete permanently. This is safer for demo work and lets
    the tester restore a target by moving the YAML file back into targets/builtin/
    or targets/local/.
    """
    files = find_target_files_by_id(
        target_id,
        builtin_dir=builtin_dir,
        local_dir=local_dir,
        legacy_builtin_dir=legacy_builtin_dir,
    )
    if not files:
        raise FileNotFoundError(f"No target YAML file found for target id: {target_id}")

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    safe_id = "".join(c if c.isalnum() or c in "-_" else "-" for c in target_id).strip("-") or "target"
    dest_dir = Path(disabled_root) / f"{timestamp}_{safe_id}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    moved: List[str] = []
    for path in files:
        dest = dest_dir / path.name
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{path.stem}_{counter}{path.suffix}"
            counter += 1
        shutil.move(str(path), str(dest))
        moved.append(str(dest))

    if reason:
        (dest_dir / "DISABLED_REASON.txt").write_text(reason + "\n", encoding="utf-8")

    return DisabledTargetResult(target_id=target_id, moved_files=moved, disabled_dir=str(dest_dir))
