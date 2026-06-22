# TrustInspect Project Structure

Recommended repository layout for the public TrustInspect project.

```text
trustinspect/
  analyzers/              # response and evidence analysis
  core/                   # data models, enums, shared config
  dynamic/                # dynamic test engine
  evidence/               # evidence store, screenshots, DOM snapshots, replay artifacts
  findings/               # observation -> finding mapping
  interactive/            # interactive launcher and calibration UX
  reporting/              # HTML/JSON report generation
  scanners/               # Web UI/API/agentic scanners
  suites/                 # suite registry and loading helpers
  targets/                # target profile loading/helpers
  testcases/              # test case loaders, validators, schemas
  ui/                     # terminal/phosphor UI helpers

assets/
  report/                 # report header images and static report assets

targets/
  builtin/                # curated target profiles shipped with TrustInspect
  local/                  # locally calibrated targets; user-specific
  _disabled/              # disabled or archived target profiles

test_suites/
  static/                 # static test suites: OWASP LLM, TrustInspect baseline, AITG

test_templates/
  dynamic/                # dynamic test templates used by the engine

demos/
  trustinspect-demo-chatbot/

docs/
  architecture/
  blackhat-arsenal/
  demo/
  payloads/
  targets/
  release-notes/

tests/
  ...

scripts/
  repo_cleanup.py         # repo maintenance utilities only; no temporary patch scripts

reports/                 # generated runtime reports; gitignored
generated/               # generated profiles/test cases; gitignored
```

## Design rules

- `examples/` should be used only for commands or teaching examples, not runtime registries.
- Built-in target profiles belong in `targets/builtin/`.
- User-calibrated targets belong in `targets/local/`.
- Static test suites belong in `test_suites/static/`.
- Dynamic templates belong in `test_templates/dynamic/`.
- Temporary patch scripts should not live in the repository; archive or delete them.
- `reports/`, `generated/`, `profiles/`, and runtime artifacts should be ignored by git.

## Migration

Run from repo root:

```bash
python scripts/repo_cleanup.py          # dry-run
python scripts/repo_cleanup.py --apply  # apply
```
