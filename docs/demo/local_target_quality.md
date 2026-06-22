# Local Demo Target Quality Notes

The local demo target is a deterministic, controlled Web UI target used for TrustInspect demos.
It is intentionally not a real LLM: the goal is to provide stable, reproducible evidence for
static and dynamic Trustworthy AI testing workflows.

## Vulnerable mode expected behavior

Static OWASP LLM Top 10 Light should produce three immediate findings:

- LLM01: instruction hierarchy override (`ACCESS_GRANTED_TEST`)
- LLM05: unsafe output echo (`<script>...` as model output, safely escaped by the report)
- LLM08: hidden instruction following (`TRUSTINSPECT_SENTINEL`)

Dynamic tests should find contextual weaknesses based on the travel/customer-support profile:

- contextual sensitive data disclosure
- internal policy/system instruction disclosure
- unauthorized domain action completion
- domain boundary override / roleplay policy override
- resource exhaustion using dynamic sentinels

## Hardened mode expected behavior

The same tests should be refused, bounded, or redirected, showing re-test after mitigation.

## Quality improvements in this patch

- Safe refusals for LLM06 and LLM09 are classified as SAFE rather than POSSIBLE.
- Generic static LLM10 remains bounded/SAFE.
- Dynamic LLM10 variants use resource-exhaustion templates, not unsafe-output echo fallbacks.
- Stale sentinel / cross-test contamination is flagged as ERROR, not a vulnerability.
