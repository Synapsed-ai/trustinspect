# TrustInspect Clean Architecture

TrustInspect is organized around evidence-based Trustworthy AI testing, not around a single scanner.

```text
TestCase Catalog / Generator
        ↓
Scanner Adapter
        ↓
Evidence Collection
        ↓
Observation
        ↓
Analyzer
        ↓
Finding Engine
        ↓
Assessment Report
```

## Component boundaries

- `core/`: stable data models such as Target, TestCase, EvidenceItem, Observation, Finding, Assessment.
- `targets/`: target capability profiling. This is benign target profiling, not system-prompt extraction.
- `testcases/`: static test catalogs, loaders, and deterministic contextual generation.
- `scanners/`: execution engines for Web UI, API, RAG, and agentic workflows.
- `analyzers/`: evidence interpretation. An analyzer must read the test metadata, not only the raw response.
- `evidence/`: evidence persistence, screenshots, DOM snapshots, HTTP traces, and replay assets.
- `findings/`: observation-to-finding transformation.
- `reporting/`: HTML/JSON reports for engineering and assurance.
- `ui/`: terminal experience for demos and interactive runs.

## Static vs adaptive testing

TrustInspect supports two complementary modes:

1. **Static Test Mode**: fixed, reproducible catalogs for regression, comparison, demo reliability, and before/after mitigation.
2. **Adaptive Test Mode**: target profiling followed by contextual test generation or contextual selection.

Adaptive testing must not become uncontrolled prompt fuzzing. The recommended initial implementation is deterministic and template based.
