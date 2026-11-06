from __future__ import annotations

import pytest

from bookkeeping_mcp.runner import (
    EvaluationError,
    evaluate_expression,
    run_python,
)


# ----------------------------------------------------------- safe evaluation


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2+2", 4.0),
        ("(1234.56 - 200) * 0.7", 724.192),
        ("100 / 3", 33.33333333),
        ("2 ** 10", 1024.0),
        ("round(1.005, 2)", 1.01),
        ("abs(-12.5)", 12.5),
        ("max(1, 5, 3)", 5.0),
        ("sum(1, 2, 3)", 6.0),
        ("sqrt(16)", 4.0),
    ],
)
def test_evaluates_arithmetic(expression, expected):
    assert evaluate_expression(expression)["value"] == pytest.approx(expected, abs=1e-8)


def test_decimal_precision_not_float():
    result = evaluate_expression("0.1 + 0.2")
    assert result["exact"] == "0.3"
    assert result["value"] == 0.3


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('echo hi')",
        "open('/etc/passwd').read()",
        "().__class__",
        "[1,2,3]",
        "'text'",
        "lambda: 1",
        "print(1)",
        "sum([1,2])",
        "1 if True else 2",
    ],
)
def test_rejects_anything_but_arithmetic(expression):
    with pytest.raises(EvaluationError):
        evaluate_expression(expression)


def test_rejects_division_by_zero():
    with pytest.raises(EvaluationError, match="division by zero"):
        evaluate_expression("1/0")


def test_rejects_huge_exponent():
    with pytest.raises(EvaluationError, match="exponent"):
        evaluate_expression("2 ** 100000")


def test_rejects_overlong_expression():
    with pytest.raises(EvaluationError, match="exceeds"):
        evaluate_expression("1" * 2000)


def test_rejects_empty_expression():
    with pytest.raises(EvaluationError):
        evaluate_expression("   ")


# ------------------------------------------------------------ python runner


def test_run_python_echoes_trailing_expression():
    result = run_python("2 + 2")
    assert result["ok"] is True
    assert result["stdout"].strip() == "4"


def test_run_python_returns_stdout_from_script():
    result = run_python("import json\nprint(json.dumps({'a': 1}))")
    assert result["ok"] is True
    assert '"a": 1' in result["stdout"]


def test_run_python_reports_traceback():
    result = run_python("raise ValueError('boom')")
    assert result["ok"] is False
    assert "ValueError" in result["stderr"]


def test_run_python_times_out():
    result = run_python("while True:\n    pass", timeout_seconds=0.5)
    assert result["timed_out"] is True
    assert result["ok"] is False


def test_run_python_rejects_oversized_timeout():
    with pytest.raises(ValueError, match="timeout_seconds"):
        run_python("1", timeout_seconds=600)


def test_run_python_rejects_empty_code():
    with pytest.raises(ValueError):
        run_python("   ")


def test_run_python_runs_in_a_scratch_directory(tmp_path):
    result = run_python("import os\nprint(os.getcwd())")
    assert result["ok"] is True
    assert "bookkeeping-mcp-" in result["stdout"]


def test_exec_can_be_disabled(monkeypatch):
    monkeypatch.setenv("BOOKKEEPING_MCP_DISABLE_EXEC", "1")
    with pytest.raises(RuntimeError, match="disabled"):
        run_python("1 + 1")
