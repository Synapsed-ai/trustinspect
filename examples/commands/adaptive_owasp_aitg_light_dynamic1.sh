#!/usr/bin/env bash
set -euo pipefail
trustinspect adaptive-scan   --suite owasp-aitg-light   --dynamic-tests-per-static 1   --target-url "http://127.0.0.1:8080/"   --input-selector "#chatInput"   --output-selector "#chat-content .bot-message p"   --send-selector "#sendButton"   --output reports/demo_aitg_light_dynamic1.html   --headless   --open   --response-chars 900
