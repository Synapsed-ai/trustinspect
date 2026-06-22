# TrustInspect Dynamic Engine Quality Pack

This pack updates the dynamic test templates so generated tests are reusable across target domains, measurable, and less prone to false positives.

## Principles

Dynamic tests should not be arbitrary jailbreak prompts. Each generated test case should include:

- target-specific context;
- a clear trustworthiness risk area;
- an expected safe behavior;
- structured failure indicators;
- a generation reason;
- benign sentinels for measurable execution.

## Static vs Dynamic

Static tests are loaded from the base catalog and should be executed as provided.
Dynamic tests are generated from the target capability profile and limited by `--max-dynamic-tests`.

## Indicator semantics

Prefer structured indicators, for example:

```yaml
failure_indicators:
  - value: TRUSTINSPECT_SENTINEL
    match: ends_with_unquoted
    quoted_mentions_allowed: false
```

This prevents benign mentions of a sentinel from being treated as execution.
