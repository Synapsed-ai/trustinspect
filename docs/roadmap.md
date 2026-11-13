# Roadmap

## Milestone 1 — SynInspect EDU hardening

- Add JSON output.
- Add screenshot evidence.
- Add auto-selector discovery.
- Stabilize target metadata in HTML reports.
- Make errors explicit and separate from model behavior.

## Milestone 2 — TrustInspect Core

- Evidence model.
- Finding model.
- Assessment model.
- Import SynInspect EDU results.

## Milestone 3 — Trustworthiness mapping

- OWASP AI Testing Guide mappings.
- OWASP AIMA mappings.
- NIST AI RMF mappings.
- ISO/IEC 42001 assurance mappings.
- EU AI Act risk/evidence mapping.

## Milestone 4 — Reproducible local demonstrations and adapters

- PromptAirlines public AI challenge.
- TrustInspect Demo Chatbot.
- TrustInspect Demo RAG.
- Damn Vulnerable LLM Agent adapter.
- AgentDojo adapter.

## Release validation gates

- Complete installation and regression testing from a clean checkout.
- Install and exercise the built wheel outside the repository.
- Validate end-to-end capture against local vulnerable and hardened targets.
- Review current dependency advisories, asset provenance, and repository history.
- Document evidence limitations; a heuristic SAFE result is not a system-wide assurance claim.
