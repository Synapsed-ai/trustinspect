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
  --target-url "http://127.0.0.1:8080/" \
  --wait-time 15
```

Web UI scan:

```bash
trustinspect scan-web \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --test-cases examples/test_cases/owasp_light_full.yaml \
  --output reports/demo_chatbot.html \
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
