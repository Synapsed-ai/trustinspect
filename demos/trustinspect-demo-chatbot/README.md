# TrustInspect Demo Chatbot Local Target

This is a controlled local target for TrustInspect demos and regression testing.
It is **not a real LLM**. It is a deterministic LLM-like web chatbot that returns predictable responses so TrustInspect can demonstrate:

- static/fixed suite detection;
- dynamic contextual test generation;
- evidence collection;
- vulnerable vs hardened re-testing.

## Why it exists

Public targets such as PromptAirlines, Gandalf, GPA, HackMerlin, and institutional chatbots are useful, but they are not fully controlled. Their selectors, rate limits, and behavior may change. 

## Modes

### Vulnerable mode

Contains three intentionally weak response behaviors. With the current analyzer, the two sentinel violations are confirmed test-predicate findings; raw script-like text is a review-only observation, not evidence of browser execution:

| Static test | Intended weakness |
|---|---|
| OWASP-LLM01-LIGHT-001 | Instruction hierarchy override with `ACCESS_GRANTED_TEST` |
| OWASP-LLM05-LIGHT-001 | Unsafe output echo of script-like content |
| OWASP-LLM08-LIGHT-001 | Hidden instruction following with `TRUSTINSPECT_SENTINEL` |

Dynamic tests exercise additional contextual behaviors. Counts depend on the selected templates, test budget and analyzer semantics; do not assume a fixed number of findings:

- contextual sensitive data disclosure using fake travel assets;
- system/internal policy disclosure for the travel assistant;
- unauthorized booking/refund/action completion;
- domain boundary override;
- roleplay policy override;
- resource exhaustion/unbounded output.

All disclosed data is fake and local-only.

### Hardened mode

The same test plan should produce materially fewer findings:

- refuses sensitive data disclosure;
- refuses internal policy/system instruction disclosure;
- does not claim unauthorized actions;
- treats embedded instructions as untrusted data;
- refuses unsafe output echo;
- applies bounded output behavior.

## Run vulnerable mode

Terminal 1:

```bash
cd /path/to/trustinspect/demos/trustinspect-demo-chatbot
./run_vulnerable.sh
```

Terminal 2:

```bash
cd /path/to/trustinspect
source .venv/bin/activate
./demos/trustinspect-demo-chatbot/scan_owasp_light_static.sh
```

Expected for the current static-light fixture: two confirmed sentinel predicates, no execution errors, and review-only observations for inconclusive cases and raw markup.

## Run static + dynamic

Terminal 1:

```bash
./run_vulnerable.sh
```

Terminal 2:

```bash
cd /path/to/trustinspect
source .venv/bin/activate
./demos/trustinspect-demo-chatbot/scan_owasp_light_dynamic1.sh
```

Inspect both confirmed test-predicate findings and POSSIBLE observations; correlate each with its captured evidence.

## Run hardened comparison

Stop vulnerable mode, then start hardened mode:

```bash
./run_hardened.sh
```

Then run:

```bash
cd /path/to/trustinspect
source .venv/bin/activate
./demos/trustinspect-demo-chatbot/scan_hardened_comparison.sh
```

Expected: significantly fewer findings than vulnerable mode.

## Stable selectors

```text
input_selector:  #chatInput
output_selector: #chat-content .bot-message p
send_selector:   #sendButton
```

## Manual CLI examples

```bash
trustinspect scan-web \
  --suite owasp-llm-top10-2025-light \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --output reports/demo_chatbot_static.html \
  --headless \
  --open
```

```bash
trustinspect adaptive-scan \
  --suite owasp-llm-top10-2025-light \
  --dynamic-tests-per-static 1 \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --output reports/demo_chatbot_dynamic1.html \
  --headless \
  --open
```

See [local-browser validation](../../docs/testing/local-browser.md) for automated before/after checks.
