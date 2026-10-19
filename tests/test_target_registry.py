from pathlib import Path

from trustinspect.targets.registry import load_target_registry


def test_registry_loads_builtin_targets():
    # Public repository location. The loader also keeps backward compatibility
    # with examples/targets, but built-ins now live under targets/builtin.
    registry = load_target_registry(builtins_dir="targets/builtin", local_dir="__missing__")
    targets = registry.list()
    ids = {t.id for t in targets}

    assert ids == {"trustinspect-demo-chatbot"}


def test_demo_chatbot_target_is_ready():
    registry = load_target_registry(builtins_dir="targets/builtin", local_dir="__missing__")
    target = registry.get("trustinspect-demo-chatbot")

    assert target is not None
    assert target.url.startswith("http://127.0.0.1")
    assert target.input_selector
    assert target.output_selector
    assert target.is_ready


def test_legacy_examples_targets_argument_falls_back_to_builtin_if_needed():
    registry = load_target_registry(builtins_dir="examples/targets", local_dir="__missing__")
    assert registry.get("trustinspect-demo-chatbot") is not None
