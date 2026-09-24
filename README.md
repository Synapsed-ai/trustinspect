# TrustInspect

**Evidence-Based Trustworthy AI Testing for LLM and Agentic Applications**  
by Synapsed AI Lab • Open Source License: Apache-2.0

TrustInspect is an open-source testing workbench for evaluating the behavior of LLM, RAG, chatbot, and agentic applications through reproducible tests, target profiling, evidence capture, and structured reporting.

It is designed for AI application assurance, not traditional web application security scanning.

---

## Reproducible demonstrations

Use the [controlled local demo](demos/trustinspect-demo-chatbot/README.md) and
[real-browser regression checks](docs/testing/local-browser.md) to reproduce
current behavior. Historical videos and screenshots are not used as validation
of the current analyzer. No external AI account is required for these checks.

## What TrustInspect does

TrustInspect helps testers and assurance teams:

- run static Trustworthy AI test suites against LLM and agentic web UIs;
- profile a target application to understand its declared role, capabilities, boundaries, likely sensitive assets, and risk areas;
- generate dynamic contextual tests from the target capability profile;
- collect prompt, response, screenshot, timing, and rationale evidence (DOM snapshots only when explicitly enabled);
- produce self-contained HTML reports with findings, observations, target profile, generated test plan summary, and evidence details;
- compare vulnerable and hardened target behavior using the local demo chatbot.

---

## What TrustInspect is not

TrustInspect is **not**:

- a traditional web vulnerability scanner or static code analyzer;
- a generic jailbreak toy;
- a model benchmark only;
- a guarantee of complete coverage or zero false positives.

TrustInspect focuses on **evidence-based Trustworthy AI testing** for LLM and agentic application behavior.

---

## Current status

This repository is currently an **early v0.3-alpha** development version.

Supported capabilities include:

- Web UI scanner using Selenium;
- interactive launcher;
- target registry and target calibration workflow;
- static test suites;
- target capability profiling;
- dynamic tests per static test;
- evidence-based HTML reports;
- output capture guard to reduce false positives caused by incorrect selectors;
- local vulnerable/hardened demo chatbot.

Known limitations:

- public AI challenge targets may change their UI and require selector recalibration;
- full suites can be slow;
- dynamic generation is deterministic/template-based;
- RAG/vector-store adapters, agent trace adapters, and API adapters are roadmap items;
- web UI testing depends on DOM selectors and browser behavior.

---

## Scope and evidence

TrustInspect exercises application behavior through a web UI and records the
observed response. Native API, RAG-trace and agent-trace adapters remain roadmap
items. A textual claim of access or completion is not proof of a real action, and
raw markup in a response is not proof that a browser executed it. Review-only
signals are reported as `POSSIBLE VULNERABILITY`; a failure predicate is not a
certificate of exploitability or comprehensive coverage.

Generate [current sample reports](examples/sample-reports/README.md), or use the
[real-browser regression workflow](docs/testing/local-browser.md) to inspect
prompt/response evidence from controlled vulnerable and hardened local targets.

## Installation

Run the following from a checkout of this repository. See the
[installation guide](docs/installation.md) for wheel and platform details.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Selenium and the driver-manager dependency are installed with the project.
Web UI scans also require a compatible local browser and driver.
Do not disable the browser sandbox to work around setup problems.

---

## Quick start: local vulnerable demo

Start the local vulnerable target:

```bash
cd demos/trustinspect-demo-chatbot
./run_vulnerable.sh
```

In a second terminal:

```bash
cd /path/to/trustinspect
source .venv/bin/activate

trustinspect adaptive-scan \
  --suite owasp-llm-top10-2025-light \
  --dynamic-tests-per-static 1 \
  --target-url "http://127.0.0.1:8080/" \
  --input-selector "#chatInput" \
  --output-selector "#chat-content .bot-message p" \
  --send-selector "#sendButton" \
  --output reports/demo_local_vulnerable.html \
  --headless \
  --open
```

Then compare with hardened mode:

```bash
cd demos/trustinspect-demo-chatbot
./run_hardened.sh
```

Run the same TrustInspect command again and compare the reports.

---

## Interactive mode

```bash
trustinspect
```

The interactive launcher lets you:

- select a known target;
- calibrate a new target;
- select a static test suite;
- choose dynamic tests per static test;
- preview the command before execution;
- open the HTML report.

---

## Test suites

TrustInspect currently supports:

- `trustinspect-baseline`
- `owasp-llm-top10-2025-light`
- `owasp-llm-top10-2025-full`
- `owasp-aitg-light`
- `owasp-aitg-full`

The OWASP-related suites are mapped for TrustInspect-style evidence-based testing. OWASP trademarks and project names belong to the OWASP Foundation.

---

## Dynamic testing

Dynamic tests are contextual variants generated from:

- the selected static test suite;
- the target capability profile;
- deterministic dynamic templates.

Example:

```bash
--dynamic-tests-per-static 1
```

means:

```text
for each static test, generate one contextual dynamic variant
```

For large suites, add a cap:

```bash
--max-dynamic-tests 50
```

---

## Report model

TrustInspect reports include:

- assessment metadata;
- engine versions;
- executive summary;
- target capability profile;
- generated test plan summary;
- suite/AITG coverage when applicable;
- observations ordered by severity;
- prompt/response/evidence details;
- generated test plan artifact references.

Reports treat all target output as untrusted data and are rendered with a restrictive Content Security Policy.

---

## Responsible use

Use TrustInspect only on systems you own, operate, or are authorized to test.

Public AI challenge targets included in the registry are provided for research and demonstration convenience. They may change, rate-limit, or require selector recalibration.

---

## Roadmap

- API scanner support;
- RAG/vector-store adapters;
- agent trace adapters;
- Docker image;
- improved selector calibration;
- expanded AITG full scenarios;
- richer JSON/SARIF-style outputs;
- CI-friendly regression mode.

## Evidence handling and privacy

TrustInspect reports and evidence files may contain sensitive information collected during an assessment, including prompts, model responses, screenshots, DOM snapshots, target URLs, generated test cases, and target capability profiles.

Review generated reports and evidence artifacts before sharing them outside the assessment team. TrustInspect does not upload reports or evidence by default; generated artifacts are stored locally in the output path selected by the tester.

Use TrustInspect only against systems you own, operate, or are explicitly authorized to test. Public AI challenge targets may change over time and may require selector calibration.
