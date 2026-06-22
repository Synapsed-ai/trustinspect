# TrustInspect Repository Structure

TrustInspect separates product code, target configurations, test assets, generated evidence and demos.

## Product code

```text
trustinspect/
  core/          Data models and shared types
  scanners/      Web UI / API / future agentic scanners
  analyzers/     Evidence and response analyzers
  dynamic/       Dynamic test generation engine
  testcases/     Test case loaders, validators and schemas
  targets/       Target registry/profiling logic
  reporting/     HTML/JSON report generation
  interactive/   Interactive launcher and calibration UX
  ui/            Terminal UI helpers
```

## Target configuration

```text
targets/
  builtin/       Curated targets distributed with the tool
  local/         Locally calibrated targets saved by the tester
  disabled/      Disabled/archived targets
```

Operational target profiles should live under `targets/`, not `examples/`.

## Test assets

```text
examples/test_cases/        TrustInspect baseline/static catalogs
examples/test_suites/       Named suites such as OWASP LLM Top 10 light/full
examples/dynamic_templates/ Dynamic test templates
examples/test_templates/    Older or experimental template assets
examples/commands/          Reproducible command examples
```

## Runtime outputs

```text
reports/          HTML reports and evidence screenshots/DOM snapshots
generated_tests/  Dynamic test catalogs generated at runtime
profiles/         Target profiles generated at runtime
```

These folders are intentionally gitignored.

## Prototype artefacts

Patch scripts and `README_*_PATCH.md` files were useful during rapid prototyping but should not remain in the root. The cleanup utility archives them under `_archive/prototype-patches/<timestamp>/`.
