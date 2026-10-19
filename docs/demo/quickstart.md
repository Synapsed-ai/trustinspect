# TrustInspect Demo Quickstart

These steps use the bundled local demo chatbot. Start it first in a separate
terminal:

```bash
demos/trustinspect-demo-chatbot/run_vulnerable.sh
```

## 1. Validate templates and catalogs

```bash
python -m trustinspect.dynamic.validate_templates examples/dynamic_templates
python -m trustinspect.testcases.validator examples/test_cases/trustinspect_baseline.yaml
```

## 2. Profile a target

```bash
trustinspect profile-target \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --output profiles/demo_chatbot.yaml \
  --headless
```

## 3. Generate dynamic tests

```bash
python -m trustinspect.dynamic.engine \
  --target-profile profiles/demo_chatbot.yaml \
  --template-dir examples/dynamic_templates \
  --max-dynamic-tests 4 \
  --output generated_tests/demo_chatbot_dynamic.yaml
```

## 4. Run dynamic-only scan

```bash
trustinspect scan-web \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --test-cases generated_tests/demo_chatbot_dynamic.yaml \
  --output reports/demo_chatbot_dynamic_only.html \
  --headless \
  --open \
  --response-chars 900
```

## 5. Run full adaptive scan

```bash
trustinspect adaptive-scan \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --base-test-cases examples/test_cases/trustinspect_baseline.yaml \
  --max-dynamic-tests 4 \
  --output reports/demo_chatbot_adaptive_dynamic4.html \
  --headless \
  --open \
  --response-chars 900
```

## Demo narrative

1. TrustInspect profiles the target with a benign prompt.
2. It infers domain, style, capabilities, boundaries, sensitive assets, and risk areas.
3. It generates deterministic contextual test cases.
4. It executes all static tests and selected dynamic tests.
5. It captures evidence.
6. It classifies observations.
7. It generates findings and an HTML report.
