from __future__ import annotations

import shutil
import re
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml

from trustinspect.resources import builtin_directory


_NULL_SELECTOR_VALUES = {"", "null", "none", "nil", "n/a", "na", "-", "--"}


def normalize_optional_selector(value: Optional[str]) -> Optional[str]:
    """Normalize optional selector values coming from CLI/wizards.

    Users often type literal values such as "null" or "none" when a selector
    is not present. Those strings must never be passed to Selenium as CSS
    selectors.
    """
    if value is None:
        return None
    normalized = str(value).strip()
    if normalized.lower() in _NULL_SELECTOR_VALUES:
        return None
    return normalized


@dataclass
class TargetDefinition:
    id: str
    name: str
    url: str
    type: str = "web-ui"
    category: str = "ai_target"
    status: str = "selector_required"  # ready | selector_required | local | disabled
    input_selector: Optional[str] = None
    output_selector: Optional[str] = None
    send_selector: Optional[str] = None
    frame_selector: Optional[str] = None
    profile_strategy: str = "standard_chat"
    supported_suites: List[str] = field(default_factory=list)
    recommended_dynamic_tests_per_static: int = 1
    risk_focus: List[str] = field(default_factory=list)
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_path: Optional[str] = None
    registry_local_dir: Optional[str] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], source_path: Optional[Path] = None) -> "TargetDefinition":
        return cls(
            id=str(data.get("id") or "unknown"),
            name=str(data.get("name") or data.get("id") or "Unknown target"),
            url=str(data.get("url") or ""),
            type=str(data.get("type") or "web-ui"),
            category=str(data.get("category") or "ai_target"),
            status=str(data.get("status") or "selector_required"),
            input_selector=normalize_optional_selector(data.get("input_selector")),
            output_selector=normalize_optional_selector(data.get("output_selector")),
            send_selector=normalize_optional_selector(data.get("send_selector")),
            frame_selector=normalize_optional_selector(data.get("frame_selector")),
            profile_strategy=str(data.get("profile_strategy") or "standard_chat"),
            supported_suites=list(data.get("supported_suites") or []),
            recommended_dynamic_tests_per_static=int(data.get("recommended_dynamic_tests_per_static") or 1),
            risk_focus=list(data.get("risk_focus") or []),
            notes=str(data.get("notes") or ""),
            metadata=dict(data.get("metadata") or {}),
            source_path=str(source_path) if source_path else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "type": self.type,
            "category": self.category,
            "status": self.status,
            "input_selector": self.input_selector,
            "output_selector": self.output_selector,
            "send_selector": self.send_selector,
            "frame_selector": self.frame_selector,
            "profile_strategy": self.profile_strategy,
            "supported_suites": self.supported_suites,
            "recommended_dynamic_tests_per_static": self.recommended_dynamic_tests_per_static,
            "risk_focus": self.risk_focus,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @property
    def is_ready(self) -> bool:
        return bool(self.url and self.input_selector and self.output_selector)

    @property
    def source_kind(self) -> str:
        if not self.source_path:
            return "unknown"
        p = Path(self.source_path)
        parts = set(p.parts)
        if self.registry_local_dir and p.resolve().parent == Path(self.registry_local_dir).resolve():
            return "local"
        if p.parent.name == "builtin":
            return "builtin"
        if "local" in parts:
            return "local"
        if "builtin" in parts or "examples" in parts:
            return "builtin"
        return "unknown"


class TargetRegistry:
    def __init__(self, targets: Iterable[TargetDefinition] | None = None) -> None:
        self.targets: List[TargetDefinition] = []
        for target in targets or []:
            self.add(target)

    def add(self, target: TargetDefinition) -> None:
        # Local targets should override built-ins with the same id.
        existing_index = next((i for i, t in enumerate(self.targets) if t.id == target.id), None)
        if existing_index is None:
            self.targets.append(target)
            return

        existing = self.targets[existing_index]
        if target.source_kind == "local" or existing.source_kind != "local":
            self.targets[existing_index] = target

    def list(self) -> List[TargetDefinition]:
        return sorted(self.targets, key=lambda t: (0 if t.is_ready else 1, t.name.lower()))

    def get(self, target_id: str) -> Optional[TargetDefinition]:
        for target in self.targets:
            if target.id == target_id:
                return target
        return None

    def ready_targets(self) -> List[TargetDefinition]:
        return [t for t in self.list() if t.is_ready]


def _load_yaml_file(path: Path) -> Optional[TargetDefinition]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return TargetDefinition.from_dict(data, source_path=path)



def _resolve_builtin_dirs_for_public_release(builtins_dir, legacy_builtins_dir=None):
    """Default names refer to trusted bundled targets, not similarly named cwd files."""
    if builtins_dir is None or str(builtins_dir) in {"targets/builtin", "examples/targets"}:
        candidates = [builtin_directory("targets/builtin")]
    else:
        requested = Path(builtins_dir).expanduser()
        # Explicit registry roots are optional search locations: local-only
        # workspaces need not create a built-in directory. Do not replace an
        # explicitly configured root with bundled entries when it is absent.
        if requested.exists() and not requested.is_dir():
            raise NotADirectoryError(f"Built-in target path is not a directory: {requested}")
        candidates = [requested]
    if legacy_builtins_dir is not None and str(legacy_builtins_dir) != "examples/targets":
        candidates.append(Path(legacy_builtins_dir).expanduser())
    return list(dict.fromkeys(candidates))

def load_target_registry(
    builtins_dir: str | Path = "targets/builtin",
    local_dir: str | Path = "targets/local",
    legacy_builtins_dir: str | Path | None = None,
) -> TargetRegistry:
    registry = TargetRegistry()

    # Load built-ins first, then legacy examples, then local overrides.
    for directory in [*_resolve_builtin_dirs_for_public_release(builtins_dir, legacy_builtins_dir), Path(local_dir).expanduser()]:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.yaml")):
            target = _load_yaml_file(path)
            if target:
                target.registry_local_dir = str(Path(local_dir).expanduser().resolve())
                registry.add(target)

    registry.targets = [t for t in registry.targets if t.status.lower() != "disabled"]
    return registry


def _workspace_directory(value: str | Path) -> Path:
    directory = Path(value).expanduser()
    package = Path(__file__).resolve().parents[1]
    if directory.resolve().is_relative_to(package):
        raise ValueError("Target state must be stored outside the TrustInspect package")
    return directory


def save_local_target(target: TargetDefinition, local_dir: str | Path = "targets/local") -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", target.id):
        raise ValueError("Target id must be a safe filename, not a path")
    directory = _workspace_directory(local_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{target.id}.yaml"
    if path.is_symlink():
        raise ValueError("Local target file must not be a symlink")
    clean = target.to_dict()
    if clean.get("status", "").lower() != "disabled":
        clean["status"] = "ready" if target.is_ready else "selector_required"
    path.write_text(yaml.safe_dump(clean, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path



def _find_target_source_file_for_archive(target: TargetDefinition) -> Optional[Path]:
    """Locate the backing YAML for a target created manually or loaded from registry."""
    if getattr(target, "source_path", None):
        src = Path(str(target.source_path))
        if src.exists():
            return src

    candidates = [
        Path("targets/local") / f"{target.id}.yaml",
        Path("targets/builtin") / f"{target.id}.yaml",
        Path("examples/targets") / f"{target.id}.yaml",
    ]
    for src in candidates:
        if src.exists():
            return src

    # Last resort: scan local/builtin for a YAML with matching id field.
    for directory in [Path("targets/local"), Path("targets/builtin"), Path("examples/targets")]:
        if not directory.exists():
            continue
        for path in directory.glob("*.yaml"):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            if isinstance(data, dict) and str(data.get("id")) == str(target.id):
                return path
    return None

def archive_target(target: TargetDefinition, disabled_dir: str | Path = "targets/disabled") -> Optional[Path]:
    """Archive a target YAML file instead of deleting it permanently.

    Returns the destination path when archived, or None if the target has no
    backing source file.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", target.id):
        raise ValueError("Target id must be a safe filename, not a path")
    src = _find_target_source_file_for_archive(target)
    if src is None or not src.exists():
        return None

    if src.is_symlink():
        raise ValueError("Target source file must not be a symlink")

    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    kind = target.source_kind or "unknown"
    dest_dir = _workspace_directory(_workspace_directory(disabled_dir) / stamp / kind)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.is_symlink() or dest.exists():
        raise FileExistsError("Archive destination already exists; no files were changed")

    if src.resolve().parent == builtin_directory("targets/builtin").resolve():
        # Installed data is immutable. A workspace tombstone suppresses the target.
        save_local_target(replace(target, status="disabled"), target.registry_local_dir or "targets/local")
        shutil.copy2(src, dest)
    else:
        shutil.move(str(src), str(dest))
    return dest
