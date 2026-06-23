# Security Policy

## Responsible use

TrustInspect is intended for authorized testing of LLM, RAG, chatbot, and agentic applications.

Use it only on systems you own, operate, or are explicitly authorized to test.

## Reporting vulnerabilities in TrustInspect

Please do not publicly disclose security vulnerabilities in TrustInspect before maintainers have had a reasonable opportunity to investigate and release a fix.

Report suspected vulnerabilities privately to the maintainers through the preferred project contact channel.

Include:

- affected version or commit;
- reproduction steps;
- impact;
- affected component;
- proof-of-concept if safe to share.

## Report safety

TrustInspect treats target responses as untrusted content. Reports should remain non-executable and use restrictive rendering controls.

If you find a report rendering issue such as script execution, HTML injection, or unsafe local file access, treat it as a security issue.

## Evidence and report handling

TrustInspect is an evidence-based testing tool. Assessment outputs may contain sensitive prompts, model responses, screenshots, DOM snapshots, target URLs, generated dynamic tests, and target capability profiles.

Before sharing reports, sample outputs, screenshots, or evidence folders, reviewers should verify that they do not contain customer data, credentials, secrets, private prompts, internal system prompts, proprietary documents, or other sensitive material.

For release artifacts, do not include local runtime outputs such as `reports/`, `profiles/`, `generated_tests/`, `_archive/`, `.venv/`, `.pytest_cache/`, or `trustinspect.egg-info/`. Build public release archives from Git-tracked files only, for example with `git archive`.
