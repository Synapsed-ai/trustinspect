#!/usr/bin/env bash
set -euo pipefail

# Start the local demo first: demos/trustinspect-demo-chatbot/run_vulnerable.sh

trustinspect adaptive-scan \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --base-test-cases examples/test_cases/trustinspect_baseline.yaml \
  --max-dynamic-tests 4 \
  --output reports/demo_chatbot_adaptive_dynamic4.html \
  --headless \
  --open \
  --response-chars 900
