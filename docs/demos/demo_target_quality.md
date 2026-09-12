# TrustInspect Demo Target Quality Patch

This patch makes the local demo target deterministic demos.

Expected vulnerable-mode behavior:

- Static OWASP LLM Top 10 Light: exactly 3 immediate findings:
  - LLM01 instruction hierarchy override
  - LLM05 unsafe output echo
  - LLM08 hidden instruction following
- Dynamic tests: additional contextual findings, including:
  - travel sensitive-data disclosure
  - travel internal policy disclosure
  - unauthorized travel action completion
  - domain/role boundary override
  - dynamic resource exhaustion

It also adds analyzer guardrails for safe refusals and stale sentinel / cross-test contamination.
