# Dependency evidence for the first alpha

This is a release-review procedure, not a vulnerability-free certification. The package version remains `0.3.0a0` until an explicitly approved version decision.

## Minimums changed in this review

| Component | Previous minimum | New minimum | Reason |
| --- | --- | --- | --- |
| Jinja2 (runtime) | 3.1.2 | 3.1.6 | Includes upstream security fixes through GHSA-cpwx-vrp4-4pq7. |
| wheel (build) | 0.45 | 0.46.2 | GHSA-8rrh-rw8j-w5fx / CVE-2026-24049. |
| setuptools (build/dev) | 77 | 83.0.0 | Includes the earlier 78.1.1 correction and the Unicode MANIFEST exclusion fix documented for 83.0.0. |
| pytest (dev/test) | 8.0 | 9.0.3 | CVE-2025-71176, confirmed by the 9.0.3 upstream changelog and by auditing the advertised minimum. |

Primary references:
- https://github.com/pallets/jinja/security/advisories/GHSA-cpwx-vrp4-4pq7
- https://github.com/pypa/wheel/security/advisories/GHSA-8rrh-rw8j-w5fx
- https://github.com/pypa/setuptools/blob/v84.0.0/NEWS.rst
- https://docs.pytest.org/en/stable/changelog.html#pytest-9-0-3-2026-04-07

The pytest advisory appeared twice under the same PYSEC identifier in the initial service response. It is one distinct advisory, not two different vulnerabilities. No advisory is ignored by the dependency workflow. Raising a floor is preventive maintenance; it does not establish that TrustInspect exercised the affected upstream feature.

## What is retained

`Release Dependency Audit` records the Git commit/tree, OS, interpreter, direct and transitive package versions, downloaded-package SHA-256 hashes, build/test environments, pip inspection metadata, JSON advisory results and a CycloneDX runtime SBOM. It builds a wheel from a tracked-source sdist and proves that its runtime dependency hashes can be reinstalled in a fresh environment. The existing installed-package probe is executed outside the checkout. Linux/Python 3.11 additionally runs ordinary and real-browser tests with runtime versions constrained to the captured list.

Each matrix job emits `runtime-pins.txt`, `runtime-hashed.txt`, `build-environment.txt`, `runtime-environment.txt`, `dependency-graph.json`, `runtime-sbom.json`, audit JSON files and `summary.json`. Hash locks are platform/interpreter-specific; do not use a Linux wheel hash as a Windows lock. They are retained as CI artifacts for 90 days. The approved release's records must also be exported to durable release evidence storage before expiry.

The minimum-version audit checks the ten directly declared runtime/build/dev/package-tool floors. It is not a test of every possible older transitive combination permitted by upstream requirements. Use the recorded complete runtime lock for a reproducible assessed environment. A new resolution, platform, Python version, or release requires a fresh audit. Standard-library, browser, OS, malicious-package and undisclosed-vulnerability risks are outside pip-audit's package-advisory result.

No pipeline here publishes a release or moves a branch. Build checks, advisory checks and a human release decision are distinct gates.
