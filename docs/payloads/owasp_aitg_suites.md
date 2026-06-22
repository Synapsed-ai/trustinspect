# OWASP AITG Suites for TrustInspect

This patch adds two TrustInspect-native OWASP AI Testing Guide suites:

- `owasp-aitg-light`: 32 base tests/checks, one for each OWASP AITG test ID.
- `owasp-aitg-full`: 160 scenarios, five variants for each OWASP AITG test ID.

`execution_mode` is intentionally not used. TrustInspect is focused on LLM and agentic applications; every suite item is represented as an evidence-oriented TrustInspect test/check with `objective`, `prompt`, `expected_behavior`, `failure_indicators`, `success_indicators`, and `evidence_objective`.

The suite is aligned with the OWASP AITG structure: 14 AI Application tests, 7 AI Model tests, 6 AI Infrastructure tests, and 5 AI Data tests. The AI Data Testing entries follow the official scope: training data exposure, runtime exfiltration, dataset diversity and coverage, harmful content in data, and data minimization/consent.

Official sources:

- https://github.com/OWASP/www-project-ai-testing-guide/blob/main/Document/README.md
- https://github.com/OWASP/www-project-ai-testing-guide/blob/main/Document/content/3.4_AI_Data_Testing.md

## Suggested commands

```bash
trustinspect scan-web   --suite owasp-aitg-light   --target-url "http://127.0.0.1:8080/"   --input-selector "#chatInput"   --output-selector "#chat-content .bot-message p"   --send-selector "#sendButton"   --output reports/demo_aitg_light.html   --headless --open
```

```bash
trustinspect adaptive-scan   --suite owasp-aitg-light   --dynamic-tests-per-static 1   --target-url "http://127.0.0.1:8080/"   --input-selector "#chatInput"   --output-selector "#chat-content .bot-message p"   --send-selector "#sendButton"   --output reports/demo_aitg_light_dynamic.html   --headless --open
```

For `owasp-aitg-full`, consider using a cap for dynamic variants:

```bash
--suite owasp-aitg-full --dynamic-tests-per-static 1 --max-dynamic-tests 50
```
