#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except Exception:
    print("Missing dependency: pyyaml. Install with: pip install pyyaml", file=sys.stderr)
    raise

ROOT = Path.cwd()
TARGET_DIRS = [ROOT / "examples" / "targets", ROOT / "targets" / "local"]
DISABLED_ROOT = ROOT / "targets" / "_disabled"


def load_yaml(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        return {"_error": str(exc)}


def target_id(data: dict, path: Path) -> str:
    return str(data.get("id") or data.get("target_id") or path.stem).strip()


def target_url(data: dict) -> str:
    return str(data.get("url") or data.get("target_url") or "").strip()


def normalized_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = (parsed.hostname or "").lower().replace("www.", "")
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def status(data: dict) -> str:
    explicit = data.get("status")
    if explicit:
        return str(explicit)
    return "ready" if data.get("input_selector") and data.get("output_selector") else "selector_required"


def priority(path: Path, data: dict) -> int:
    # Higher is better.
    is_local = "targets/local" in str(path)
    is_ready = status(data) == "ready"
    if is_local and is_ready:
        return 40
    if is_ready:
        return 30
    if is_local:
        return 20
    return 10


def iter_targets():
    for target_dir in TARGET_DIRS:
        if not target_dir.exists():
            continue
        for path in sorted(target_dir.glob("*.y*ml")):
            yield path, load_yaml(path)


def move_to_disabled(path: Path, reason: str, apply: bool) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    rel = path.relative_to(ROOT)
    dst = DISABLED_ROOT / ts / rel
    print(f"{'MOVE' if apply else 'WOULD MOVE'} {rel} -> {dst.relative_to(ROOT)}  reason={reason}")
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dst))


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean duplicate or unwanted TrustInspect target registry entries.")
    parser.add_argument("--apply", action="store_true", help="Apply changes. Without this, the command is a dry run.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned changes without applying them.")
    parser.add_argument("--dedupe", action="store_true", default=True, help="Dedupe targets by id and normalized URL. Default: true.")
    parser.add_argument("--disable", action="append", default=[], help="Disable target by id, filename stem, or normalized hostname/path substring. Can be used multiple times.")
    args = parser.parse_args()

    apply = args.apply and not args.dry_run
    targets = list(iter_targets())

    if not targets:
        print("No targets found.")
        return 0

    disable_terms = [x.lower().strip() for x in args.disable if x.strip()]
    disabled_paths = set()

    for path, data in targets:
        tid = target_id(data, path).lower()
        stem = path.stem.lower()
        nurl = normalized_url(target_url(data)).lower()
        if any(term in tid or term in stem or term in nurl for term in disable_terms):
            disabled_paths.add(path)
            move_to_disabled(path, "explicit-disable", apply)

    if args.dedupe:
        groups: dict[str, list[tuple[Path, dict]]] = {}
        for path, data in targets:
            if path in disabled_paths:
                continue
            keys = {target_id(data, path).lower()}
            nurl = normalized_url(target_url(data))
            if nurl:
                keys.add(nurl)
            for key in keys:
                groups.setdefault(key, []).append((path, data))

        seen_duplicate_paths = set()
        for key, items in groups.items():
            unique = []
            for item in items:
                if item[0] not in [x[0] for x in unique]:
                    unique.append(item)
            if len(unique) <= 1:
                continue
            keep = sorted(unique, key=lambda item: priority(item[0], item[1]), reverse=True)[0]
            for path, data in unique:
                if path == keep[0] or path in seen_duplicate_paths or path in disabled_paths:
                    continue
                seen_duplicate_paths.add(path)
                move_to_disabled(path, f"duplicate-of={keep[0].relative_to(ROOT)} key={key}", apply)

    if not apply:
        print("\nDry run only. Re-run with --apply to move files.")
    else:
        print("\nCleanup applied. Disabled targets were moved under targets/_disabled/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
