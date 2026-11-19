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

# LeetCode input names that represent linked-list heads.
LINKED_LIST_INPUT_NAMES = {
    "head",
    "list",
    "l1",
    "l2",
    "list1",
    "list2",
    "heada",
    "headb",
}

# LeetCode input names that may hold an adjacency list for an object graph.
NODE_GRAPH_INPUT_NAMES = {
    "adjlist",
    "adj_list",
    "graph",
    "neighbors",
    "g",
    "node",
}

# Common LeetCode entry-method names, checked before definition order.
SOLUTION_METHOD_PREFERENCE = (
    "sort",
    "bubble_sort",
    "selection_sort",
    "insertion_sort",
    "merge_sort",
    "quick_sort",
    "reverseList",
    "reverse_list",
    "mergeTwoLists",
    "merge_two_lists",
    "maxDepth",
    "max_depth",
    "invertTree",
    "invert_tree",
    "isValidBST",
    "is_valid_bst",
    "lowestCommonAncestor",
    "lowest_common_ancestor",
    "numIslands",
    "num_islands",
    "cloneGraph",
    "clone_graph",
    "isValid",
    "is_valid",
    "twoSum",
    "two_sum",
    "groupAnagrams",
    "group_anagrams",
    "queueUsingStacks",
    "queue_using_stacks",
    "hasCycle",
    "has_cycle",
)


def _is_user_function(value: Any) -> bool:
    """Return True for a function compiled from the submitted source."""
    return (
        isinstance(value, types.FunctionType)
        and getattr(value, "__code__", None) is not None
        and value.__code__.co_filename == USER_CODE_FILENAME
    )


def _public_solution_methods(solution_cls: type) -> list[str]:
    """Return public callable methods declared directly on a Solution class."""
    methods: list[str] = []
    for name in vars(solution_cls):
        if name.startswith("_"):
            continue
        try:
            candidate = getattr(solution_cls, name)
        except Exception:  # pragma: no cover - defensive descriptor handling
            continue
        if inspect.isroutine(candidate):
            methods.append(name)
    return methods


def _bind_solution_method(
    solution_cls: type,
    method_name: str,
) -> tuple[Optional[Callable[..., Any]], Optional[str], Optional[str]]:
    """Instantiate ``Solution`` and return the requested bound method."""
    try:
        instance = solution_cls()
    except Exception as exc:
        return (
            None,
            None,
            f"Could not instantiate 'Solution': {type(exc).__name__}: {exc}",
        )

    method = getattr(instance, method_name, None)
    if not callable(method):
        return None, None, f"Solution method '{method_name}' is not callable."
    return method, method_name, None


def _find_target_function(
    namespace: dict[str, Any],
    function_name: Optional[str],
) -> tuple[Optional[Callable[..., Any]], Optional[str], Optional[str]]:
    """Locate a top-level function or a bound LeetCode ``Solution`` method."""
    solution_cls = namespace.get("Solution")
    if not isinstance(solution_cls, type):
        solution_cls = None

    if function_name:
        candidate = namespace.get(function_name)
        if _is_user_function(candidate):
            return candidate, function_name, None

        if solution_cls is not None:
            methods = _public_solution_methods(solution_cls)
            if function_name in methods or hasattr(solution_cls, function_name):
                return _bind_solution_method(solution_cls, function_name)

        if candidate is None:
            return (
                None,
                None,
                f"Function '{function_name}' was not found in submitted code.",
            )
        if not callable(candidate):
            return None, None, f"'{function_name}' is not callable."
        return candidate, function_name, None

    # Prefer a LeetCode Solution class when the submission defines one.
    if solution_cls is not None:
        methods = _public_solution_methods(solution_cls)
        if not methods:
            return (
                None,
                None,
                "No method definition found in the 'Solution' class.",
            )
        chosen = next(
            (name for name in SOLUTION_METHOD_PREFERENCE if name in methods),
            methods[0],
        )
        return _bind_solution_method(solution_cls, chosen)

    # Auto-detect user-defined functions in the namespace
    user_functions = [
        (name, obj)
        for name, obj in namespace.items()
        if _is_user_function(obj)
    ]

    if not user_functions:
        return None, None, "No function definition found in submitted code."

    if len(user_functions) == 1:
        return user_functions[0][1], user_functions[0][0], None

    # Check for common convention names
    for preferred_name in SOLUTION_METHOD_PREFERENCE:
        for name, obj in user_functions:
            if name == preferred_name:
                return obj, name, None

    # Default to the first defined function
    return user_functions[0][1], user_functions[0][0], None


