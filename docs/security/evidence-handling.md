# Evidence handling and privacy

TrustInspect is an evidence-based testing tool. Generated reports and evidence artifacts may contain sensitive information, including prompts, model responses, screenshots, DOM snapshots, target URLs, generated dynamic tests, and target capability profiles.

## Automatic error diagnostics

When a Web UI test fails to execute, the scanner attempts to save a screenshot
and a DOM snapshot locally and attaches their paths to the error observation.
This diagnostic collection is automatic; no separate DOM opt-in is required by
the current scanner. A snapshot may contain hidden fields and state that a
screenshot does not show. DOM files use the `.html.txt` suffix and must be treated
as untrusted diagnostic data, not opened as executable HTML. Failure to capture
an artifact does not turn an execution error into a successful test.

## Sharing evidence

Before sharing reports or sample outputs, review them for:

- credentials or API keys;
- personal data or customer data;
- private prompts, hidden instructions, or system prompts;
- internal documents or retrieved context;
- target URLs, screenshots, DOM snapshots, and selector details;
- generated tests that may reveal internal assumptions about a target.

TrustInspect does not upload reports or evidence by default. Artifacts are written locally to the output path selected by the tester.

Release archives should be generated from Git-tracked files only, for example:

```bash
git archive --format=zip --output trustinspect-v0.3-alpha.zip HEAD
python scripts/maintenance/verify_release_artifact.py --artifact trustinspect-v0.3-alpha.zip
```

Do not include local runtime artifacts in public release bundles:

```text
.git/
.venv/
reports/
profiles/
generated_tests/
_archive/
trustinspect.egg-info/
.pytest_cache/
```
