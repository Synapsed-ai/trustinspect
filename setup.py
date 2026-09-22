"""Copy an explicit runtime-data allowlist without duplicating source catalogs."""
import json
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).resolve().parent


def resource_files():
    paths = json.loads((ROOT / "trustinspect/_resource_manifest.json").read_text(encoding="utf-8"))
    if not isinstance(paths, list) or any(not isinstance(p, str) for p in paths):
        raise ValueError("Runtime resource manifest must be a list of paths")
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate entries in runtime resource manifest")
    for relative in paths:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or "\\" in relative:
            raise ValueError(f"Unsafe runtime resource path: {relative}")
        source = (ROOT / path).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file():
            raise FileNotFoundError(f"Missing or external runtime resource: {relative}")
    return paths


class BuildWithRuntimeData(build_py):
    def get_source_files(self):
        return super().get_source_files() + resource_files()

    def _resource_outputs(self):
        return {str(Path(self.build_lib) / "trustinspect/_data" / p): p for p in resource_files()}

    def get_outputs(self, include_bytecode=1):
        return super().get_outputs(include_bytecode) + list(self._resource_outputs())

    def get_output_mapping(self):
        return {**super().get_output_mapping(), **self._resource_outputs()}

    def run(self):
        super().run()
        # Editable installations read original resources next to the checkout.
        if self.editable_mode:
            return
        outputs = self._resource_outputs()
        data_dir = Path(self.build_lib) / "trustinspect/_data"
        if data_dir.is_symlink():
            raise ValueError("Runtime data build directory must not be a symlink")
        if data_dir.exists():
            shutil.rmtree(data_dir)
        for output, source in outputs.items():
            self.mkpath(str(Path(output).parent))
            self.copy_file(str(ROOT / source), output)


setup(cmdclass={"build_py": BuildWithRuntimeData})
