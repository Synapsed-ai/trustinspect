# TrustInspect Lightweight Report Header

The default report header should be lightweight, offline-safe, and privacy-preserving.

## Decision

Use an inline ASCII/CSS header by default instead of embedding a large base64 PNG.

Reasons:

- generated reports remain small;
- reports are fully offline and self-contained;
- opening a report does not call external domains;
- strict CSP can remain in place;
- the report remains suitable as evidence.

## Optional hosted brand assets

A hosted image on `synapsed.ai` can be supported later as an explicit opt-in mode for marketing/demo exports, for example:

```bash
trustinspect ... --report-header-mode remote --report-header-url https://synapsed.ai/assets/trustinspect-header.png
```

This should not be the default because it requires network access, modifies CSP, and may leak that a report was opened.
