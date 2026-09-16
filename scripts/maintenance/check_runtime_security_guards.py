#!/usr/bin/env python3
"""Regression guards for literal browser options and DOM snapshot filenames.

Inspect executable syntax, not words inside migration strings, comments or
messages. This is a targeted guard, not a complete Python data-flow analyzer.
Dynamic option/path construction still requires code review and runtime tests.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re

DEFAULT_ROOTS = ["trustinspect", "demos", "scripts"]
EXCLUDED_PARTS = {"tests", ".venv", "_archive", ".git", "__pycache__"}
EXCLUDED_FILES = {"check_runtime_security_guards.py"}
OPT_IN_NAMES = {"chrome_no_sandbox", "allow_no_sandbox", "no_sandbox"}
DOM_HTML = re.compile(r"(?:_dom|dom)\.html(?!\.txt)", re.IGNORECASE)


def iter_py_files(root: Path):
    for base in DEFAULT_ROOTS:
        directory = root / base
        if directory.exists():
            for path in sorted(directory.rglob("*.py")):
                if path.name not in EXCLUDED_FILES and not any(part in EXCLUDED_PARTS for part in path.parts):
                    yield path


def _positive_opt_in(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id in OPT_IN_NAMES
    if isinstance(node, ast.Attribute):
        return node.attr in OPT_IN_NAMES
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        return any(_positive_opt_in(value) for value in node.values)
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        return (isinstance(node.ops[0], (ast.Is, ast.Eq))
                and isinstance(node.comparators[0], ast.Constant)
                and node.comparators[0].value is True and _positive_opt_in(node.left))
    return False


def _text(node: ast.AST | None, bindings: dict, seen: frozenset = frozenset()) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(_text(value, bindings, seen) if isinstance(value, ast.Constant) else "{dynamic}" for value in node.values)
    if isinstance(node, ast.Name) and node.id in bindings and node.id not in seen:
        return _text(bindings[node.id], bindings, seen | {node.id})
    if isinstance(node, (ast.Tuple, ast.List)):
        return "|".join(_text(item, bindings, seen) for item in node.elts)
    if isinstance(node, ast.BinOp):
        return _text(node.left, bindings, seen) + _text(node.right, bindings, seen)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"Path", "str"} and node.args:
        return _text(node.args[0], bindings, seen)
    return ""


class GuardVisitor(ast.NodeVisitor):
    def __init__(self):
        self.bindings: dict = {}
        self.guarded = False
        self.findings: list[tuple[str, int, str]] = []

    def visit_FunctionDef(self, node):
        previous_bindings, previous_guard = self.bindings, self.guarded
        self.bindings, self.guarded = dict(previous_bindings), False
        for statement in node.body:
            self.visit(statement)
        self.bindings, self.guarded = previous_bindings, previous_guard

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_If(self, node):
        self.visit(node.test)
        old_guard, old_bindings = self.guarded, dict(self.bindings)
        self.guarded = old_guard or _positive_opt_in(node.test)
        for statement in node.body:
            self.visit(statement)
        body_bindings = dict(self.bindings)
        self.guarded = old_guard
        self.bindings = dict(old_bindings)
        for statement in node.orelse:
            self.visit(statement)
        other_bindings = dict(self.bindings)
        # Retain all statically possible branch values. A potentially unsafe
        # filename must not disappear just because it was assigned in an if.
        self.bindings = dict(old_bindings)
        for key in body_bindings.keys() | other_bindings.keys():
            possibilities = [mapping[key] for mapping in (body_bindings, other_bindings) if key in mapping]
            self.bindings[key] = ast.Tuple(elts=possibilities, ctx=ast.Load())

    def visit_Assign(self, node):
        self.visit(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.bindings[target.id] = node.value

    def visit_AnnAssign(self, node):
        if node.value is not None:
            self.visit(node.value)
            if isinstance(node.target, ast.Name):
                self.bindings[node.target.id] = node.value

    def visit_Call(self, node):
        function = node.func
        if isinstance(function, ast.Attribute) and function.attr == "add_argument":
            if any("--no-sandbox" in _text(arg, self.bindings).split("|") for arg in node.args) and not self.guarded:
                self.findings.append(("sandbox", node.lineno, "unguarded --no-sandbox option"))
        path_node = None
        if isinstance(function, ast.Attribute) and function.attr in {"write_text", "write_bytes", "touch"}:
            path_node = function.value
        if ((isinstance(function, ast.Name) and function.id == "open")
                or (isinstance(function, ast.Attribute) and function.attr == "open")):
            is_method = isinstance(function, ast.Attribute)
            index = 0 if is_method else 1
            mode = _text(node.args[index], self.bindings) if len(node.args) > index else "r"
            for keyword in node.keywords:
                if keyword.arg == "mode":
                    mode = _text(keyword.value, self.bindings)
            if any(character in mode for character in "wax"):
                path_node = function.value if is_method else (node.args[0] if node.args else None)
                if not is_method and path_node is None:
                    path_node = next((keyword.value for keyword in node.keywords if keyword.arg == "file"), None)
        if path_node is not None and DOM_HTML.search(_text(path_node, self.bindings)):
            self.findings.append(("dom", node.lineno, "DOM snapshot is written with executable .html extension"))
        self.generic_visit(node)


def _check(root: Path, kind: str) -> list[str]:
    findings = []
    for path in iter_py_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            findings.append(f"{path}: cannot inspect Python source: {exc}")
            continue
        visitor = GuardVisitor(); visitor.visit(tree)
        findings.extend(f"{path}:{line}: {message}" for category, line, message in visitor.findings if category == kind)
    return findings


def check_no_sandbox(root: Path) -> list[str]:
    return _check(root, "sandbox")


def check_dom_snapshot_extension(root: Path) -> list[str]:
    return _check(root, "dom")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    findings = list(dict.fromkeys(check_no_sandbox(args.root) + check_dom_snapshot_extension(args.root)))
    if findings:
        print("[FAIL] Runtime security guard violations detected:")
        for finding in findings:
            print(f"  - {finding}")
        return 1
    print("[OK] Runtime security guards passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
