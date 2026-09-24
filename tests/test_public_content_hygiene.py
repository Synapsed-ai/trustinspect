"""Check current public text, not historical commits or image OCR."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EVENT_WORDING = re.compile(r"black[\s_-]*hat|\barse" r"nal\b", re.I)
EXTENSIONS = {".py", ".md", ".txt", ".yaml", ".yml", ".json", ".html", ".j2", ".sh"}


def test_public_runtime_docs_and_catalogs_are_event_independent():
    hits = []
    for directory in ("trustinspect", "docs", "demos", "examples", "suites", "targets/builtin", "scripts"):
        for path in (ROOT / directory).rglob("*"):
            if not path.is_file() or path.suffix not in EXTENSIONS or "__pycache__" in path.parts:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if EVENT_WORDING.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{number}")
    assert not hits, "Obsolete event wording: " + ", ".join(hits)
    assert not EVENT_WORDING.search((ROOT / "README.md").read_text(encoding="utf-8"))
