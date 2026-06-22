#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

ROOT = Path.cwd()
TS = time.strftime('%Y%m%d-%H%M%S')
ARCHIVE = ROOT / '_archive' / 'generated-outputs' / TS
GENERATED_DIRS = ['reports', 'generated_tests', 'profiles']


def move_dir(name: str, dry_run: bool) -> None:
    src = ROOT / name
    if not src.exists():
        return
    dst = ARCHIVE / name
    if dry_run:
        print(f'[dry-run] move {src} -> {dst}')
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    (ROOT / name).mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description='Archive generated reports/profiles/tests.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true')
    group.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    for name in GENERATED_DIRS:
        move_dir(name, dry_run=args.dry_run)

    if args.apply:
        print(f'Archived generated outputs under: {ARCHIVE.relative_to(ROOT)}')
    else:
        print('Dry-run complete.')


if __name__ == '__main__':
    main()
