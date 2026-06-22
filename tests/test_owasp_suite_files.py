from pathlib import Path
import yaml


def test_owasp_light_suite_has_10_categories():
    path = Path('examples/test_suites/owasp_llm_top10_2025_light.yaml')
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    cases = data['test_cases']
    assert len(cases) == 10
    assert len({c['owasp_id'] for c in cases}) == 10
    assert all(c.get('payload') for c in cases)
    assert all(c.get('failure_indicators') for c in cases)


def test_owasp_full_suite_has_226_tests():
    path = Path('examples/test_suites/owasp_llm_top10_2025_full.yaml')
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    cases = data['test_cases']
    assert len(cases) == 226
    assert all(c.get('payload') for c in cases)


def test_suite_registry_resolves_owasp_suites():
    from trustinspect.suites.registry import resolve_suite_path
    assert resolve_suite_path('owasp-llm-top10-2025-light').exists()
    assert resolve_suite_path('owasp-llm-top10-2025-full').exists()
