# TrustInspect Architecture

TrustInspect is organized around a clean separation of responsibilities.

```text
trustinspect/
  core/          shared models and enums
  targets/       target profiles and profilers
  dynamic/       dynamic test engine
  testcases/     loaders, validators, and catalogs
  scanners/      execution engines: web UI, API, agentic
  analyzers/     response/evidence analysis
  evidence/      evidence storage and replay support
  findings/      observation -> finding conversion
  reporting/     HTML/JSON reports
  ui/            terminal UI
  cli.py         command-line entrypoint
```

## Pipeline

```text
Target Profiler
  -> Target Profile Normalizer
  -> Risk Mapper
  -> Dynamic Test Planner
  -> Template Engine
  -> Indicator Compiler
  -> Test Budget Manager
  -> Scanner
  -> Evidence Store
  -> Analyzer
  -> Findings Engine
  -> Report
```

## Separation of concerns

### Scanner

The scanner executes test cases and captures evidence. It should not decide whether a target is vulnerable.

### Analyzer

The analyzer classifies observations using test metadata, failure indicators, success indicators, and refusal/safe-deflection handling.

### Dynamic Engine

The dynamic engine creates contextual test cases from a target profile. It should produce full test cases, not raw prompts.

### Findings Engine

The findings engine converts observations into audit-ready findings. It should include impact, remediation, source test, evidence references, confidence, and severity.

## Static vs Dynamic Tests

Static tests are loaded from a catalog and should be executed as-is. Dynamic tests are generated from the target profile and limited with `--max-dynamic-tests`.

```text
static total = number of tests in baseline catalog
dynamic total = generated tests limited by --max-dynamic-tests
execution total = static total + dynamic total
```

## Trustworthiness dimensions

TrustInspect should map test cases and findings to dimensions such as:

- Security
- Privacy
- Robustness
- Safety
- Reliability
- Transparency
- Human Oversight
- Governance
