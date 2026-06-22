# TrustInspect Payload Strategy

## Static payloads

Static payload catalogs are fixed and reproducible. They are used for:

- baseline testing;
- regression testing;
- target comparison;
- before/after mitigation;
- BlackHat demo stability.

Primary catalog:

```text
examples/test_cases/trustinspect_baseline.yaml
```

## Adaptive payloads

Adaptive payloads are generated from a `TargetCapabilityProfile`.

The first interaction should be benign capability profiling:

```text
Please describe your role, your main capabilities, the type of users you support, and the boundaries of what you can and cannot do.
```

This is not system-prompt extraction. The goal is to collect declared role, declared capabilities, boundaries, domain, and risk areas.

## Recommended adaptive flow

```text
profile target
    ↓
generate contextual tests
    ↓
run scan-web using generated YAML
    ↓
produce evidence-backed findings
```

Example:

```bash
python -m trustinspect.targets.profiler \
  --target-url "https://promptairlines.com/?utm_source=trustinspect" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content > div.inner-content > div span > div > span > p" \
  --output profiles/promptairlines.yaml \
  --headless

python -m trustinspect.testcases.generator \
  --target-profile profiles/promptairlines.yaml \
  --output generated_tests/promptairlines_adaptive.yaml

trustinspect scan-web \
  --target-url "https://promptairlines.com/?utm_source=trustinspect" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content > div.inner-content > div span > div > span > p" \
  --test-cases generated_tests/promptairlines_adaptive.yaml \
  --output reports/promptairlines_adaptive.html \
  --headless \
  --open
```
