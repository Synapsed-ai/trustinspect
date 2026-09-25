"""Public dynamic-generation APIs, loaded without pre-importing module CLIs."""
from importlib import import_module
from typing import TYPE_CHECKING

__all__ = ["DynamicTestEngine", "generate_dynamic_tests", "generate_dynamic_tests_for_static_suite"]

if TYPE_CHECKING:
    from .engine import DynamicTestEngine, generate_dynamic_tests
    from .per_static import generate_dynamic_tests_for_static_suite


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = ".per_static" if name == "generate_dynamic_tests_for_static_suite" else ".engine"
    value = getattr(import_module(module, __name__), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
