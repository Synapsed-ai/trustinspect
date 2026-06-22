# OWASP Top 10 LLM 2025 Payload Review for TrustInspect

## Source reviewed

Uploaded source package:

```text
OWASP-TOP-10-LLM-2025.zip
```

The package contains 10 JSON files, one per OWASP Top 10 LLM 2025 category.

## Inventory

| OWASP category | Tests in uploaded corpus |
|---|---:|
| LLM01 Prompt Injection | 41 |
| LLM02 Sensitive Information Disclosure | 41 |
| LLM03 Supply Chain | 40 |
| LLM04 Data and Model Poisoning | 35 |
| LLM05 Improper Output Handling | 33 |
| LLM06 Excessive Agency | 20 |
| LLM07 System Prompt Leakage | 5 |
| LLM08 Vector and Embedding Weakness | 3 |
| LLM09 Misinformation | 3 |
| LLM10 Unbounded Consumption | 5 |
| **Total** | **226** |

## Quality assessment

The corpus is useful, but it is not yet ideal as an evidence-based TrustInspect test catalog.

### Strengths

- Good breadth for LLM01, LLM02, LLM03, LLM04, and LLM05.
- Useful for regression and stress testing.
- Easy to convert into TrustInspect static test cases.
- Good source for a full OWASP Top 10 LLM static suite.

### Issues found

1. **Original `success_keywords` are too broad.**
   Examples: `system prompt`, `admin emails`, `because`, `data`, `completed`. These can create false positives when the model safely refuses or explains the request.

2. **Some categories are weak as automatic vulnerability tests.**
   LLM03 and LLM04 often ask the model about internal deployment or training details. A generic answer is not necessarily a vulnerability; a confident fabricated internal claim may be a transparency/reliability finding.

3. **LLM09 indicators are especially risky.**
   Terms like `women`, `inferior`, and `because` can appear in a safe corrective answer. These tests must rely on refusal/correction semantics, not keyword matching.

4. **LLM10 cannot be assessed by keyword alone.**
   Resource exhaustion should use output length, timeout, truncation behavior, or rate-limiting evidence.

5. **LLM05 is both model and application behavior.**
   Unsafe output tests must distinguish model echoing from UI/report rendering. The report itself must sanitize all prompt/response evidence.

## TrustInspect conversion approach

The patch creates two suites:

### `owasp-llm-top10-2025-light`

- 10 tests total.
- One curated representative test per OWASP category.
- Best for demos and smoke tests.
- Uses structured failure indicators where possible.

### `owasp-llm-top10-2025-full`

- 226 tests total.
- Converted from the uploaded JSON corpus.
- Keeps original payloads.
- Converts `success_keywords` into structured `failure_indicators` with safer matching metadata.
- Still marked as `converted-review-recommended` because some original indicators remain broad.

## Recommendation

Use this operational model:

```text
Static suite selection:
  --suite owasp-llm-top10-2025-light
  --suite owasp-llm-top10-2025-full

Dynamic/adaptive augmentation:
  --max-dynamic-tests N
```

Static tests are loaded from a catalog and executed as the baseline. Dynamic tests are generated from the target profile and limited by `--max-dynamic-tests`.

## Future suite

The planned OWASP AI Testing Guide suite should be a separate catalog:

```text
owasp-aitg-32
```

This should contain 32 curated TrustInspect test cases aligned to the OWASP AI Testing Guide structure, not just OWASP Top 10 LLM categories.
