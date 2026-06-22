# TrustInspect Web UI Engine

This patch moves the proven SynInspect EDU browser-execution capability into the public TrustInspect architecture as a TrustInspect scanner module.

## Positioning

The Web UI Engine is **not** a traditional web application security scanner. It does not test SQL injection, XSS in the application, authentication flaws, or proxy-based web vulnerabilities.

It is an execution engine for Trustworthy AI test cases. It sends structured AI test cases to LLM/chatbot interfaces and captures evidence from the model/application response.

## Flow

```text
TestCase YAML
  -> WebUiScanner
  -> EvidenceItem(prompt, response, screenshot, logs)
  -> Observation
  -> FindingEngine
  -> Assessment report
```

## CLI commands

Selector discovery:

```bash
trustinspect detect-selectors \
  --target-url "https://promptairlines.com/?utm_source=trustinspect" \
  --wait-time 15
```

Web UI scan:

```bash
trustinspect scan-web \
  --target-url "https://promptairlines.com/?utm_source=trustinspect" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content > div.inner-content > div:last-child span > div > span > p" \
  --test-cases examples/test_cases/owasp_light_full.yaml \
  --output reports/promptairlines.html \
  --headless \
  --open
```

## Evidence generated

For each test case, TrustInspect creates:

- prompt evidence;
- response evidence;
- screenshot evidence when available;
- execution metadata;
- classification and rationale.

If a selector or UI interaction fails, the observation is classified as `ERROR`, not as a model weakness.
