#!/usr/bin/env bash
set -euo pipefail
# Run from the TrustInspect project root.
trustinspect adaptive-scan \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --base-test-cases examples/test_cases/trustinspect_baseline.yaml \
  --max-dynamic-tests 4 \
  --output reports/demo_chatbot_adaptive.html \
  --headless \
  --open \
  --response-chars 900
