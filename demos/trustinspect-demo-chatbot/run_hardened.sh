#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 app/main.py --mode hardened --host 127.0.0.1 --port 8080
