# Installing and verifying TrustInspect

TrustInspect currently declares an alpha version (`0.3.0a0`). Building an archive
or passing CI is not a production-readiness certification or a PyPI publication.

## Development installation

From the repository checkout, create a virtual environment and run:

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
