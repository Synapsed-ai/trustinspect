# Install TrustInspect from zero

This guide starts with a computer that has **no Python, no Git and no TrustInspect environment**. Follow your operating system's steps, then download the project, install it and run the local demo. You do not need to build a release, install a language model or create an AI-provider account.

TrustInspect currently declares an alpha version (`0.3.0a0`). Its source declares Python 3.10 or later. This guide selects **standard CPython 3.13** for new macOS/Windows installations; the package's current CI matrix checks Linux on Python 3.10/3.11/3.13 and Windows/macOS on Python 3.11. A documented setup path is not a claim that a fresh desktop installation or every other OS/Python combination has been tested.

## Before you start

Use a desktop or laptop and your normal user account. Installing Python or Chrome may require administrator approval; running TrustInspect does not require an administrator terminal. Internet access is needed to download the source, Python packages and ChromeDriver. The bundled demo itself runs locally and does not use a paid API.

The required components have different jobs:

| Component | What it does | How it is installed |
| --- | --- | --- |
| Python | Runs TrustInspect | Install it in the OS-specific step below |
| pip and venv | Install packages into a private project environment | Supplied with the standard Python installer; install the distribution packages on Linux |
| Google Chrome | Runs the automated browser session | Install Chrome separately |
| Selenium and webdriver-manager | Automate Chrome and obtain its matching driver | Installed automatically with TrustInspect |
| TrustInspect source folder | Contains the project and the local demo | Download ZIP; Git is optional |

Safari, Edge or Firefox can be used to download the files, but they are **not substitutes for Google Chrome in the current scanner**. You do not need Homebrew, Docker, Node.js or an IDE for this procedure. The simple Linux path below assumes an x86-64 desktop; other architectures, WSL and containers need separate browser/driver setup and are not covered by this walkthrough.

Commands go in **Terminal** on macOS/Linux or **PowerShell** on Windows, not in Python's `>>>` prompt. When you see `>>>`, type `exit()` and press Enter. Run one command at a time and stop at the first error. Do not copy Markdown backticks or a shell prompt such as `$`.

## 1. Install Python and Chrome

### macOS

