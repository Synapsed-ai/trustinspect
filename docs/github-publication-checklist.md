# TrustInspect GitHub Publication Checklist

This checklist prepares TrustInspect for a public `v0.3-alpha` GitHub release.

## 1. Repository cleanup

Run:

```bash
python scripts/maintenance/github_preflight.py
python scripts/maintenance/cleanup_public_repo.py --dry-run
```

If the dry run looks safe:

```bash
python scripts/maintenance/cleanup_public_repo.py --apply
```

Expected cleanup:

- archive root `README_*_PATCH.md` files;
- archive root `patch_*.py` scripts;
- archive `*_patch/` directories;
- remove Python caches;
- ignore runtime artifacts;
- normalize target folders.

## 2. Runtime artifacts

Do not commit:

```text
reports/
profiles/
generated_tests/
targets/local/*.yaml
_archive/
```

Only curated reports should be committed under:

```text
examples/sample-reports/
```

## 3. Target registry

Use:

```text
targets/builtin/   # built-in target definitions
targets/local/     # local calibrated targets, gitignored
targets/disabled/  # archived disabled targets, gitignored
```

`examples/targets/` should not be used for operational target configs.

## 4. Public target status

Recommended public status:

```text
ready:
- TrustInspect Demo Chatbot local
- PromptAirlines, if selectors are stable

selector_required / experimental:
- Gandalf
- GPA
- HackMerlin
- Immersive Labs
```

## 5. Test suites

Before publishing, validate:

```bash
python -m trustinspect.testcases.validator suites/owasp/aitg-light.yaml
python -m trustinspect.testcases.validator suites/owasp/aitg-full.yaml
python -m trustinspect.testcases.validator suites/owasp/llm-top10-2025-light.yaml
python -m trustinspect.testcases.validator suites/owasp/llm-top10-2025-full.yaml
```

## 6. Report template

Report template requirements:

- no embedded base64 PNG header;
- no executable JavaScript;
- restrictive CSP;
- suite metadata populated;
- duration populated;
- observations sorted by severity;
- full evidence available in details sections.

Check:

```bash
python scripts/maintenance/github_preflight.py
```

## 7. Minimal CI

Run:

```bash
pytest -q
```

At minimum, CI should cover:

- target registry loading;
- suite registry loading;
- suite validation;
- dynamic generation;
- report sanitization;
- output capture guard;
- demo chatbot behavior.

## 8. Version and release notes

For the first public release:

```text
v0.3-alpha
```

Update:

```text
trustinspect/__init__.py
README.md
docs/release-notes/v0.3-alpha.md
```

## 9. Legal and attribution

Ensure:

- Apache-2.0 license present;
- SECURITY.md present;
- NOTICE present;
- OWASP references are attributed correctly;
- no implication that TrustInspect is an official OWASP project unless formally accepted.

## 10. Final command

```bash
git init
git add .
git status
```

Review carefully before first commit.
