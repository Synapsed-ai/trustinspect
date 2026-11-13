#!/usr/bin/env bash
set -euo pipefail

# Start the local demo first: demos/trustinspect-demo-chatbot/run_vulnerable.sh

python -m trustinspect.dynamic.engine \
  --target-profile demos/trustinspect-demo-chatbot/target_profile.yaml \
  --template-dir examples/dynamic_templates \
  --max-dynamic-tests 4 \
  --output generated_tests/demo_chatbot_dynamic.yaml

trustinspect scan-web \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --test-cases generated_tests/demo_chatbot_dynamic.yaml \
  --output reports/demo_chatbot_dynamic_only.html \
  --headless \
  --open \
  --response-chars 900
