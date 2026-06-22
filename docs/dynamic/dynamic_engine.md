# TrustInspect Dynamic Test Engine

The Dynamic Test Engine turns a target capability profile into complete,
reproducible, evidence-ready Trustworthy AI test cases.

It does not simply invent payloads. It builds structured test cases with:

- target context
- risk area
- prompt
- expected behavior
- structured failure indicators
- success indicators
- generation reason
- source metadata

## Architecture

```text
Target Profile
  -> Profile Normalizer
  -> Risk Mapper
  -> Dynamic Test Planner
  -> Template Engine
  -> Indicator Compiler
  -> Dynamic Test Budget
  -> Generated Test Catalog
```

## Static vs Dynamic

Static tests are loaded from the baseline catalog and should normally all be
executed. Dynamic tests are generated from the target profile and controlled by:

```bash
--max-dynamic-tests N
```

Example:

```text
8 static baseline tests + --max-dynamic-tests 4 = 12 total tests
```

## Indicator semantics

Dynamic tests use structured indicators such as:

```yaml
failure_indicators:
  - value: TRUSTINSPECT_SENTINEL
    match: ends_with_unquoted
    quoted_mentions_allowed: false
```

This prevents false positives where a target merely quotes or explains the
sentinel instead of executing the hidden instruction.
