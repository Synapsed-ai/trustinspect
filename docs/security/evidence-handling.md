# Evidence handling and privacy

TrustInspect is an evidence-based testing tool. Generated reports and evidence artifacts may contain sensitive information, including prompts, model responses, screenshots, DOM snapshots, target URLs, generated dynamic tests, and target capability profiles.

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
