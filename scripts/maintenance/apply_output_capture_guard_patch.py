from __future__ import annotations

from pathlib import Path
import re

ROOT = Path.cwd()


def patch_file(path: Path, transform) -> bool:
    text = path.read_text(encoding="utf-8")
    new_text = transform(text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        print(f"[+] Patched {path}")
        return True
    print(f"[=] No change {path}")
    return False


def ensure_dom_snapshot_enum(text: str) -> str:
    if 'DOM_SNAPSHOT = "dom_snapshot"' in text:
        return text
    if 'SCREENSHOT = "screenshot"' in text:
        return text.replace(
            'SCREENSHOT = "screenshot"',
            'SCREENSHOT = "screenshot"\n    DOM_SNAPSHOT = "dom_snapshot"',
            1,
        )
    return text


def patch_scanner(text: str) -> str:
    if "output_capture_guard" not in text:
        marker = "from trustinspect.scanners.base import ScannerAdapter\n"
        import_line = (
            "from trustinspect.scanners.web_ui.output_capture_guard import "
            "is_prompt_echo, format_prompt_echo_error\n"
        )
        if marker in text:
            text = text.replace(marker, marker + import_line, 1)
        else:
            text = import_line + text

    if "Output capture appears to be the submitted user prompt" in text:
        return text

    # Insert after any line that assigns response_text from _wait_for_response(...).
    lines = text.splitlines()
    out: list[str] = []
    inserted = False
    for line in lines:
        out.append(line)
        if not inserted and re.search(r"response_text\s*=\s*self\._wait_for_response\(", line):
            indent = re.match(r"^(\s*)", line).group(1)
            out.extend([
                f"{indent}_ti_payload_for_guard = getattr(test_case, 'payload', None) or getattr(test_case, 'prompt', '')",
                f"{indent}_ti_is_echo, _ti_echo_reason, _ti_echo_score = is_prompt_echo(_ti_payload_for_guard, response_text)",
                f"{indent}if _ti_is_echo:",
                f"{indent}    raise RuntimeError(format_prompt_echo_error(",
                f"{indent}        _ti_payload_for_guard,",
                f"{indent}        response_text,",
                f"{indent}        input_selector=self.input_selector,",
                f"{indent}        output_selector=self.output_selector,",
                f"{indent}    ))",
            ])
            inserted = True
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def patch_analyzer(text: str) -> str:
    if "output_capture_guard" not in text:
        marker = "from trustinspect.core.models import Classification, TestCase\n"
        import_line = "from trustinspect.scanners.web_ui.output_capture_guard import is_prompt_echo\n"
        if marker in text:
            text = text.replace(marker, marker + import_line, 1)
        else:
            text = import_line + text

    if "Output capture guard:" in text:
        return text

    needle = "        text = (response_text or \"\").strip()\n"
    block = """        text = (response_text or \"\").strip()

        _ti_payload_for_guard = getattr(test_case, \"payload\", None) or getattr(test_case, \"prompt\", \"\")
        _ti_is_echo, _ti_echo_reason, _ti_echo_score = is_prompt_echo(_ti_payload_for_guard, text)
        if _ti_is_echo:
            return (
                Classification.ERROR,
                0.0,
                f\"Output capture guard: {_ti_echo_reason}. The captured response appears to be the user prompt, not the assistant response. Recalibrate the output selector.\",
            )
"""
    if needle in text:
        return text.replace(needle, block, 1)
    return text


def main() -> None:
    models = ROOT / "trustinspect" / "core" / "models.py"
    scanner = ROOT / "trustinspect" / "scanners" / "web_ui" / "selenium_scanner.py"
    analyzer = ROOT / "trustinspect" / "analyzers" / "heuristic.py"

    if models.exists():
        patch_file(models, ensure_dom_snapshot_enum)
    else:
        print(f"[!] Missing {models}")

    if scanner.exists():
        patch_file(scanner, patch_scanner)
    else:
        print(f"[!] Missing {scanner}")

    if analyzer.exists():
        patch_file(analyzer, patch_analyzer)
    else:
        print(f"[!] Missing {analyzer}")

    print("\n[+] Output Capture Guard patch applied.")
    print("    Run: pip install -e .")
    print("    Then rerun the target. Prompt echo captures should now be ERROR, not vulnerabilities.")


if __name__ == "__main__":
    main()