def _build_neighbor_graph(adjacency: list[Any], node_cls: type) -> Any:
    """Build a LeetCode-style ``Node.neighbors`` graph from an adjacency list."""
    if not adjacency:
        return None

    nodes = []
    for index in range(len(adjacency)):
        try:
            nodes.append(node_cls(index + 1))
        except Exception:
            nodes.append(node_cls(index + 1, []))

    for index, neighbor_indices in enumerate(adjacency):
        if not isinstance(neighbor_indices, (list, tuple)):
            continue
        nodes[index].neighbors = [
            nodes[neighbor - 1]
            for neighbor in neighbor_indices
            if isinstance(neighbor, int) and 1 <= neighbor <= len(nodes)
        ]

    return nodes[0]


def _coerce_input_value(
    name: str,
    value: Any,
    namespace: dict[str, Any],
) -> Any:
    """Apply LeetCode-specific conversions that depend on the input name."""
    if isinstance(value, (ListNode, TreeNode)):
        return value

    lower_name = name.lower()
    node_cls = namespace.get("Node")
    if isinstance(node_cls, type) and lower_name in NODE_GRAPH_INPUT_NAMES:
        if (
            isinstance(value, list)
            and not value
            and lower_name in ("adjlist", "adj_list")
        ):
            # An empty LeetCode adjacency list represents a missing node.
            return None
        if (
            isinstance(value, list)
            and value
            and all(isinstance(row, (list, tuple)) for row in value)
        ):
            built = _build_neighbor_graph(value, node_cls)
            if built is not None:
                return built

    if lower_name in LINKED_LIST_INPUT_NAMES and isinstance(value, list):
        return ListNode.from_list(value)

    return value


def _select_primary_list(inputs: Any) -> Optional[list[Any]]:
    """Return the array-like input used for the primary event snapshots."""
    if isinstance(inputs, list):
        return list(inputs)
    if isinstance(inputs, str):
        return list(inputs)
    if not isinstance(inputs, dict):
        return None

    for value in inputs.values():
        if isinstance(value, list):
            return value
        if isinstance(value, ListNode):
            return value.to_list()
        if isinstance(value, TreeNode):
            return value.to_level_order()

    # Strings are a fallback so mixed inputs still prefer explicit arrays.
    for value in inputs.values():
        if isinstance(value, str):
            return list(value)
    return None


def _node_graph_to_adjacency(start: Any) -> list[list[int]]:
    """Convert a cloned object graph back into a sorted adjacency list."""
    from collections import deque

    nodes = []
    seen: set[int] = set()
    queue = deque([start])
    while queue:
        curr = queue.popleft()
        if id(curr) in seen or not hasattr(curr, "val"):
            continue
        seen.add(id(curr))
        nodes.append(curr)
        for neighbor in getattr(curr, "neighbors", None) or []:
            if id(neighbor) not in seen:
                queue.append(neighbor)

    if not nodes:
        return []

    try:
        nodes = sorted(nodes, key=lambda node: getattr(node, "val", 0))
    except TypeError:  # pragma: no cover - mixed label types
        pass

    index = {id(node): position + 1 for position, node in enumerate(nodes)}
    return [
        [
            index[id(neighbor)]
            for neighbor in getattr(node, "neighbors", None) or []
            if id(neighbor) in index
        ]
        for node in nodes
    ]


