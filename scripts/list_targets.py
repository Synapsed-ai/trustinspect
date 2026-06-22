#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import sys

try:
    import yaml
except Exception as exc:
    print("Missing dependency: pyyaml. Install with: pip install pyyaml", file=sys.stderr)
    raise

ROOT = Path.cwd()
TARGET_DIRS = [ROOT / "examples" / "targets", ROOT / "targets" / "local"]


def _load_yaml(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        return {"_error": str(exc)}


def _target_id(data: dict, path: Path) -> str:
    return str(data.get("id") or data.get("target_id") or path.stem)


def _target_name(data: dict, path: Path) -> str:
    return str(data.get("name") or data.get("title") or _target_id(data, path))


def _target_url(data: dict) -> str:
    return str(data.get("url") or data.get("target_url") or "")


def _target_status(data: dict) -> str:
    status = data.get("status")
    if status:
        return str(status)
    if data.get("input_selector") and data.get("output_selector"):
        return "ready"
    return "selector_required"


def _target_type(data: dict) -> str:
    return str(data.get("category") or data.get("type") or data.get("target_type") or "-")


def _short(value: str, max_len: int = 74) -> str:
    value = value or ""
    return value if len(value) <= max_len else value[: max_len - 1] + "…"


def iter_targets():
    for target_dir in TARGET_DIRS:
        if not target_dir.exists():
            continue
        for path in sorted(target_dir.glob("*.y*ml")):
            data = _load_yaml(path)
            yield path, data


def main() -> int:
    rows = []
    for path, data in iter_targets():
        rows.append([
            _target_id(data, path),
            _target_name(data, path),
            _target_status(data),
            _target_type(data),
            _target_url(data),
            str(path.relative_to(ROOT)),
        ])

    if not rows:
        print("No targets found in examples/targets or targets/local.")
        return 0

    headers = ["id", "name", "status", "type", "url", "file"]
    widths = [min(max(len(str(r[i])) for r in rows + [headers]), 36 if i in (0, 1) else 22 if i in (2, 3) else 70) for i in range(len(headers))]

    print("TrustInspect targets")
    print("=" * 80)
    print("  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("-" * 80)
    for row in rows:
        print("  ".join(_short(str(row[i]), widths[i]).ljust(widths[i]) for i in range(len(headers))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
