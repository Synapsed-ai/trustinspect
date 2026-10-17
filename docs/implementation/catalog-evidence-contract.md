# Catalog input and evidence contract

## Validate before executing

CLI scans and library loading validate the original YAML before constructing
`TestCase` objects. Supported envelopes are a list, a `test_cases` list, a `tests`
list, and a single test mapping. Every row must be a mapping. The validator and
loader share the same rules and aliases; malformed rows are not silently dropped.
Static catalogs are checked before selector discovery or target profiling, including
in adaptive mode. Invalid input raises a configuration error rather than producing
a finding about the target.

`failure_indicators` must be a list of valid strings or structured indicators.
Missing/null values retain the existing no-explicit-indicators behavior; an empty
list is also allowed, with a validation warning. False, zero, strings and mappings
are not substitutes for a list. Serialization checks the same boundary so that an
invalid value cannot be converted to apparently valid character-level predicates.
Conflicting ID/prompt aliases, empty prompts and duplicate IDs are errors.

## A match and a finding are different claims

The optional `evidence_role` field is either `failure` (the compatibility default)
or `review`. A matching review indicator contributes a `POSSIBLE VULNERABILITY`
observation, not a confirmed finding. The signal, prompt and response remain in
the report for investigation. It is never silently discarded as safe behavior.

```yaml
failure_indicators:
  - value: '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    match: regex
    evidence_role: review
```

An email-shaped value alone does not establish that the value is confidential or
that the caller was unauthorized. Similarly, translating or decoding a value
supplied in the test input does not independently establish extraction of a secret
from the target. An output-filtering requirement may intentionally forbid such a
value; author that separate requirement explicitly instead of labeling all input
transformations as exfiltration.

For a controlled disclosure test, put a synthetic protected value in the target's
protected context, omit it from the attack prompt, and define an exact predicate
for its appearance. Setting `negative_context_enabled: false` and allowing quoted
mentions makes the value count even when disclosed inside a disclaimer or quotes.
The tester must establish the confidentiality and authorization assumptions; the
analyzer cannot infer them solely from a string.

An independent failure predicate still takes precedence over review signals,
refusals and corrections elsewhere in the response. Existing instruction-following
sentinels and explicit output-length limits are not blanket-downgraded.
Review-only match types cannot be promoted by setting `evidence_role: failure`.

## Claim-aware text signals

`asserted_claim` is a review-only literal signal with narrow English-language
rules for explicit rejection of the matched claim. For example, `The claim that
<value> is false` can establish a correction of that occurrence. A positive
occurrence elsewhere is still retained for review. Conditional and interrogative
forms are not treated as confirmed corrections. Protected literal predicates and
length measurements do not use these claim-rejection rules.

These heuristics are not a semantic model or multilingual accuracy benchmark.
Unresolved wording remains reviewable. Confidence scores are heuristic scores,
not calibrated probabilities. `SAFE` describes the captured response to the
specific predicate, never the safety of the entire application.

## Scope of the catalog corrections

The initial changes cover LLM02 and LLM09 in `owasp-llm-top10-2025-light`, and
LLM02-002, LLM02-033 and LLM02-038 in the full catalog. Payloads, IDs, mappings and
case counts are unchanged. This is not a certification that every other predicate
has been independently calibrated. The regression tests include both negative
controls and independent positive disclosure/instruction-following controls.

## Operational behavior

Browser interaction and automatic DOM capture on execution errors are retained.
See [evidence handling](../security/evidence-handling.md). No prompt, screenshot,
video, positioning matrix or runtime interaction is removed by these evaluator
and input-contract changes.
