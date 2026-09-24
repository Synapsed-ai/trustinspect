# Static and contextual test catalogs

Static suites provide reproducible inputs. The baseline is
`examples/test_cases/trustinspect_baseline.yaml`; named suites are resolved by
the registry and distributed through the explicit resource allowlist.

Contextual tests are deterministic variants generated from the static suite and
a Target Capability Profile. Capability profiling records what a target says
about its role and boundaries; it is not independent verification of those claims.

For a controlled local run, start the demo as described in its
[README](../../demos/trustinspect-demo-chatbot/README.md), then run:

```bash
trustinspect adaptive-scan \
  --suite owasp-llm-top10-2025-light \
  --dynamic-tests-per-static 1 --max-dynamic-tests 4 \
  --target-profile demos/trustinspect-demo-chatbot/target_profile.yaml \
  --target-url http://127.0.0.1:8080/ \
  --input-selector '#chatInput' \
  --output-selector '#chat-content .bot-message p' \
  --send-selector '#sendButton' \
  --output reports/local-adaptive.html --headless
```

This schedules ten static cases and up to four dynamic variants. Inspect both
confirmed test predicates and POSSIBLE observations. A textual claim that an
action occurred is not proof of a real side effect. See
[indicator semantics](../implementation/indicator-match-semantics.md).
