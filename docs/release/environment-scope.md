# Environment audit scope

The release review distinguishes the project's resolved dependency graph from the complete temporary virtual environment. Python 3.10/3.11 may bootstrap an old setuptools into a new venv even though it is not a TrustInspect runtime dependency. That extra package is not present in the wheel's pip installation report and must not silently fall outside an environment-level assurance claim.

`tools/release_dependency_audit.py` therefore removes bootstrap setuptools only from the fresh disposable venvs it creates. It never uninstalls from the user's existing environment. Builder and test venvs subsequently install the declared setuptools minimum or newer. Runtime and replay venvs do not require setuptools to run TrustInspect.

The workflow audits both `runtime-pins.txt` (all direct/transitive application dependencies) and `runtime-environment.txt` (also including pip). Build, declared-minimum and test-environment audits remain separate. Exact bootstrap/auditor versions are recorded. No package-advisory result covers the operating system, browser or Python standard library.

This distinction was found by inspecting the retained environment lists, not inferred from a green dependency badge. Earlier candidate audit results remain attributable to their own commits; they are not the final environment result. The release must retain evidence from the final approved candidate and revalidate after merge/version changes.
