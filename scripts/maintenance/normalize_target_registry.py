#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path.cwd()


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def read_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def key_for(path: Path) -> str:
    data = read_yaml(path)
    url = str(data.get("url") or "").strip().rstrip("/").lower()
    tid = str(data.get("id") or path.stem).strip().lower()
    name = str(data.get("name") or path.stem).strip().lower()
    return url or tid or name


def status_score(path: Path) -> int:
    data = read_yaml(path)
    status = str(data.get("status") or "").lower()
    if status == "ready":
        return 3
    if status == "partial":
        return 2
    if status == "selector_required":
        return 1
    return 0


def source_score(path: Path) -> int:
    # prefer local calibrated target over built-in, because selectors are user-validated
    s = str(path)
    if "/targets/local/" in s:
        return 3
    if "/targets/builtin/" in s:
        return 2
    return 1


def main() -> None:
    ap = argparse.ArgumentParser(description="Detect and optionally disable duplicate target YAML files.")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = bool(args.apply)

    roots = [ROOT / "targets" / "builtin", ROOT / "targets" / "local"]
    files = []
    for r in roots:
        if r.exists():
            files.extend(sorted(r.glob("*.y*ml")))

    groups: dict[str, list[Path]] = {}
    for f in files:
        groups.setdefault(key_for(f), []).append(f)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Found {len(files)} target file(s); duplicate groups: {len(duplicates)}")

    disabled_root = ROOT / "targets" / "disabled" / "duplicates" / now()
    moved = 0
    for key, paths in sorted(duplicates.items()):
        sorted_paths = sorted(paths, key=lambda p: (status_score(p), source_score(p), -len(str(p))), reverse=True)
        keep = sorted_paths[0]
        print(f"\nDuplicate key: {key}")
        print(f"  KEEP {keep.relative_to(ROOT)}")
        for p in sorted_paths[1:]:
            dst = disabled_root / p.relative_to(ROOT)
            print(f"  DISABLE {p.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
            moved += 1
            if apply:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), str(dst))

    print(f"\n{'Moved' if apply else 'Would move'} {moved} duplicate file(s).")


if __name__ == "__main__":
    main()
