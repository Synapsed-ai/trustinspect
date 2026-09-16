"""Keep regression guards enabled without matching patch strings as runtime code."""
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('ti_runtime_guards',Path(__file__).resolve().parents[1]/'scripts/maintenance/check_runtime_security_guards.py')
guards=importlib.util.module_from_spec(spec);spec.loader.exec_module(guards)


def run_check(tmp_path,code):
    folder=tmp_path/'trustinspect';folder.mkdir()
    (folder/'runtime.py').write_text(code)
    return guards.check_no_sandbox(tmp_path),guards.check_dom_snapshot_extension(tmp_path)

@pytest.mark.parametrize('code',[
    'options.add_argument("--no-sandbox")',
    'if not allow_no_sandbox:\n    options.add_argument("--no-sandbox")',
    'if unrelated or allow_no_sandbox:\n    options.add_argument("--no-sandbox")',
    'if allow_no_sandbox:\n    pass\nelse:\n    options.add_argument("--no-sandbox")',
    'switch="--no-" + "sandbox"\noptions.add_argument(switch)',
])
def test_real_unguarded_option_fails(tmp_path,code):
    assert run_check(tmp_path,code)[0]

@pytest.mark.parametrize('code',[
    'if allow_no_sandbox:\n    options.add_argument("--no-sandbox")',
    'if args.chrome_no_sandbox is True:\n    options.add_argument("--no-sandbox")',
    'if ready and allow_no_sandbox:\n    options.add_argument("--no-sandbox")',
    'message = "options.add_argument(\\\"--no-sandbox\\\")"\nprint(message)',
    'old = "snapshot_dom.html"\ntext = text.replace(old, "snapshot_dom.html.txt")\nPath("runtime.py").write_text(text)',
])
def test_explicit_opt_in_and_migration_literals_pass(tmp_path,code):
    assert run_check(tmp_path,code)==([],[])

@pytest.mark.parametrize('code',[
    'path=Path("target_dom.html")\npath.write_text(source)',
    'path=folder / f"{target}_dom.html"\npath.write_text(source)',
    'with open("target_dom.html", "w") as stream:\n    stream.write(source)',
])
def test_dom_snapshot_write_is_detected(tmp_path,code):
    assert run_check(tmp_path,code)[1]


def test_non_executable_dom_snapshot_passes(tmp_path):
    assert run_check(tmp_path,'path=Path("target_dom.html.txt")\npath.write_text(source)')==([],[])


def test_reading_html_is_not_a_snapshot_write(tmp_path):
    assert run_check(tmp_path,'text=Path("target_dom.html").read_text()')==([],[])


def test_conditional_unsafe_filename_is_not_lost(tmp_path):
    code = 'if condition:\n    path=Path("target_dom.html")\nelse:\n    path=Path("target_dom.html.txt")\npath.write_text(source)'
    assert run_check(tmp_path,code)[1]

def test_keyword_open_path_is_checked(tmp_path):
    assert run_check(tmp_path,'open(file="target_dom.html", mode="w")')[1]
