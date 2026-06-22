from trustinspect.dynamic.budget import select_dynamic_tests


def test_dynamic_budget_limits_only_dynamic_candidates():
    candidates = [
        {"id": "TI-DYN-001", "risk_area": "hidden_instruction_following", "metadata": {"template_priority": 10}},
        {"id": "TI-DYN-002", "risk_area": "sensitive_data_exposure", "metadata": {"template_priority": 20}},
        {"id": "TI-DYN-003", "risk_area": "system_instruction_disclosure", "metadata": {"template_priority": 30}},
    ]

    selected = select_dynamic_tests(candidates, max_dynamic_tests=2)

    assert [t["id"] for t in selected] == ["TI-DYN-001", "TI-DYN-002"]


def test_dynamic_budget_zero_or_none_means_all_dynamic():
    candidates = [{"id": "A"}, {"id": "B"}]

    assert len(select_dynamic_tests(candidates, max_dynamic_tests=None)) == 2
    assert len(select_dynamic_tests(candidates, max_dynamic_tests=0)) == 2
