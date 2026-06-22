#!/usr/bin/env bash
set -euo pipefail
# Run from the TrustInspect project root, with the demo server running.
trustinspect adaptive-scan \
  --suite owasp-llm-top10-2025-light \
  --dynamic-tests-per-static 2 \
  --max-dynamic-tests 12 \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --output reports/demo_chatbot_owasp_light_dynamic2.html \
  --headless \
  --open \
  --response-chars 900
