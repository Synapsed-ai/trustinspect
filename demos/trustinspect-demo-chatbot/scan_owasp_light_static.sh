#!/usr/bin/env bash
set -euo pipefail
# Run from the TrustInspect project root, with the demo server running.
trustinspect scan-web \
  --suite owasp-llm-top10-2025-light \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --output reports/demo_chatbot_owasp_light_static.html \
  --headless \
  --open \
  --response-chars 900
