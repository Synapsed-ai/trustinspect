#!/usr/bin/env bash
set -euo pipefail

python -m trustinspect.dynamic.validate_templates examples/dynamic_templates
python -m trustinspect.testcases.validator examples/test_cases/trustinspect_baseline.yaml

if [ -f generated_tests/promptairlines_dynamic.yaml ]; then
  python -m trustinspect.testcases.validator generated_tests/promptairlines_dynamic.yaml
fi
