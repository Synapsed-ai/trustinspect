#!/usr/bin/env bash
set -euo pipefail
trustinspect scan-web   --suite owasp-aitg-full   --target-url "http://127.0.0.1:8080/"   --input-selector "#chatInput"   --output-selector "#chat-content .bot-message p"   --send-selector "#sendButton"   --output reports/demo_aitg_full.html   --headless   --open   --response-chars 900
