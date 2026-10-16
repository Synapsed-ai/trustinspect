"""Remove only the two approved presentation labels; retain all other pixels."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median
from PIL import Image, PngImagePlugin

SPECS = {
    "01-launcher.png": ("07a1f91d0f8ebc28425e971e71b76a71cfa6bc78", (90, 312, 294, 329)),
    "05-html-report-overview.png": ("d5b484100302a7d2dcb21e153e91ead08696f4b1", (214, 128, 374, 154)),
}


def prepare(source_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for name, (expected, box) in SPECS.items():
        raw = (source_dir / name).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if blob != expected:
            raise ValueError(f"{name}: original image identity changed; review required")
        original = Image.open(source_dir / name)
        before = original.convert("RGBA")
        after = before.copy()
        a, b = before.load(), after.load()
        left, top, right, bottom = box
        for y in range(top, bottom):
            weight = (y - top + 1) / (bottom - top + 1)
            delta = [median(a[q, y][c] - ((1-weight)*a[q, top-1][c] + weight*a[q, bottom][c])
                            for q in range(right+2, right+30)) for c in range(3)]
            for x in range(left, right):
                if name == "01-launcher.png":
                    b[x, y] = a[right+5, top]
                else:
                    row = [(1-weight)*a[x, top-1][c] + weight*a[x, bottom][c] for c in range(4)]
                    b[x, y] = tuple(max(0, min(255, round(row[c] + (delta[c] if c < 3 else 0)))) for c in range(4))
        for y in range(before.height):
            for x in range(before.width):
                if not (left <= x < right and top <= y < bottom) and a[x, y] != b[x, y]:
                    raise AssertionError("Pixels changed outside the approved label rectangle")
        metadata = PngImagePlugin.PngInfo()
        for key, value in original.info.items():
            if isinstance(value, str):
                metadata.add_text(key, value)
        target = output_dir / name
        after.save(target, optimize=True, icc_profile=original.info.get("icc_profile"),
                   exif=original.info.get("exif"), pnginfo=metadata)
        saved = Image.open(target)
        assert saved.info.get("icc_profile") == original.info.get("icc_profile")
        assert saved.convert("RGBA").tobytes() == after.tobytes()
        records.append({"file": name, "source_git_blob": expected, "rectangle": list(box),
                        "size": list(after.size), "outside_pixels_unchanged": True, "icc_preserved": True,
                        "pixel_sha256": hashlib.sha256(after.tobytes()).hexdigest(),
                        "file_sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    (output_dir / "media-verification.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output)))
