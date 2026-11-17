# TrustInspect

**Evidence-Based Trustworthy AI Testing for LLM and Agentic Applications**  
by Synapsed AI Lab • Open Source License: Apache-2.0

TrustInspect is an open-source testing workbench for evaluating the behavior of LLM, RAG, chatbot, and agentic applications through reproducible tests, target profiling, evidence capture, and structured reporting.

It is designed for AI application assurance, not traditional web application security scanning.

---

## Demo Videos

The following videos demonstrate TrustInspect in action against PromptAirlines, a controlled vulnerable AI application used to showcase OWASP AI Testing Guide aligned testing workflows.

| Video | Description |
|---|---|
| [Minimal AITG Scan](https://synapsed.ai/wp-content/uploads/2026/06/TrustInspect1.mov) | Runs a minimal OWASP AITG-aligned scan against PromptAirlines and shows one detected issue. |
| [Full AITG Scan with Dynamic Testing](https://synapsed.ai/wp-content/uploads/2026/06/TrustInspect2.mov) | Runs a broader AITG scan with dynamic testing enabled, including two dynamic test executions and several detected vulnerabilities. |
| [Additional TrustInspect Demo](https://synapsed.ai/wp-content/uploads/2026/06/TrustInspect3.mov) | Provides an additional demonstration of TrustInspect capabilities for evidence-based Trustworthy AI testing. |

---

## What TrustInspect does

TrustInspect helps testers and assurance teams:

- run static Trustworthy AI test suites against LLM and agentic web UIs;
- profile a target application to understand its declared role, capabilities, boundaries, likely sensitive assets, and risk areas;
- generate dynamic contextual tests from the target capability profile;
- collect prompt, response, screenshot, timing, and rationale evidence (including local DOM snapshots on execution errors for diagnosis);
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

<!-- TRUSTINSPECT_POSITIONING_START -->
## Positioning

TrustInspect is designed as an evidence-based Trustworthy AI testing workbench for LLM and agentic applications. Its focus is application behavior, evidence collection, target profiling, static and dynamic test execution, and reporting for AI assurance.

![TrustInspect positioning matrix](assets/screenshots/01-comparison-matrix.jpeg)
<!-- TRUSTINSPECT_POSITIONING_END -->

<!-- TRUSTINSPECT_SCREENSHOTS_START -->
## Screenshots

### Interactive launcher

TrustInspect can be started in interactive mode to guide the tester through target selection, suite selection, and static/dynamic execution choices.

![TrustInspect interactive launcher](assets/screenshots/01-launcher.png)

### Live CLI execution

During execution, TrustInspect displays the current test, prompt, response, progress counters, and classification in a terminal-first interface suitable for demos and hands-on testing.

![TrustInspect CLI live run](assets/screenshots/02-cli-live-run.png)

### Target capability profiling

In adaptive mode, TrustInspect first profiles the target, builds a Target Capability Profile, and uses it to generate contextual dynamic tests.

![TrustInspect target capability profile](assets/screenshots/03-target-capability-profile.png)

### Controlled vulnerable demo target

TrustInspect includes a local vulnerable/hardened demo chatbot so findings can be reproduced without depending on unstable third-party targets.

![TrustInspect demo chatbot vulnerable mode](assets/screenshots/04-demo-chatbot-vulnerable.png)

### HTML assessment report

TrustInspect generates a structured HTML report with assessment metadata, executive summary, target profile, generated test plan, observations, evidence, and prompt/response details.

![TrustInspect HTML report overview](assets/screenshots/05-html-report-overview.png)

### Evidence details

Observations are sorted by criticality and include expandable prompt/response evidence for each test.

![TrustInspect report observations](assets/screenshots/06-html-report-observations.png)
<!-- TRUSTINSPECT_SCREENSHOTS_END -->

## Installation

**First time, with no Python or Git installed? Start with the [from-zero installation guide](docs/installation.md).** It covers macOS, Windows and Ubuntu/Debian, including Python, Google Chrome, downloading the project and opening your first report.

You need **Python 3.10+**, **Google Chrome** and an internet connection for the initial package/driver downloads. Use the **Python version actually installed** (not a hard-coded `3.13`). In November 2026 the current stable release is Python 3.15.2; the guide distinguishes the official installer version from the combinations verified by CI. Git, Homebrew, Docker, an AI API key and a paid model account are **not required** for the local demo. See the guide for the distinction between declared support and the CI-tested platform/Python combinations.

Download the project from **Code → Download ZIP**, extract it, and move the folder **containing `pyproject.toml`** into your home folder, named `trustinspect`. Do not overwrite an existing checkout. Git users can clone instead; both routes are explained in the guide.

After installing the prerequisites, run the block for your operating system **one command at a time**. Stop if a command fails.

**macOS — Terminal**

First check `python3 --version` and `command -v python3`. If `python3` still invokes an older Apple/Xcode installation, use the official Python.org interpreter as described in the full guide (for example, `python3.15`).

```bash
cd "$HOME/trustinspect"
python3 --version
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install .
./.venv/bin/trustinspect --help
```

**Windows — PowerShell**

Check `py --version` to identify the Python runtime installed by Python Install Manager.

```powershell
Set-Location "$HOME\trustinspect"
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\trustinspect.exe --help
```

**Ubuntu/Debian — Terminal**

```bash
cd "$HOME/trustinspect"
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install .
./.venv/bin/trustinspect --help
```

These commands deliberately use the executables inside `.venv`: you do not need to activate the environment, change PowerShell execution policy or install packages into system Python. Selenium and `webdriver-manager` are installed with TrustInspect; Chrome must also be installed. The scanner uses `webdriver-manager` to obtain ChromeDriver on first use. Do not disable TLS verification or the browser sandbox to bypass setup errors.

---

## Quick start: local vulnerable demo

The local demo is deterministic: it does **not** call a real LLM or require an API key. Complete installation first, then open **two terminal windows**. Both must start in the `trustinspect` folder.

**Terminal 1 — start the target and leave this terminal running.**

macOS/Linux:

```bash
cd "$HOME/trustinspect"
./.venv/bin/python demos/trustinspect-demo-chatbot/app/main.py --mode vulnerable --host 127.0.0.1 --port 8080
```

Windows PowerShell:

```powershell
Set-Location "$HOME\trustinspect"
.\.venv\Scripts\python.exe demos/trustinspect-demo-chatbot/app/main.py --mode vulnerable --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/` in Chrome. You should see the demo chatbot in **VULNERABLE** mode. Keep the server bound to `127.0.0.1`; it is a deliberately vulnerable local test target, not a public service.

**Terminal 2 — run a first static scan.** Each scan below is a single command, even if your browser wraps it across lines.

macOS/Linux:

```bash
cd "$HOME/trustinspect"
./.venv/bin/trustinspect scan-web --suite owasp-llm-top10-2025-light --target-url "http://127.0.0.1:8080/" --input-selector "#chatInput" --output-selector "#chat-content .bot-message p" --send-selector "#sendButton" --output reports/demo_local_vulnerable.html --headless --open
```

Windows PowerShell:

```powershell
Set-Location "$HOME\trustinspect"
.\.venv\Scripts\trustinspect.exe scan-web --suite owasp-llm-top10-2025-light --target-url "http://127.0.0.1:8080/" --input-selector "#chatInput" --output-selector "#chat-content .bot-message p" --send-selector "#sendButton" --output reports/demo_local_vulnerable.html --headless --open
```

The report is saved as `reports/demo_local_vulnerable.html`. `--open` requests opening it in your default browser; double-click the file if it does not open automatically. `--headless` hides the automated Chrome window, not the report. A sample report or successful installation alone does not verify browser scanning: inspect the scan's observations and any `ERROR` results.

For the **hardened comparison**, stop Terminal 1 with **Ctrl+C**, restart the same command with `--mode hardened`, then repeat the scan with `--output reports/demo_local_hardened.html` so the first report is not overwritten. The [complete guide](docs/installation.md#compare-hardened-mode) includes the full commands, an optional adaptive scan and troubleshooting.

---

## Interactive mode

From the project folder, use the executable in the environment created above.

macOS/Linux:

```bash
./.venv/bin/trustinspect
```

Windows PowerShell:

```powershell
.\.venv\Scripts\trustinspect.exe
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

## Validation

For reproducible checks of the current code, see the [local-browser regression guide](docs/testing/local-browser.md). Demonstration media may show earlier builds; findings should be evaluated using evidence from the version under test.

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
