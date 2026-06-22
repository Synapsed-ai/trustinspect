# TrustInspect Repository Structure

This structure separates source code, target profiles, static suites, dynamic templates, demos, documentation and generated outputs.

## Proposed structure

```text
trustinspect/
  analyzers/
  core/
  dynamic/
  evidence/
  findings/
  interactive/
  reporting/
  scanners/
  suites/
  targets/
  testcases/
  ui/

assets/
  report/

docs/
  architecture/
  blackhat-arsenal/
  demo/
  payloads/
  targets/

targets/
  builtin/
  local/
  disabled/

examples/
  commands/
  test_cases/
  test_suites/
  dynamic_templates/

demos/
  trustinspect-demo-chatbot/

scripts/
  maintenance/

tests/
```

## Target profiles

Target profiles should not live under `examples/targets/`. They are operational configuration used by TrustInspect.

Use:

```text
targets/builtin/    # distributed with the project
targets/local/      # calibrated on the tester machine
targets/disabled/   # disabled or archived target profiles
```

## Generated outputs

Generated reports and transient outputs should not be committed:

```text
reports/
generated_tests/
profiles/
_archive/
```

## Patch scripts

Root-level files like `patch_*.py` were useful during rapid prototyping, but they should not remain in a professional repository root. The cleanup script archives them under:

```text
_archive/repo-cleanup/<timestamp>/legacy_patch_scripts/
```
