#!/usr/bin/env bash
set -euo pipefail

python -m trustinspect.dynamic.engine \
  --target-profile profiles/promptairlines.yaml \
  --template-dir examples/dynamic_templates \
  --max-dynamic-tests 4 \
  --output generated_tests/promptairlines_dynamic.yaml

trustinspect scan-web \
  --target-url "https://promptairlines.com/?utm_source=trustinspect" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content > div.inner-content > div span > div > span > p" \
  --test-cases generated_tests/promptairlines_dynamic.yaml \
  --output reports/promptairlines_dynamic_only.html \
  --headless \
  --open \
  --response-chars 900
