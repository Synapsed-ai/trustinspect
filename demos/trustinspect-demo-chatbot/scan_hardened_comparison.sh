#!/usr/bin/env bash
set -euo pipefail
# Start hardened mode in another terminal first, then run this from project root.
trustinspect adaptive-scan \
  --suite owasp-llm-top10-2025-light \
  --dynamic-tests-per-static 1 \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --output reports/demo_chatbot_hardened_owasp_light_dynamic1.html \
  --headless \
  --open \
  --response-chars 900
