#!/usr/bin/env bash
set -euo pipefail
# Run from the TrustInspect project root.
trustinspect scan-web \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --test-cases examples/test_cases/trustinspect_baseline.yaml \
  --output reports/demo_chatbot_static.html \
  --headless \
  --open \
  --response-chars 900
