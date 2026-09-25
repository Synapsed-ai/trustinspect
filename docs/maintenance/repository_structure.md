# Maintaining repository structure

Use [the current layout](../architecture/repository_structure.md). Runtime inputs
are governed by `trustinspect/_resource_manifest.json`; moving them requires
coordinated changes to packaging, loaders and tests.

Generated reports, screenshots and locally calibrated targets are workspace
state. Keep them out of normal source commits. Preserve required LICENSE and
NOTICE files, test fixtures and validation utilities. Legacy maintenance scripts
need a dependency/reference review before removal; this cleanup does not run them.