1. Check **Apple menu → About This Mac**. Current Chrome requires **macOS 13 Ventura or later**; consult [Google's current requirements](https://support.google.com/chrome/answer/95346?hl=en) before proceeding on an older Mac. Python installing successfully does not establish Chrome compatibility.
2. Open [Python's official macOS downloads](https://www.python.org/downloads/macos/), choose a stable **Python 3.13.x** release with a **macOS installer**, download the `.pkg` and complete the installer. Choose the standard build, not an experimental free-threaded build or a source archive. No Homebrew or Xcode installation is required for this path.
3. In Finder, open **Applications → Python 3.13** and double-click **Install Certificates.command** to finish the certificate setup. This is the certificate helper supplied by the official Python installer, not a script from this repository.
4. Install [Google Chrome](https://www.google.com/chrome/), drag it to **Applications**, open it once and complete the first-run prompts. A Google sign-in is not required for the local demo.
5. Open **Terminal** with Spotlight: press **Command+Space**, type `Terminal`, then press Enter. If Terminal was already open before the Python installation, close and reopen it.

Check Python:

```bash
python3.13 --version
```

Expected: `Python 3.13.x`, where `x` is the patch version you installed. If the command is not found, finish the installer and reopen Terminal. Do not replace or delete Apple's `/usr/bin/python3`.

### Windows — PowerShell

1. Use a supported Windows installation; this walkthrough targets **Windows 11 x64**. Check **Settings → System → About** when unsure. Consult the official Python and Chrome requirements for other Windows versions or ARM systems.
2. Download **Python Install Manager** from [python.org/downloads/windows](https://www.python.org/downloads/windows/) and install it, or install the Python Software Foundation's Python Install Manager from the Microsoft Store. Do not download the embeddable ZIP or Python source code.
3. Open **Start → PowerShell** as your normal user. Close and reopen PowerShell after installing the manager. Install the selected Python runtime:

```powershell
pymanager install 3.13
py -3.13 --version
```

Expected: `Python 3.13.x`. `pymanager` avoids ambiguity with the older `py` launcher. If it is not found, the install manager is not yet available in that terminal; reopen PowerShell and consult the [official Windows installation/troubleshooting guide](https://docs.python.org/3/using/windows.html). An existing installation for which `py -3.13 --version` already works does not need to be reinstalled.

4. Install [Google Chrome](https://www.google.com/chrome/), open it once and complete the first-run prompts. Use the standard installer location. You do not need a Google account.

The commands below invoke `.venv\Scripts\python.exe` directly. They do **not** require running `Activate.ps1`, changing execution policy, Git Bash or WSL.

### Ubuntu/Debian Linux — Terminal

This path uses the distribution's Python, not a replacement for system Python. Open Terminal (commonly **Ctrl+Alt+T**) and run:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 --version
```

Expected: Python **3.10 or later**. The actual version depends on your distribution. An older distribution whose packages only provide Python below 3.10 needs a supported OS/interpreter setup first; do not remove or overwrite system Python.

Download the appropriate official **Google Chrome `.deb`** from [Google](https://www.google.com/chrome/), install it using the system package installer and open Chrome once. This is a browser installation, not a Python package. For an x86-64 system where the downloaded file is in the standard Downloads directory, the terminal alternative is:

```bash
sudo apt install "$HOME/Downloads/google-chrome-stable_current_amd64.deb"
google-chrome --version
```

Use the actual file path if the browser saved the package elsewhere. Never run TrustInspect or Chrome as root to fix a permission problem, and do not add `--no-sandbox`.

## 2. Download the complete project — no Git required

In your web browser, open the [TrustInspect repository](https://github.com/Synapsed-ai/trustinspect), select the **main** branch, then **Code → Download ZIP**. Downloading the public source does not require a GitHub account.

Extract the archive completely: double-click it on macOS; use **Extract All** in Windows File Explorer; use your archive manager on Linux. Do not run commands inside the ZIP preview.

Find the extracted folder that contains **`pyproject.toml`, `README.md`, `trustinspect/` and `demos/`**. Move that folder to your home directory and name it **`trustinspect`**. The commands in this guide assume:

| OS | Project folder |
| --- | --- |
| macOS | `/Users/your-user/trustinspect` — Finder **Go → Home** opens the parent folder |
| Windows | `C:\Users\your-user\trustinspect` — enter `%USERPROFILE%` in File Explorer's address bar to open the parent folder |
| Linux | `/home/your-user/trustinspect` — your file manager's **Home** folder |

`your-user` is explanatory; do not type it literally. The commands use `$HOME` to obtain your real home path. Keep your existing checkout if one is already there: use a different folder name and adjust the `cd`/`Set-Location` commands instead of overwriting work.

### Optional: download with Git instead

Git is only needed for cloning, updating a checkout or contributing. Install it from the [official Git installation guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) when choosing this route. Verify `git --version`, then run the following from your home directory if `trustinspect` does not already exist:

```text
git clone https://github.com/Synapsed-ai/trustinspect.git
```

The ZIP and Git routes provide the source folder for the same installation procedure. A ZIP is a snapshot and cannot be updated with `git pull`.

## 3. Create the environment and install TrustInspect

A virtual environment is a `.venv` folder containing the Python environment used only by this project. Installing here avoids changing your system's packages. The dot at the end of `pip install .` means **the project in your current directory**; it is essential.

### macOS commands

```bash
cd "$HOME/trustinspect"
ls pyproject.toml
python3.13 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install .
./.venv/bin/python -m pip check
./.venv/bin/trustinspect --help
```

### Windows PowerShell commands

```powershell
Set-Location "$HOME\trustinspect"
Get-Item .\pyproject.toml
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\trustinspect.exe --help
```

### Ubuntu/Debian commands

```bash
cd "$HOME/trustinspect"
ls pyproject.toml
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install .
./.venv/bin/python -m pip check
./.venv/bin/trustinspect --help
```

**Checkpoints:** the file check must find `pyproject.toml`; pip must complete without an error; `pip check` should print `No broken requirements found`; the final command must display TrustInspect help, including `scan-web` and `adaptive-scan`. Dependency downloads and build messages are normal. Stop and fix an error rather than continuing to the next block.

No standalone `pip install selenium`, manual ChromeDriver download or `pip install trustinspect` from a package-name search is needed. We install this repository explicitly. Do not use `sudo pip` or `--break-system-packages`.

The environment is tied to its location. Do not move the project after creating `.venv`; recreating an environment in its new location is safer than copying it between folders or computers.

## 4. Check report generation before browser scanning

From the project folder, create a sample report. This verifies the CLI and report templates **without starting Chrome or contacting a target**.

macOS/Linux:

```bash
./.venv/bin/python -c "from importlib.metadata import version; print(version('trustinspect'))"
./.venv/bin/trustinspect demo-report --output reports/install-check.html
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -c "from importlib.metadata import version; print(version('trustinspect'))"
.\.venv\Scripts\trustinspect.exe demo-report --output reports/install-check.html
```

The current package reports `0.3.0a0`. Open the project's `reports` folder and double-click `install-check.html`. **This report contains synthetic example data; it is not a completed scan and does not prove the browser setup works.**

## 5. Run your first real scan against the local demo

Use **two terminal windows**. The target server stays running in the first; the scanner runs in the second. Both command blocks explicitly enter the project folder, so neither depends on activation in another terminal.

### Terminal 1: start the local vulnerable target

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

The terminal prints the mode and `http://127.0.0.1:8080/`, then remains occupied serving requests. This is expected: **leave it open**. Open that address in Chrome and confirm the **VULNERABLE** label and chat input. You can also open `http://127.0.0.1:8080/health` for a small JSON health response.

`127.0.0.1` means this computer. Do not expose this deliberately vulnerable target on the public internet. It uses synthetic data and deterministic responses, not an installed model or paid API.

### Terminal 2: scan the target

Each long command below is **one line**; visual wrapping is not a line break. Explicit selectors match the bundled demo. Do not reuse them unmodified on unrelated websites.

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

**What happens:** TrustInspect uses `webdriver-manager` to obtain a compatible ChromeDriver, launches a separate automated Chrome session, sends the light suite's ten prompts and writes a report. The first driver download needs internet access, even though the target is local. You do not need to sign in to a personal Chrome profile. `--headless` hides the automated browser window; omit just that flag to see the interaction. `--open` requests opening the final report in your default browser.

Open `reports/demo_local_vulnerable.html` manually if the report does not open. Check that ten observations were recorded, inspect their prompt/response evidence and investigate any `ERROR` classifications. For the existing deterministic static-light fixture, two sentinel violations are expected to be confirmed; other observations can require review. These fixture expectations are not a promise of a fixed finding count on real applications. A command finishing or a report existing alone is not evidence that every test executed successfully.

## Compare hardened mode

In **Terminal 1**, press **Ctrl+C** to stop the vulnerable server. Do not start a second server on the same port without stopping the first. Restart it as follows.

macOS/Linux:

```bash
./.venv/bin/python demos/trustinspect-demo-chatbot/app/main.py --mode hardened --host 127.0.0.1 --port 8080
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe demos/trustinspect-demo-chatbot/app/main.py --mode hardened --host 127.0.0.1 --port 8080
```

Refresh the page and confirm **HARDENED**. In **Terminal 2**, run the same static scan with a **different output filename**.

macOS/Linux:

```bash
./.venv/bin/trustinspect scan-web --suite owasp-llm-top10-2025-light --target-url "http://127.0.0.1:8080/" --input-selector "#chatInput" --output-selector "#chat-content .bot-message p" --send-selector "#sendButton" --output reports/demo_local_hardened.html --headless --open
```

Windows PowerShell:

```powershell
.\.venv\Scripts\trustinspect.exe scan-web --suite owasp-llm-top10-2025-light --target-url "http://127.0.0.1:8080/" --input-selector "#chatInput" --output-selector "#chat-content .bot-message p" --send-selector "#sendButton" --output reports/demo_local_hardened.html --headless --open
```

Compare the two report files; do not overwrite the first one. The hardened fixture should avoid the confirmed sentinel violations, but `POSSIBLE` observations still need interpretation and are not equivalent to confirmed vulnerabilities. Keep the report and its associated evidence files together when moving an assessment.

## Optional: add contextual dynamic tests

Only after the static scan works, run an adaptive scan. Keep one demo server running and note its mode. This example profiles it, runs the ten static tests and adds **at most four** deterministic variants; it does not use an LLM to generate tests.

macOS/Linux:

```bash
./.venv/bin/trustinspect adaptive-scan --suite owasp-llm-top10-2025-light --dynamic-tests-per-static 1 --max-dynamic-tests 4 --target-url "http://127.0.0.1:8080/" --input-selector "#chatInput" --output-selector "#chat-content .bot-message p" --send-selector "#sendButton" --output reports/demo_local_adaptive.html --headless --open
```

Windows PowerShell:

```powershell
.\.venv\Scripts\trustinspect.exe adaptive-scan --suite owasp-llm-top10-2025-light --dynamic-tests-per-static 1 --max-dynamic-tests 4 --target-url "http://127.0.0.1:8080/" --input-selector "#chatInput" --output-selector "#chat-content .bot-message p" --send-selector "#sendButton" --output reports/demo_local_adaptive.html --headless --open
```

Choose another report filename for subsequent comparisons. Avoid using a changing third-party website as your first installation check.

## Use TrustInspect again later

Open a new terminal and return to the same project folder. You do **not** need to reinstall packages or recreate `.venv` every time.

macOS/Linux:

```bash
cd "$HOME/trustinspect"
./.venv/bin/trustinspect
```

Windows PowerShell:

```powershell
Set-Location "$HOME\trustinspect"
.\.venv\Scripts\trustinspect.exe
```

This opens the interactive launcher. A local target still needs its server running in another terminal. The shorter command `trustinspect` only works when the environment's executable directory is on `PATH`, for example after optional activation; the full paths above avoid that dependency.

A normal `pip install .` copies the package into the environment. After deliberately updating the source, reinstall with that environment's Python (`./.venv/bin/python -m pip install .` or `.\.venv\Scripts\python.exe -m pip install .`). Do not assume editing the source changes an already installed copy; editable installation is a separate developer option below.

## Troubleshooting

| Symptom | Check or fix |
| --- | --- |
| `python3.13`, `py` or `pymanager` is not recognized | Complete the correct official Python installation and reopen the terminal. On macOS verify `python3.13 --version`; on Windows verify `py -3.13 --version`. Avoid relying on an unrelated system Python or a Microsoft Store placeholder alias. |
| Python displays `>>>` | You opened the Python interpreter, not a shell. Enter `exit()` and paste commands into Terminal/PowerShell. |
| `pyproject.toml` not found / directory is not installable | Enter the extracted folder containing `pyproject.toml`, not the outer Downloads folder, ZIP preview or inner Python package directory. |
| Linux reports `ensurepip is not available` | Install the matching distribution `python3-venv` package. For a non-default Python version, its matching venv package is needed; do not mix interpreters. |
| `externally-managed-environment` or global install permission errors | Use `.venv/bin/python -m pip` or `.venv\Scripts\python.exe -m pip`, not system pip. Do not use `sudo pip` or bypass system-package protections. |
| PowerShell blocks `Activate.ps1` | Activation is not needed. Use the explicit `.exe` paths in this guide; no execution-policy change is necessary. |
| `trustinspect` not found | Use the full `.venv` executable path. Check the installation log for an earlier error. |
| `ModuleNotFoundError` after installation | Confirm you used the same `.venv` Python for pip and the `.venv` TrustInspect executable. |
| `No matching distribution found` or package download errors | Check the Python version, internet access and the configured package index/proxy. A corporate mirror may not contain the declared minimum versions. Do not lower dependency minimums or disable TLS just to complete installation. |
| macOS certificate errors | Run the official `Install Certificates.command` for the Python version installed. For corporate TLS interception, ask IT to configure the approved CA/proxy; do not set `WDM_SSL_VERIFY=0` or use insecure downloads. |
| Chrome cannot be found / driver download or session-creation error | Install/open Google Chrome in its standard location, complete first-run prompts, check the Chrome version and allow approved driver downloads. The current scanner explicitly uses `webdriver-manager`; placing an arbitrary chromedriver on PATH is not this guide's fix. |
| The local page does not open / connection refused | Keep Terminal 1 running; confirm the printed host/port and open `/health`. Start the server before starting the scan. |
| Port 8080 is already in use | Stop your previous demo with Ctrl+C, or choose `--port 8081` and change the browser URL and scanner `--target-url` to that same port. Do not terminate an unrelated process blindly. |
| Windows cannot run `./run_vulnerable.sh` | Those optional helpers are Unix shell scripts. Use the direct Python server command in this guide. |
| The scan produces `ERROR` results | Open the diagnostic evidence, verify the target is reachable, use the bundled selectors and check Chrome/driver setup. Do not count `ERROR` as a successful or safe test. |
| The HTML report does not open automatically | Open the named `.html` in the project's `reports` folder. The auto-open option depends on the desktop/default browser. |

Report installation problems with your OS, Python version, exact command and full error output. Redact private paths, credentials and target data before posting logs publicly. For vulnerabilities in TrustInspect itself, use the contact in [SECURITY.md](../SECURITY.md).

## Reference sources for prerequisite installation

Official instructions checked when preparing this guide (17 November 2026): [Python on macOS](https://docs.python.org/3.13/using/mac.html), [Python on Windows](https://docs.python.org/3/using/windows.html), [Python virtual environments](https://docs.python.org/3/library/venv.html), [Ubuntu Python setup](https://documentation.ubuntu.com/ubuntu-for-developers/howto/python-setup/), [Chrome installation and requirements](https://support.google.com/chrome/answer/95346?hl=en), and [Git installation](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git). Vendor requirements can change; project CI coverage is listed above rather than inferred from vendor support.

---

# Advanced: development and distribution verification

The sections below are for contributors and maintainers. **They are not additional steps required to run TrustInspect.**

## Development installation

From a Git checkout with the prerequisites and virtual environment already prepared above, activate that environment first. On macOS/Linux use `source .venv/bin/activate`; on Windows Command Prompt use `.venv\Scripts\activate.bat`. Windows PowerShell users can instead prefix Python commands with `.\.venv\Scripts\python.exe` without activation. Then install the optional developer tools:

```sh
python -m pip install -e '.[dev]'
python -m pytest -q
```

Python 3.10 or later is declared. The distribution workflow exercises Linux on
Python 3.10, 3.11 and 3.13, and Windows/macOS on Python 3.11. Other configurations
are not implied to have been tested by this matrix.

## Build a distributable wheel

```sh
python -m pip install 'build>=1.2.2' 'twine>=6.0'
python -m build
python -m twine check dist/*
python scripts/maintenance/verify_installed_distribution.py
```

The default `build` command creates an sdist and builds the wheel **from that
sdist**. The verifier creates a new virtual environment (without system site
packages), installs the wheel and its declared dependencies, runs `pip check`,
and executes commands in a temporary working directory unrelated to the checkout.
Isolated Python subprocesses use explicit `-I -B -X utf8` flags: isolation
ignores `PYTHON*` environment settings. Console entry points receive UTF-8
environment settings for captured output. Legacy non-Unicode terminal behavior
is not certified by this packaging check.
Installation requires access to the public Python package index; no external AI
endpoint or paid model API is called by the verifier.

To install the built wheel manually in another environment:

```sh
python -m pip install /absolute/path/to/trustinspect-0.3.0a0-py3-none-any.whl
trustinspect --help
trustinspect demo-report --output demo.html
```

Use an environment-appropriate activation command or the full path to its Python
and `trustinspect` executables. Do not use an editable installation as evidence
that the wheel works independently of the source tree.

## Built-in data and custom inputs

The five built-in suite IDs resolve resources relative to the installed package,
not the current directory. `scan-web` without a custom catalog keeps its existing
OWASP light default, now loaded from bundled data. `--test-cases` and
`--base-test-cases` accept explicit user paths; existing custom files are honored
and missing unknown paths raise errors rather than running an empty campaign.
Known legacy relative catalog paths remain aliases when the files are absent.

The eight deterministic dynamic templates and three built-in target definitions
are included in the wheel. Built-in template-directory names use installed data;
use an explicit absolute directory for custom templates.

Resources are listed individually in `trustinspect/_resource_manifest.json`.
The build copies only those files into `trustinspect/_data/`; the original paths
in the manifest remain authoritative for this build, without adding mirrored copies
to the repository. Existing legacy duplicates are unchanged in this phase. Missing or
external/symlink-escaping resources fail the build. Source and editable installs
read those same originals relative to the module location. Direct zipimport of
an uninstalled wheel is not supported by the resource Path API.

Reports, screenshots, archived targets, local target settings and customer data
are not included by the runtime-data manifest. The local demo application and
source-only maintenance scripts remain checkout tools, not installed runtime data.

## Workspace target settings

Local target files remain in `targets/local/` relative to the working directory.
They override built-in targets with the same ID. Disabling a built-in target
creates a local `status: disabled` override and an archive copy; it never moves or
rewrites package data in `site-packages`. Remove the local override to restore the
built-in definition, or save a new local target with `status: ready` to re-enable
it. Explicit registry directory arguments remain available to library callers.
Missing explicit target search directories are skipped to preserve local-only
registries; an existing file supplied as a registry directory is rejected.
This does not change the errors for missing required bundled resources, custom
catalog files or custom dynamic-template directories.

## What the distribution check proves

The check verifies exact resource bytes, metadata, license files, command entry
points, built-in suite loading, both dynamic-generation APIs, all static CLI
suite selections, default scan selection, adaptive planning, report generation,
and workspace target disable/override behavior. It checks imported code is inside
the fresh environment and package bytes remain unchanged.

CLI planning checks replace only the browser execution function. They **do not**
constitute a real Selenium campaign. Browser/driver compatibility, controlled
vulnerable/hardened target campaigns, dependency advisory analysis and history-wide
secret/asset review are separate release gates. This workflow has read-only
repository permissions and does not publish, push, merge or release anything.
