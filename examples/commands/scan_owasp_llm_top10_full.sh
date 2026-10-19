#!/usr/bin/env bash
set -euo pipefail

trustinspect scan-web \
  --suite owasp-llm-top10-2025-full \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --output reports/owasp_llm_top10_full.html \
  --headless \
  --open \
  --response-chars 900
