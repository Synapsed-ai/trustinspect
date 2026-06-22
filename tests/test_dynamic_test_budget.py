from trustinspect.cli import _select_static_and_dynamic_tests

class Dummy:
    def __init__(self, id):
        self.id = id

def test_static_tests_are_always_executed_dynamic_limited():
    static = [Dummy(f"S{i}") for i in range(8)]
    dynamic = [Dummy(f"D{i}") for i in range(8)]

    selected_static, selected_dynamic = _select_static_and_dynamic_tests(static, dynamic, 3)

    assert len(selected_static) == 8
    assert len(selected_dynamic) == 3
    assert [d.id for d in selected_dynamic] == ["D0", "D1", "D2"]

def test_no_dynamic_limit_executes_all():
    static = [Dummy(f"S{i}") for i in range(2)]
    dynamic = [Dummy(f"D{i}") for i in range(4)]

    selected_static, selected_dynamic = _select_static_and_dynamic_tests(static, dynamic, None)

    assert len(selected_static) == 2
    assert len(selected_dynamic) == 4
