# TrustInspect Interactive Launcher and Target Registry

This patch adds a user-friendly launcher for TrustInspect.

Running:

```bash
trustinspect
```

with no arguments opens an interactive workflow:

1. choose a known target or add/calibrate a new target;
2. select the static test suite;
3. decide whether to add dynamic tests per static test;
4. run the assessment and open the HTML report.

## Known targets

Known targets are stored as YAML files in:

```text
examples/targets/
targets/local/
```

Built-in targets can be `ready` or `selector_required`.

- `ready`: selectors are already known.
- `selector_required`: target is known, but the user must calibrate input/output selectors locally.

## New target wizard

For a new target, the launcher asks for:

- target URL;
- display name;
- input selector;
- output selector;
- optional send selector;
- optional iframe selector.

If the selectors validate in future versions, the target can be saved under:

```text
targets/local/<target-id>.yaml
```

## Static and dynamic test selection

The launcher supports:

- TrustInspect Baseline;
- OWASP LLM Top 10 2025 Light;
- OWASP LLM Top 10 2025 Full;
- OWASP AI Testing Guide 32 (planned placeholder).

Dynamic tests follow the current TrustInspect semantics:

```text
--dynamic-tests-per-static N
```

That means N dynamic contextual variants are generated for each static test selected by the user.
