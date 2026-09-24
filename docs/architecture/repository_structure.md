# Repository layout and runtime resources

The current layout separates the Python package, reviewed input catalogs, the
controlled local demo, documentation and generated evidence.

```text
trustinspect/                 # Python source
  analyzers/                  # response classification
  core/                       # models, engine versions, shared indicator contract
  dynamic/                    # deterministic test generation
  evidence/                   # evidence storage
  findings/                   # observation-to-finding mapping
  interactive/                # launcher and calibration
  reporting/templates/        # escaped HTML report templates
  scanners/web_ui/            # Selenium transport and response capture
  suites/                     # named suite registry
  targets/                    # target registry and capability profiling
  testcases/                  # catalog loading and validation
  ui/                         # terminal presentation
  resources.py                # installed/source resource resolution
  _resource_manifest.json     # explicit runtime-data allowlist
examples/
  test_cases/                 # baseline and compatibility catalogs
  test_suites/                # OWASP LLM catalogs
  dynamic_templates/          # contextual generation templates
  sample-reports/README.md    # instructions to generate current examples
suites/owasp/                 # authoritative AITG light/full catalogs
targets/builtin/              # bundled target definitions
demos/trustinspect-demo-chatbot/
tests/                       # unit and contract tests
  browser/                   # opt-in real local-browser regressions
scripts/maintenance/         # validation utilities and legacy migration helpers
.github/workflows/           # source, installed-package and browser checks
```

`setup.py` copies the 18 allowlisted runtime data files into `trustinspect/_data/`
at build time. The input files remain authoritative; generated copies are not
committed. The packaging workflow rebuilds a wheel from its source distribution
and verifies installed resources from outside the checkout. See
[installation](../installation.md) for supported workflows and constraints.

Local calibrated targets and disable overrides live under `targets/local/`;
archives under `targets/disabled/`. These are workspace state, not changes to
installed built-in definitions. Reports, profiles and generated tests are also
workspace outputs. Inspect all evidence before sharing it.

Old screenshot/report outputs have been retired from the current tree, not from
Git history. The browser workflow provides short-lived evidence tied to the
commit under test. The local demo uses deterministic responses, not a real LLM.

## Changes that are not part of this cleanup

No catalog migration or automatic deletion of legacy maintenance scripts is
performed here. Earlier layout proposals are not instructions to run a migration.
Moving resource inputs requires a coordinated update of the allowlist, build,
registry, examples and tests. API and agent-trace adapters remain roadmap items.
