#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[2]
src = root / "tests" / "test_demo_target_quality.py"
if not src.exists():
    raise SystemExit(f"Expected test file not found: {src}")
print(f"[+] test_demo_target_quality.py ready: {src}")
print("[+] This test uses importlib to load demos/trustinspect-demo-chatbot/app/main.py despite the hyphenated directory name.")
