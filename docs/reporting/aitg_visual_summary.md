# TrustInspect AITG Visual Summary Report Update

This update removes the long `Findings Summary` table from AITG reports and replaces it with a lightweight, CSS-only visual overview.

## Design choices

- No JavaScript.
- No embedded image/base64 header.
- No generic trustworthiness dimensions in the AITG summary.
- Uses OWASP AITG layers only:
  - AI Application Testing
  - AI Model Testing
  - AI Infrastructure Testing
  - AI Data Testing

## Report flow

1. Cover and assessment metadata.
2. Executive Summary.
3. Target Capability Profile.
4. Generated Test Plan Summary, grouped by OWASP AITG layer.
5. OWASP AITG Impact Overview with visual bars.
6. OWASP AITG Coverage Matrix.
7. Observations sorted by criticality.
8. Full generated test plan collapsed at the end.

The raw findings still remain in the internal data model and JSON-compatible objects. The HTML report avoids duplicating them because the Observations table already contains prompt, response, screenshots and evidence.
