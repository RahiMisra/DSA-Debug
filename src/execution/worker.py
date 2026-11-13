"""Worker for executing user-submitted Python code."""

from __future__ import annotations

import io
import json
import sys
import time
import traceback
import types
from pathlib import Path
from typing import Any, Callable, Optional

# Ensure project root is in sys.path when worker runs as a script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.execution.result import ExecutionError, ExecutionResult, ExecutionStatus

USER_CODE_FILENAME = "<user_code>"


def _extract_user_code_lineno(tb: types.TracebackType | None) -> Optional[int]:
    """Extract line number belonging to the user's code from a traceback."""
    if tb is None:
        return None
    extracted = traceback.extract_tb(tb)
    for frame in reversed(extracted):
        if frame.filename == USER_CODE_FILENAME:
            return frame.lineno
    return None


def _find_target_function(
    namespace: dict[str, Any],
    function_name: Optional[str],
) -> tuple[Optional[Callable[..., Any]], Optional[str], Optional[str]]:
    """Locate the target sorting function within the executed namespace.

    Returns:
        (callable_func, resolved_name, error_message)
    """
    if function_name:
        func = namespace.get(function_name)
        if func is None:
            return None, None, f"Function '{function_name}' was not found in submitted code."
        if not callable(func):
            return None, None, f"'{function_name}' is not callable."
        return func, function_name, None

    # Auto-detect user-defined functions in the namespace
    user_functions = [
        (name, obj)
        for name, obj in namespace.items()
        if isinstance(obj, types.FunctionType)
        and getattr(obj, "__code__", None)
        and obj.__code__.co_filename == USER_CODE_FILENAME
    ]

    if not user_functions:
        return None, None, "No function definition found in submitted code."

    # If exactly one function is defined, choose it
    if len(user_functions) == 1:
        return user_functions[0][1], user_functions[0][0], None

    # Check for common convention names
    for preferred_name in ("sort", "bubble_sort", "selection_sort", "insertion_sort", "merge_sort", "quick_sort"):
        for name, obj in user_functions:
            if name == preferred_name:
                return obj, name, None

    # Default to the first defined function
    return user_functions[0][1], user_functions[0][0], None


def execute_code(
    code: str,
    initial_array: list[int],
    function_name: Optional[str] = None,
) -> ExecutionResult:
    """Execute submitted Python code against an input array in-process.

    Args:
        code: User-submitted Python source code.
        initial_array: Input array of integers.
        function_name: Optional explicit name of the function to invoke.

    Returns:
        ExecutionResult containing outcome status, array state, and error details.
    """
    # 1. Syntax Check & Compilation
    try:
        compiled = compile(code, USER_CODE_FILENAME, "exec")
    except SyntaxError as exc:
        return ExecutionResult.syntax_error(
            message=exc.msg,
            line_number=exc.lineno,
            column_offset=exc.offset,
            traceback_text=traceback.format_exc(),
        )
    except Exception as exc:
        return ExecutionResult.internal_error(
            message=f"Compilation error: {exc}",
            traceback_text=traceback.format_exc(),
        )

    # 2. Namespace Preparation and Code Execution (defining functions)
    namespace: dict[str, Any] = {"__name__": "__main__"}
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    user_stdout = io.StringIO()
    user_stderr = io.StringIO()

    sys.stdout = user_stdout
    sys.stderr = user_stderr

    try:
        exec(compiled, namespace)
    except Exception as exc:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        tb = exc.__traceback__
        lineno = _extract_user_code_lineno(tb)
        return ExecutionResult.runtime_error(
            error_type=type(exc).__name__,
            message=str(exc) or type(exc).__name__,
            line_number=lineno,
            traceback_text=traceback.format_exc(),
            partial_array=list(initial_array),
        )
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    # 3. Target Function Resolution
    func, resolved_name, err_msg = _find_target_function(namespace, function_name)
    if err_msg or func is None:
        return ExecutionResult.runtime_error(
            error_type="NameError",
            message=err_msg or "Target function could not be resolved.",
            partial_array=list(initial_array),
        )

    # 4. Execute Function with Array
    array_copy = list(initial_array)
    start_time = time.perf_counter()

    sys.stdout = user_stdout
    sys.stderr = user_stderr

    try:
        return_value = func(array_copy)
    except Exception as exc:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        tb = exc.__traceback__
        lineno = _extract_user_code_lineno(tb)
        return ExecutionResult.runtime_error(
            error_type=type(exc).__name__,
            message=str(exc) or type(exc).__name__,
            line_number=lineno,
            traceback_text=traceback.format_exc(),
            partial_array=array_copy,
        )
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # If the algorithm sorted in-place, array_copy is mutated.
    # If it returned a list, use the returned list.
    if isinstance(return_value, list):
        final_array = return_value
    else:
        final_array = array_copy

    return ExecutionResult.success(
        final_array=final_array,
        execution_time_ms=elapsed_ms,
    )


def main() -> int:
    """Subprocess worker CLI entry point."""
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            result = ExecutionResult.internal_error("No execution payload received on stdin.")
            sys.stdout.write(result.to_json() + "\n")
            sys.stdout.flush()
            return 0

        payload = json.loads(raw_input)
        code = payload.get("code", "")
        initial_array = payload.get("initial_array", [])
        function_name = payload.get("function_name")

        result = execute_code(
            code=code,
            initial_array=initial_array,
            function_name=function_name,
        )
        sys.stdout.write(result.to_json() + "\n")
        sys.stdout.flush()
        return 0
    except Exception as exc:
        result = ExecutionResult.internal_error(
            message=f"Worker crashed: {exc}",
            traceback_text=traceback.format_exc(),
        )
        sys.stdout.write(result.to_json() + "\n")
        sys.stdout.flush()
        return 0


if __name__ == "__main__":
    sys.exit(main())
