# Test a local model with LM Studio

TrustInspect can send static tests and contextual dynamic variants directly to a model served by LM Studio. The `scan-api` command uses its OpenAI-compatible Chat Completions API and saves the usual HTML and JSON assessment reports. This workflow does not launch Chrome or require CSS selectors.

## 1. Start LM Studio's server

1. Load your model in LM Studio.
2. Open **Model Server / Local Server** and switch **Stopped** to **Running**.
3. Check **Server Settings → Server Port**. The examples use the default port `1234`.
4. Copy the model's **API Identifier**. For example, a loaded Qwen3 32B model may show `qwen3-32b`; use the identifier displayed by your installation.

Run TrustInspect on the same computer as LM Studio for these commands. Keep LM Studio running during the assessment.

| Value | Example |
| --- | --- |
| API base URL to pass to TrustInspect | `http://127.0.0.1:1234/v1` |
| Endpoint used by the connector | `http://127.0.0.1:1234/v1/chat/completions` |
| Model identifier | `qwen3-32b` |

Check connectivity from Terminal:

```bash
curl http://127.0.0.1:1234/v1/models
```

Expect a JSON model list. If you changed the server port, replace `1234` in every example. The base URL is an API address; opening it does not display a chat page.

## 2. Use an updated TrustInspect installation

The following commands are for **macOS/Linux**, from the project folder containing `pyproject.toml` and your `.venv` environment.

```bash
./.venv/bin/trustinspect scan-api --help
```

If `scan-api` is missing, update the source first and then reinstall it:

```bash
./.venv/bin/python -m pip install .
./.venv/bin/trustinspect scan-api --help
```

Reinstalling an old source folder does not download the new connector. If you originally used **Download ZIP**, download the updated project ZIP and extract it into a separate folder. Open Terminal, type `cd ` with a trailing space, drag that extracted folder from Finder into Terminal, then press Return. Create its environment using your installed Python and install the updated source:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install .
./.venv/bin/trustinspect scan-api --help
```

Keep your old folder if it contains reports, profiles, or local targets. A ZIP download is not a Git checkout, so `git pull` does not update it. See the [installation guide](installation.md) for first-time prerequisites.

On **Windows PowerShell**, use `.\.venv\Scripts\trustinspect.exe` in place of `./.venv/bin/trustinspect`. Multi-line commands below use Bash line continuations; enter them as one line in PowerShell.

## 3. Run a short first assessment

Replace `qwen3-32b` if LM Studio shows a different API Identifier. Paste this whole block as a single command:

```bash
./.venv/bin/trustinspect scan-api \
  --base-url http://127.0.0.1:1234/v1 \
  --model qwen3-32b \
  --suite owasp-llm-top10-2025-light \
  --max-tests 2 \
  --output reports/lmstudio_smoke.html \
  --open
```

This sends the first two static tests from the selected suite. It checks the complete path from HTTP requests to assessment reports. Open `reports/lmstudio_smoke.html` and review the observations, including any `ERROR` results. The accompanying evidence is saved as `reports/lmstudio_smoke.json`.

For all static tests in the light suite, omit `--max-tests`:

```bash
./.venv/bin/trustinspect scan-api \
  --base-url http://127.0.0.1:1234/v1 \
  --model qwen3-32b \
  --suite owasp-llm-top10-2025-light \
  --output reports/lmstudio_static.html \
  --open
```

Each test starts a fresh conversation. The connector does not share previous test messages with subsequent tests, execute model-requested tools, or attach files or retrieved context.

## 4. Add dynamic tests

Add `--dynamic-tests-per-static 1` to generate one contextual variant for each static test:

```bash
./.venv/bin/trustinspect scan-api \
  --base-url http://127.0.0.1:1234/v1 \
  --model qwen3-32b \
  --suite owasp-llm-top10-2025-light \
  --dynamic-tests-per-static 1 \
  --output reports/lmstudio_adaptive.html \
  --open
```

TrustInspect first sends a benign capability question to the same API, builds a Target Capability Profile, and uses the existing deterministic templates to generate variants. The profile records the model's stated capabilities; these statements are not proof that tools, private data, or other systems are accessible.

Use `--target-profile path/to/profile.yaml` to supply an existing profile instead of asking the model. Add `--max-dynamic-tests 5` to cap generated variants while keeping the selected static tests. `--max-tests` limits the static tests before dynamic variants are generated.

For the dynamic example above, the generated profile and test catalog are saved as `reports/lmstudio_adaptive_profile.yaml` and `reports/lmstudio_adaptive_dynamic_tests.yaml`. These are separate from the assessment reports. Static-only runs do not create profile or generated-test files.

## Interactive launcher

```bash
./.venv/bin/trustinspect
```

Choose **6 — Test a local model via LM Studio**. Enter the API base URL and the model identifier, choose a suite and static/dynamic mode, then review the command before selecting **Run now**.

The defaults are static tests, a 180-second timeout for network operations, a temperature of `0.6`, and a maximum of 2,048 output tokens per request. The launcher uses the same Python environment as its child command, so activation with `source .venv/bin/activate` is optional.

## Request limits and authentication

- `--request-timeout 300` sets a 300-second timeout for blocking network operations, which can help with a slower local model. It is not a hard limit on total request or scan duration.
- `--max-tokens 4096` increases the maximum generated tokens. Reasoning models may use part of this budget for reasoning before producing their final answer.
- `--temperature 0.6` is the default and a starting point consistent with the [Qwen3-32B model card's thinking-mode recommendation](https://huggingface.co/Qwen/Qwen3-32B#best-practices). Qwen recommends avoiding greedy decoding in that mode. Override the temperature to suit your model and evaluation plan; no setting guarantees identical outputs across runs or runtimes.
- `--system-prompt-file path/to/system-prompt.txt` includes that file's contents as the system message in each request.
- `--api-key-env LM_STUDIO_API_KEY` reads an authentication token from that environment variable if you enabled **Require Authentication** in LM Studio. Set the variable before running the command; pass the variable name, not the token value. With LM Studio's default local settings, no token is required.

Connection failures, HTTP errors, malformed responses, missing final answers, and token-truncated answers are execution errors. They must not be interpreted as a successful security test. A partial answer may be retained as evidence, but it is not treated as a complete answer for classification.

If a scan records execution errors, TrustInspect still saves the reports and exits with status `1`. Findings alone do not change the exit status. Configuration errors and failed capability profiling stop before test execution; correct those errors before retrying.

## What the results cover

This connector tests the model's observed textual behavior for the supplied prompts and system message. A model-only API assessment does not establish the security of a RAG pipeline, tool execution, authorization controls, or an entire application. Review the suite's applicability and the captured evidence before drawing those conclusions.

Reports contain prompts and model answers. Review these artifacts before sharing them. Authentication headers are not included in report traces.

## LM Studio references

- [Start the local API server](https://lmstudio.ai/docs/developer/core/server)
- [OpenAI-compatible endpoints and base URL](https://lmstudio.ai/docs/developer/openai-compat)
- [Server settings](https://lmstudio.ai/docs/developer/core/server/settings)
- [API authentication](https://lmstudio.ai/docs/developer/core/authentication)
