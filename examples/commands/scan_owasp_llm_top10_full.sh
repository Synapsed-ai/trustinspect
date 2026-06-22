#!/usr/bin/env bash
set -euo pipefail

trustinspect scan-web \
  --suite owasp-llm-top10-2025-full \
  --target-url "https://promptairlines.com/?utm_source=trustinspect" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content > div.inner-content > div span > div > span > p" \
  --output reports/owasp_llm_top10_full.html \
  --headless \
  --open \
  --response-chars 900
