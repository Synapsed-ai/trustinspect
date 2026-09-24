# Local browser regression

The `Local Browser Regression` workflow exercises real Chrome/ChromeDriver and
the public scanner against loopback-only HTTP targets. It calls no external AI
endpoint and needs no API key. Browser/driver and Python dependency provisioning
may require network access; target traffic stays local.

## Acceptance, not certification

Successful validation requires the ordinary suite, installed-distribution checks
and dedicated browser workflow to pass on the same candidate. Record run IDs,
commit identity and retained evidence in the pull request. Never infer success
from an earlier commit or from the ordinary suite skipping browser tests.

## Run the campaign

From an editable checkout with Chrome and a matching `chromedriver` on PATH:

```bash
python -m pip install -e '.[dev]'
TRUSTINSPECT_BROWSER_TESTS=1 TI_BROWSER_EVIDENCE_DIR=reports/browser-validation \
  python -m pytest -q -s tests/browser --junitxml=reports/browser-validation.xml
```

With the opt-in flag enabled, an unavailable browser or driver fails the tests.
Ordinary unit-test runs explicitly skip the browser group. Do not disable the
browser sandbox to make tests pass. Only driver executable discovery is replaced
in tests, to use the provisioned local driver; Selenium itself is not mocked.

## What is exercised

Ten deterministic browser-fixture cases cover canary disclosure, contradictory
refusals, slow streaming with a busy indicator, stale history, repeated identical
answers, operational error text, timeout, prompt echo, iframe/Enter submission,
and HTML/CSS report integrity in a second real browser.

Ten input-specific browser checks cover textarea, contenteditable and iframe
insertion; empty lines, CRLF normalization and literal Unicode/markup; absence of
premature keyboard submissions; one explicit submission; and read-only fields.

Four additional campaigns invoke the public CLI against the bundled demo HTTP
handler: static (10 checks) and adaptive (10 static + 4 generated checks), in both
vulnerable and hardened modes. These run the actual scanner, analyzer, finding
engine and report writer. They check captured responses against the deterministic
demo responses, reject ERROR outcomes, and reconcile findings with observations.
JSON, HTML, screenshots, JUnit results and environment versions are retained as
seven-day workflow artifacts. The workflow does not publish a release.

The demo is a tool-regression fixture, not a real model evaluation. The acceptance requirement is that vulnerable
static mode exposes two sentinel predicates; the raw script-like echo is marked
POSSIBLE because the application displays it as text. Hardened mode must have no
confirmed predicates, but inconclusive answers may legitimately remain POSSIBLE.
No test relies on every hardened response being SAFE.

## Limits

These tests do not establish universal selector support, semantic detection
accuracy on actual models, API/agent-trace support, or policy compliance. Streaming
quiet time remains a heuristic unless a reliable busy signal is configured.
Dependency vulnerability review, history-wide secrets and asset provenance are
separate release checks. Historical screenshots are not current test evidence.
