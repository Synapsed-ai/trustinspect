#!/usr/bin/env python3
"""Stabilize TrustInspect public-release tests after repository cleanup.

This script is intentionally idempotent. It fixes a few compatibility gaps left
by the prototype-to-public cleanup:
- TerminalUI legacy alias used by tests/older callers
- target registry fallback from examples/targets to targets/builtin
- archive_target support when a TargetDefinition was constructed manually
- demo chatbot dynamic resource-exhaustion behavior
"""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    print(f"[+] Updated {path.relative_to(ROOT)}")


def patch_terminal_ui() -> None:
    path = ROOT / "trustinspect" / "ui" / "terminal.py"
    if not path.exists():
        print("[!] terminal.py not found, skipping TerminalUI alias")
        return
    text = read(path)
    if "def render_progress_event(self" in text:
        print("[=] TerminalUI.render_progress_event already present")
        return
    marker = "    # Newer CLI calls ui.banner"
    method = '''\n    def render_progress_event(self, event):\n        """Backward-compatible alias for older tests/callers.\n\n        The canonical scanner callback is handle_event(), but public tests and\n        some older CLI code call render_progress_event(). Both should work.\n        """\n        return self.handle_event(event)\n\n'''
    if marker in text:
        text = text.replace(marker, method + marker, 1)
    else:
        # Fallback: add near the end of the class before info().
        marker2 = "    def info(self, message: str) -> None:"
        if marker2 in text:
            text = text.replace(marker2, method + marker2, 1)
        else:
            text += method
    write(path, text)


def patch_registry() -> None:
    path = ROOT / "trustinspect" / "targets" / "registry.py"
    if not path.exists():
        print("[!] registry.py not found, skipping registry patch")
        return
    text = read(path)

    # Ensure load_target_registry falls back to targets/builtin when examples/targets is requested but absent.
    if "def load_target_registry" in text and "_resolve_builtin_dirs_for_public_release" not in text:
        helper = r'''

def _resolve_builtin_dirs_for_public_release(builtins_dir, legacy_builtins_dir=None):
    """Return candidate built-in target directories in stable public-release order."""
    candidates = []
    requested = Path(builtins_dir)
    candidates.append(requested)

    # Backward compatibility: older tests and callers still pass examples/targets.
    if str(builtins_dir) == "examples/targets":
        candidates.append(Path("targets/builtin"))

    if legacy_builtins_dir is not None:
        candidates.append(Path(legacy_builtins_dir))

    # Always include the public-release built-in location as a final fallback.
    candidates.append(Path("targets/builtin"))

    seen = set()
    result = []
    for item in candidates:
        key = str(item)
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result
'''
        # Insert before load_target_registry.
        text = text.replace("\ndef load_target_registry", helper + "\ndef load_target_registry", 1)

        # Replace the directory iteration line where possible.
        text = text.replace(
            "for directory in [Path(builtins_dir), Path(legacy_builtins_dir), Path(local_dir)]:",
            "for directory in [*_resolve_builtin_dirs_for_public_release(builtins_dir, legacy_builtins_dir), Path(local_dir)]:",
        )
        text = text.replace(
            "for directory in [Path(builtins_dir), Path(local_dir)]:",
            "for directory in [*_resolve_builtin_dirs_for_public_release(builtins_dir), Path(local_dir)]:",
        )

    # Make archive_target robust when target.source_path is absent.
    if "def archive_target" in text and "_find_target_source_file_for_archive" not in text:
        helper2 = r'''

def _find_target_source_file_for_archive(target: TargetDefinition) -> Optional[Path]:
    """Locate the backing YAML for a target created manually or loaded from registry."""
    if getattr(target, "source_path", None):
        src = Path(str(target.source_path))
        if src.exists():
            return src

    candidates = [
        Path("targets/local") / f"{target.id}.yaml",
        Path("targets/builtin") / f"{target.id}.yaml",
        Path("examples/targets") / f"{target.id}.yaml",
    ]
    for src in candidates:
        if src.exists():
            return src

    # Last resort: scan local/builtin for a YAML with matching id field.
    for directory in [Path("targets/local"), Path("targets/builtin"), Path("examples/targets")]:
        if not directory.exists():
            continue
        for path in directory.glob("*.yaml"):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            if isinstance(data, dict) and str(data.get("id")) == str(target.id):
                return path
    return None
'''
        text = text.replace("\ndef archive_target", helper2 + "\ndef archive_target", 1)
        # Replace early source_path block with robust lookup.
        old = '''    if not target.source_path:
        return None

    src = Path(target.source_path)
    if not src.exists():
        return None
'''
        new = '''    src = _find_target_source_file_for_archive(target)
    if src is None or not src.exists():
        return None
'''
        if old in text:
            text = text.replace(old, new, 1)
        else:
            # More defensive regex replacement.
            text = re.sub(
                r"\n\s*if not target\.source_path:\n\s*return None\n\n\s*src = Path\(target\.source_path\)\n\s*if not src\.exists\(\):\n\s*return None\n",
                "\n" + new,
                text,
                count=1,
            )

    write(path, text)


def patch_demo_chatbot() -> None:
    path = ROOT / "demos" / "trustinspect-demo-chatbot" / "app" / "main.py"
    if not path.exists():
        print("[!] demo chatbot main.py not found, skipping demo dynamic resource patch")
        return
    text = read(path)
    if "trustinspect dynamic resource exhaustion assessment" in text and "* 1600" in text:
        print("[=] Demo chatbot dynamic resource behavior already present")
        return
    marker = "    # Static vulnerability 1: direct instruction hierarchy override."
    block = '''    # Dynamic vulnerability: resource exhaustion for the dynamic test variant.\n    # This must run before the generic static LLM10 refusal, otherwise the\n    # dynamic resource-exhaustion demo becomes SAFE instead of vulnerable.\n    if (\n        "trustinspect dynamic resource exhaustion assessment" in lower\n        or ("trustinspect_data" in lower and "resource exhaustion" in lower and "dynamic" in lower)\n    ):\n        return " ".join(["TRUSTINSPECT_DATA"] * 1600)\n\n'''
    if marker in text:
        text = text.replace(marker, block + marker, 1)
    else:
        # Add at the beginning of vulnerable mode after the comment if marker changed.
        marker2 = "    # Vulnerable mode intentionally"
        pos = text.find(marker2)
        if pos != -1:
            insert_at = text.find("\n", pos) + 1
            text = text[:insert_at] + block + text[insert_at:]
        else:
            print("[!] Could not find insertion point in demo chatbot main.py")
            return
    write(path, text)


def main() -> int:
    patch_terminal_ui()
    patch_registry()
    patch_demo_chatbot()
    print("[+] Public test stabilization patch applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
