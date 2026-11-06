"""Safe expression evaluation and a sandboxed Python runner.

Two separate capabilities, two separate risk profiles:

``evaluate_expression``
    AST-whitelisted arithmetic on ``Decimal``. No names, no attribute access, no
    imports, no calls other than a fixed maths whitelist. Safe to expose.

``run_python``
    Executes arbitrary Python in a child process with an isolated interpreter,
    a scratch working directory, a wall-clock timeout, and CPU / memory / file
    size limits. This is a *trusted-local* capability: it is not a security
    boundary against hostile code, it is a guard against runaway loops and
    accidental file writes. Disable it with ``BOOKKEEPING_MCP_DISABLE_EXEC=1``.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import tempfile
import time
from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext
from pathlib import Path

from .money import MoneyError, as_number, quantize, to_decimal

MAX_EXPRESSION_LENGTH = 1000
MAX_EXPONENT = 1000
MAX_CODE_BYTES = 200_000
MAX_OUTPUT_CHARS = 20_000
DEFAULT_TIMEOUT = 10.0
MAX_TIMEOUT = 30.0
MEMORY_LIMIT_BYTES = 512 * 1024 * 1024
FILE_SIZE_LIMIT_BYTES = 10 * 1024 * 1024


class EvaluationError(ValueError):
    """Raised when an expression is rejected or cannot be evaluated."""


def _decimal_pow(base: Decimal, exponent: Decimal) -> Decimal:
    if exponent != exponent.to_integral_value():
        raise EvaluationError("exponent must be a whole number")
    if abs(exponent) > MAX_EXPONENT:
        raise EvaluationError(f"exponent magnitude must not exceed {MAX_EXPONENT}")
    return base ** int(exponent)


def _math_call(name: str, args: list[Decimal]) -> Decimal:
    if name == "abs":
        return abs(args[0])
    if name == "min":
        return min(args)
    if name == "max":
        return max(args)
    if name == "sum":
        return sum(args, Decimal("0"))
    if name == "round":
        if len(args) > 1 and args[1] != args[1].to_integral_value():
            raise EvaluationError("round() places must be a whole number")
        places = int(args[1]) if len(args) > 1 else 0
        return quantize(args[0], places)
    if name == "sqrt":
        if args[0] < 0:
            raise EvaluationError("sqrt of a negative number")
        return args[0].sqrt()
    if name == "log":
        if args[0] <= 0:
            raise EvaluationError("log requires a positive argument")
        return Decimal(str(args[0].ln()))
    if name == "exp":
        return Decimal(str(args[0].exp()))
    raise EvaluationError(f"unknown function: {name}")


ALLOWED_FUNCTIONS = {"abs", "min", "max", "sum", "round", "sqrt", "log", "exp"}
ALLOWED_CONSTANTS = {"pi": Decimal("3.14159265358979323846"), "e": Decimal("2.71828182845904523536")}


def _eval_node(node: ast.AST) -> Decimal:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise EvaluationError("only numeric literals are allowed")
        return to_decimal(node.value, "literal")

    if isinstance(node, ast.Name):
        if node.id in ALLOWED_CONSTANTS:
            return ALLOWED_CONSTANTS[node.id]
        raise EvaluationError(f"unknown name: {node.id}")

    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise EvaluationError("unsupported unary operator")

    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise EvaluationError("division by zero")
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            if right == 0:
                raise EvaluationError("division by zero")
            return (left / right).to_integral_value(rounding="ROUND_FLOOR")
        if isinstance(node.op, ast.Mod):
            if right == 0:
                raise EvaluationError("division by zero")
            return left % right
        if isinstance(node.op, ast.Pow):
            return _decimal_pow(left, right)
        raise EvaluationError("unsupported operator")

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCTIONS:
            raise EvaluationError("only a fixed maths function whitelist may be called")
        if node.keywords:
            raise EvaluationError("keyword arguments are not allowed")
        args = [_eval_node(arg) for arg in node.args]
        if not args:
            raise EvaluationError("functions need at least one argument")
        return _math_call(node.func.id, args)

    raise EvaluationError(f"disallowed syntax: {type(node).__name__}")


def evaluate_expression(expression: str) -> dict:
    """Evaluate arithmetic safely and return an exact decimal plus a float."""
    if not isinstance(expression, str) or not expression.strip():
        raise EvaluationError("expression is empty")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise EvaluationError(f"expression exceeds {MAX_EXPRESSION_LENGTH} characters")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise EvaluationError(f"could not parse expression: {exc.msg}") from exc

    try:
        with localcontext() as ctx:
            ctx.prec = 40
            value = _eval_node(tree)
    except (DivisionByZero, InvalidOperation) as exc:
        raise EvaluationError(f"arithmetic error: {exc}") from exc
    except MoneyError as exc:
        raise EvaluationError(str(exc)) from exc

    if not value.is_finite():
        raise EvaluationError("result is not finite")

    return {
        "expression": expression,
        "exact": str(value),
        "value": as_number(value),
        "value_2dp": as_number(quantize(value, 2)),
        "formatted": f"{quantize(value, 2):,.2f}",
    }


def exec_enabled() -> bool:
    return os.environ.get("BOOKKEEPING_MCP_DISABLE_EXEC", "").strip() not in {"1", "true", "yes"}


def _apply_limits(timeout: float):
    try:
        import resource
    except ImportError:  # pragma: no cover - non-POSIX
        return None

    def _limit() -> None:  # pragma: no cover - runs in the child
        for name, value in (
            ("RLIMIT_CPU", (int(timeout) + 1, int(timeout) + 2)),
            ("RLIMIT_AS", (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES)),
            ("RLIMIT_FSIZE", (FILE_SIZE_LIMIT_BYTES, FILE_SIZE_LIMIT_BYTES)),
            ("RLIMIT_NPROC", (64, 64)),
        ):
            limit = getattr(resource, name, None)
            if limit is None:
                continue
            try:
                resource.setrlimit(limit, value)
            except (ValueError, OSError):
                continue

    return _limit


def _instrument(code: str) -> str:
    """Echo the value of a trailing bare expression, like a REPL."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    if not tree.body or not isinstance(tree.body[-1], ast.Expr):
        return code

    last = tree.body[-1]
    assign = ast.Assign(
        targets=[ast.Name(id="_bk_result", ctx=ast.Store())],
        value=last.value,
    )
    echo = ast.Expr(
        value=ast.Call(
            func=ast.Name(id="print", ctx=ast.Load()),
            args=[
                ast.Call(
                    func=ast.Name(id="repr", ctx=ast.Load()),
                    args=[ast.Name(id="_bk_result", ctx=ast.Load())],
                    keywords=[],
                )
            ],
            keywords=[],
        )
    )
    tree.body[-1:] = [assign, echo]
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def run_python(code: str, timeout_seconds: float = DEFAULT_TIMEOUT) -> dict:
    """Run Python in a child process and capture its output.

    Returns ``ok``, ``stdout``, ``stderr``, ``exit_code``, ``timed_out`` and
    ``duration_ms``. A trailing bare expression is echoed.
    """
    if not exec_enabled():
        raise RuntimeError(
            "Code execution is disabled by BOOKKEEPING_MCP_DISABLE_EXEC. "
            "Use evaluate_expression for arithmetic."
        )
    if not isinstance(code, str) or not code.strip():
        raise ValueError("code is empty")
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        raise ValueError(f"code exceeds {MAX_CODE_BYTES} bytes")

    try:
        timeout = float(timeout_seconds)
    except (TypeError, ValueError):
        raise ValueError("timeout_seconds must be a number")
    if not 0.1 <= timeout <= MAX_TIMEOUT:
        raise ValueError(f"timeout_seconds must be between 0.1 and {MAX_TIMEOUT}")

    script = _instrument(code)
    workdir = Path(tempfile.mkdtemp(prefix="bookkeeping-mcp-"))
    started = time.monotonic()
    timed_out = False
    try:
        script_path = workdir / "main.py"
        script_path.write_text(script, encoding="utf-8")

        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(workdir),
            "TMPDIR": str(workdir),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LANG": "C.UTF-8",
        }

        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-B", str(script_path)],
                cwd=str(workdir),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=_apply_limits(timeout) if os.name == "posix" else None,
            )
            stdout, stderr, code_out = completed.stdout, completed.stderr, completed.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            code_out = None
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    duration_ms = int((time.monotonic() - started) * 1000)

    def _clip(text: str) -> tuple[str, bool]:
        if len(text) <= MAX_OUTPUT_CHARS:
            return text, False
        return text[:MAX_OUTPUT_CHARS] + "\n… [output truncated]", True

    out, out_truncated = _clip(stdout)
    err, err_truncated = _clip(stderr)

    return {
        "ok": code_out == 0 and not timed_out,
        "exit_code": code_out,
        "timed_out": timed_out,
        "duration_ms": duration_ms,
        "stdout": out,
        "stderr": err,
        "truncated": out_truncated or err_truncated,
    }
