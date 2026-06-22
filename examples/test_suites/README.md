# TrustInspect Static Test Suites

This directory contains static, reproducible TrustInspect test catalogs.

## Available suites

| Suite ID | File | Purpose |
|---|---|---|
| `owasp-llm-top10-2025-light` | `owasp_llm_top10_2025_light.yaml` | 10 curated tests: one representative test for each OWASP Top 10 LLM 2025 category. Recommended for demos and smoke tests. |
| `owasp-llm-top10-2025-full` | `owasp_llm_top10_2025_full.yaml` | Full converted corpus from the uploaded OWASP Top 10 LLM 2025 payloads. Contains 226 tests. Recommended for longer assessments and regression runs. |
| `trustinspect-baseline` | `../test_cases/trustinspect_baseline.yaml` | TrustInspect-native baseline tests. |

## Recommended workflow

Quick smoke test:

```bash
trustinspect scan-web \
  --suite owasp-llm-top10-2025-light \
  --target-url "https://promptairlines.com/?utm_source=trustinspect" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content > div.inner-content > div span > div > span > p" \
  --output reports/owasp_light.html \
  --headless \
  --open
```

Adaptive assessment using OWASP static tests as the baseline:

```bash
trustinspect adaptive-scan \
  --suite owasp-llm-top10-2025-light \
  --max-dynamic-tests 4 \
  --target-url "https://promptairlines.com/?utm_source=trustinspect" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content > div.inner-content > div span > div > span > p" \
  --output reports/owasp_light_plus_dynamic.html \
  --headless \
  --open
```

Full run:

```bash
trustinspect scan-web --suite owasp-llm-top10-2025-full ...
```

Note: the full corpus is intentionally broad. Use it for longer runs; use the light suite for demos.