def _serialize_final_value(value: Any) -> Any:
    """Serialize a returned value for JSON IPC without losing graph shapes."""
    if isinstance(value, ListNode):
        return value.to_list()
    if isinstance(value, TreeNode):
        return value.to_level_order()
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_final_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        try:
            return sorted(value, key=lambda item: (type(item).__name__, repr(item)))
        except TypeError:  # pragma: no cover - mixed members
            return list(value)
    if hasattr(value, "neighbors") and hasattr(value, "val"):
        return _node_graph_to_adjacency(value)
    if isinstance(value, dict):
        return {str(key): _serialize_final_value(item) for key, item in value.items()}
    return value

    """Extract line number belonging to the user's code from a traceback."""
    if tb is None:
        return None
    extracted = traceback.extract_tb(tb)
    for frame in reversed(extracted):
        if frame.filename == USER_CODE_FILENAME:
            return frame.lineno
    return None


def _extract_user_code_lineno(tb: types.TracebackType | None) -> Optional[int]:
    """Extract line number belonging to the user's code from a traceback."""
    if tb is None:
        return None
    extracted = traceback.extract_tb(tb)
    for frame in reversed(extracted):
        if frame.filename == USER_CODE_FILENAME:
            return frame.lineno
    return None


def _deserialize_value(value: Any) -> Any:
    """Recursively restore typed IPC values, nodes, containers, and dictionary keys."""
    if isinstance(value, dict):
        value_type = value.get("__type__")
        if value_type == "ListNode":
            return ListNode.from_list(value.get("values", []))
        if value_type == "TreeNode":
            return TreeNode.from_level_order(value.get("values", []))
        if value_type == "dict":
            return {
                _deserialize_value(key): _deserialize_value(item)
                for key, item in value.get("items", [])
            }
        return {
            key: _deserialize_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_deserialize_value(item) for item in value]
    return value


def _deserialize_initial_data(data: Any) -> Any:
    """Convert IPC data back into native models (ListNode, TreeNode) or parsed inputs."""
    if isinstance(data, dict):
        return {
            key: _deserialize_value(value)
            for key, value in data.items()
        }
    elif isinstance(data, str):
        return parse_leetcode_inputs(data)
    return _deserialize_value(data)


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

    init_list = _select_primary_list(initial_inputs) or []

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
        "__trace_container_call__": tracer.trace_container_call,
        "__trace_slice__": tracer.trace_slice,
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
        prepared_inputs = {
            key: _coerce_input_value(key, value, namespace)
            for key, value in initial_inputs.items()
        }
        primary_list = _select_primary_list(prepared_inputs)
        tracer.bind_array(primary_list if primary_list is not None else [])

        sig = inspect.signature(func)
        parameters = [
            parameter
            for parameter in sig.parameters.values()
            if parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        param_names = [parameter.name for parameter in parameters]

        if len(param_names) == len(prepared_inputs) and all(
            name in prepared_inputs for name in param_names
        ):
            call_args = []
            call_kwargs = {name: prepared_inputs[name] for name in param_names}
        elif any(name in prepared_inputs for name in param_names):
            missing_required = [
                parameter.name
                for parameter in parameters
                if parameter.name not in prepared_inputs
                and parameter.default is inspect.Parameter.empty
            ]
            if missing_required:
                call_args = list(prepared_inputs.values())
                call_kwargs = {}
            else:
                call_args = []
                call_kwargs = {
                    name: prepared_inputs[name]
                    for name in param_names
                    if name in prepared_inputs
                }
        else:
            call_args = list(prepared_inputs.values())
            call_kwargs = {}
    elif isinstance(initial_inputs, list):
        primary_list = list(initial_inputs)
        tracer.bind_array(primary_list)
        call_args = [primary_list]
        call_kwargs = {}
    else:
        prepared_inputs = initial_inputs
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
    serialized_return = _serialize_final_value(return_value)
    if serialized_return is None:
        final_array = primary_list if primary_list is not None else None
    elif isinstance(serialized_return, (list, int, float, str, bool)):
        final_array = serialized_return
    elif primary_list is not None:
        final_array = primary_list
    else:
        final_array = serialized_return

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
