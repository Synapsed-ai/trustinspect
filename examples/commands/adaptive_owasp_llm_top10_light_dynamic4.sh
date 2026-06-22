#!/usr/bin/env bash
set -euo pipefail

trustinspect adaptive-scan \
  --suite owasp-llm-top10-2025-light \
  --max-dynamic-tests 4 \
  --target-url "https://promptairlines.com/?utm_source=trustinspect" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content > div.inner-content > div span > div > span > p" \
  --output reports/owasp_llm_top10_light_dynamic4.html \
  --headless \
  --open \
  --response-chars 900
