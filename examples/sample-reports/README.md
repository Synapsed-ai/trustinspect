# Generate current sample reports

Historical reports and screenshots were produced by older analyzer versions and
are no longer shipped as evidence of current behavior. Their original versions
remain in Git history; current outputs must be generated from the version under test.

For a synthetic formatting example (no browser or AI endpoint):

```bash
trustinspect demo-report --output reports/demo.html
```

For a reproducible browser assessment use the controlled local demo and the
[regression instructions](../../docs/testing/local-browser.md). The Local Browser
Regression workflow retains its JSON/HTML evidence and browser screenshots as
short-lived artifacts. These fixtures test the tool, not the safety of a real model.
