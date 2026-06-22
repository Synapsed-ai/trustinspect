#!/usr/bin/env bash
set -euo pipefail

trustinspect adaptive-scan \
  --target-url "https://promptairlines.com/?utm_source=trustinspect" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content > div.inner-content > div span > div > span > p" \
  --base-test-cases examples/test_cases/trustinspect_baseline.yaml \
  --max-dynamic-tests 4 \
  --output reports/promptairlines_adaptive_dynamic4.html \
  --headless \
  --open \
  --response-chars 900
