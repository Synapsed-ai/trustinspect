# TrustInspect Repository Structure

Recommended professional layout:

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

targets/
  builtin/       # official target profiles distributed with the tool
  local/         # locally calibrated target profiles, usually gitignored
  disabled/      # disabled profiles kept for traceability

examples/
  commands/      # runnable CLI examples
  test_cases/    # sample static test case files
  test_suites/   # sample suite definitions
  dynamic_templates/ # example dynamic templates if not moved to resources

demos/
  trustinspect-demo-chatbot/

docs/
  architecture.md
  demo/
  blackhat-arsenal/
  payloads/
  maintenance/

assets/
  report/

tools/
  migrations/    # historical patch/migration scripts

scripts/
  # stable utility scripts only; no one-off patch scripts
```

Rules:

- Do not store official target profiles under `examples/targets`.
- Do not keep one-off `patch_*.py` scripts in the project root.
- Do not commit local calibration output unless intentionally promoted to `targets/builtin`.
- Generated reports should stay under `reports/` and usually be gitignored.
