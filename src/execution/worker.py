"""Worker for executing user-submitted Python code."""

from __future__ import annotations

import inspect
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

from src.execution.instrumentation import instrument_code
from src.execution.models import ListNode, TreeNode
from src.execution.parsers import parse_leetcode_inputs
from src.execution.result import ExecutionError, ExecutionResult, ExecutionStatus
from src.execution.tracer import ExecutionTracer

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
    """Locate the target function within the executed namespace."""
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

    if len(user_functions) == 1:
        return user_functions[0][1], user_functions[0][0], None

    # Check for common convention names
    for preferred_name in (
        "sort",
        "bubble_sort",
        "selection_sort",
        "insertion_sort",
        "merge_sort",
        "quick_sort",
        "twoSum",
        "two_sum",
        "reverseList",
        "reverse_list",
        "maxDepth",
        "max_depth",
        "hasCycle",
        "has_cycle",
    ):
        for name, obj in user_functions:
            if name == preferred_name:
                return obj, name, None

    # Default to the first defined function
    return user_functions[0][1], user_functions[0][0], None


def _deserialize_initial_data(data: Any) -> Any:
    """Convert IPC data back into native models (ListNode, TreeNode) or parsed inputs."""
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if isinstance(v, dict) and v.get("__type__") == "ListNode":
                out[k] = ListNode.from_list(v.get("values", []))
            elif isinstance(v, dict) and v.get("__type__") == "TreeNode":
                out[k] = TreeNode.from_level_order(v.get("values", []))
            else:
                out[k] = v
        return out
    elif isinstance(data, str):
        return parse_leetcode_inputs(data)
    return data


def execute_code(
    code: str,
    initial_array: Any,
    function_name: Optional[str] = None,
) -> ExecutionResult:
    """Execute submitted Python code against input data in-process.

    Args:
        code: User-submitted Python source code.
        initial_array: Input array (list) or dictionary of LeetCode parsed arguments.
        function_name: Optional explicit name of the function to invoke.

    Returns:
        ExecutionResult containing outcome status, final state, events, and error details.
    """
    initial_inputs = _deserialize_initial_data(initial_array)

    init_list = []
    if isinstance(initial_inputs, list):
        init_list = initial_inputs
    elif isinstance(initial_inputs, dict):
        for v in initial_inputs.values():
            if isinstance(v, list):
                init_list = v
                break
            elif isinstance(v, ListNode):
                init_list = v.to_list()
                break
            elif isinstance(v, TreeNode):
                init_list = v.to_level_order()
                break

    tracer = ExecutionTracer(initial_array=init_list, target_filename=USER_CODE_FILENAME)

    # 1. AST Instrumentation & Compilation
    try:
        instrumented_tree = instrument_code(code)
        compiled = compile(instrumented_tree, USER_CODE_FILENAME, "exec")
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

    # 2. Namespace Preparation (auto-injecting ListNode and TreeNode)
    namespace: dict[str, Any] = {
        "__name__": "__main__",
        "ListNode": ListNode,
        "TreeNode": TreeNode,
        "__trace_compare__": tracer.trace_compare,
        "__trace_swap__": tracer.trace_swap,
        "__trace_write__": tracer.trace_write,
        "__trace_read__": tracer.trace_read,
    }
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
            partial_array=list(init_list),
            events=tracer.history.events,
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
            partial_array=list(init_list),
            events=tracer.history.events,
        )

    # 4. Prepare Function Arguments
    if isinstance(initial_inputs, dict):
        primary_list = None
        for v in initial_inputs.values():
            if isinstance(v, list):
                primary_list = v
                break
        tracer.bind_array(primary_list if primary_list is not None else [])

        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        if len(param_names) == len(initial_inputs) and all(p in initial_inputs for p in param_names):
            call_args = [initial_inputs[p] for p in param_names]
            call_kwargs = {}
        elif any(p in initial_inputs for p in param_names):
            call_args = []
            call_kwargs = {p: initial_inputs[p] for p in param_names if p in initial_inputs}
        else:
            call_args = list(initial_inputs.values())
            call_kwargs = {}
    elif isinstance(initial_inputs, list):
        primary_list = list(initial_inputs)
        tracer.bind_array(primary_list)
        call_args = [primary_list]
        call_kwargs = {}
    else:
        primary_list = []
        tracer.bind_array(primary_list)
        call_args = [initial_inputs]
        call_kwargs = {}

    start_time = time.perf_counter()
    sys.stdout = user_stdout
    sys.stderr = user_stderr

    try:
        tracer.install()
        return_value = func(*call_args, **call_kwargs)
    except Exception as exc:
        tracer.uninstall()
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
            partial_array=primary_list if primary_list is not None else init_list,
            events=tracer.history.events,
        )
    finally:
        tracer.uninstall()
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # Determine final representation
    if isinstance(return_value, ListNode):
        final_array = return_value.to_list()
    elif isinstance(return_value, TreeNode):
        final_array = return_value.to_level_order()
    elif isinstance(return_value, (int, float, str, list)):
        final_array = return_value
    elif primary_list is not None:
        final_array = primary_list
    else:
        final_array = return_value

    return ExecutionResult.success(
        final_array=final_array,
        execution_time_ms=elapsed_ms,
        events=tracer.history.events,
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
