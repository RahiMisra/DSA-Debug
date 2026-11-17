"""AST instrumentation for algorithm execution tracing."""

from __future__ import annotations

import ast
from typing import Any, Optional

# Methods that mutate auxiliary stacks, queues, and hash sets.
CONTAINER_METHODS = {"append", "pop", "popleft", "add", "remove", "discard"}


COMPARE_OPS: dict[type[ast.cmpop], str] = {
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Is: "is",
    ast.IsNot: "is not",
    ast.In: "in",
    ast.NotIn: "not in",
}


class TraceInstrumenter(ast.NodeTransformer):
    """AST NodeTransformer that instruments Python code for execution tracing.

    Transforms:
    - Element comparisons (arr[j] > arr[j+1]) -> __trace_compare__(...)
    - Swaps (arr[i], arr[j] = arr[j], arr[i]) -> __trace_swap__(...)
    - Array writes (arr[i] = val, arr[i] += val) -> __trace_write__(...)
    - Array reads (arr[i] in load context) -> __trace_read__(...)
    """

    def __init__(self) -> None:
        super().__init__()
        self._inside_compare = False

    def visit_Assign(self, node: ast.Assign) -> ast.AST:
        """Instrument assignments (swaps and element writes)."""
        # 1. Check for tuple swap pattern: arr1[i], arr2[j] = ...
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Tuple)
            and len(node.targets[0].elts) == 2
            and isinstance(node.targets[0].elts[0], ast.Subscript)
            and isinstance(node.targets[0].elts[1], ast.Subscript)
            and not isinstance(node.targets[0].elts[0].slice, ast.Slice)
            and not isinstance(node.targets[0].elts[1].slice, ast.Slice)
            and isinstance(node.value, ast.Tuple)
            and len(node.value.elts) == 2
        ):
            target_left = node.targets[0].elts[0]
            target_right = node.targets[0].elts[1]

            swap_call = ast.Call(
                func=ast.Name(id="__trace_swap__", ctx=ast.Load()),
                args=[
                    target_left.value,
                    target_left.slice,
                    target_right.value,
                    target_right.slice,
                    ast.Constant(value=node.lineno),
                ],
                keywords=[],
            )
            new_node = ast.Expr(value=swap_call)
            return ast.copy_location(new_node, node)

        # 2. Check for single array write: arr[i] = val (exclude slice assignments)
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Subscript)
            and not isinstance(node.targets[0].slice, ast.Slice)
        ):
            target = node.targets[0]
            val_expr = self.visit(node.value)
            container_name = (
                target.value.id if isinstance(target.value, ast.Name) else None
            )
            write_call = ast.Call(
                func=ast.Name(id="__trace_write__", ctx=ast.Load()),
                args=[
                    target.value,
                    target.slice,
                    val_expr,
                    ast.Constant(value=node.lineno),
                    ast.Constant(value=container_name),
                ],
                keywords=[],
            )
            new_node = ast.Expr(value=write_call)
            return ast.copy_location(new_node, node)

        return self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST:
        """Instrument augmented writes: arr[i] += val."""
        if isinstance(node.target, ast.Subscript) and not isinstance(node.target.slice, ast.Slice):
            target = node.target
            val_expr = self.visit(node.value)
            bin_op = ast.BinOp(
                left=ast.Subscript(value=target.value, slice=target.slice, ctx=ast.Load()),
                op=node.op,
                right=val_expr,
            )
            container_name = (
                target.value.id if isinstance(target.value, ast.Name) else None
            )
            write_call = ast.Call(
                func=ast.Name(id="__trace_write__", ctx=ast.Load()),
                args=[
                    target.value,
                    target.slice,
                    bin_op,
                    ast.Constant(value=node.lineno),
                    ast.Constant(value=container_name),
                ],
                keywords=[],
            )
            new_node = ast.Expr(value=write_call)
            return ast.copy_location(new_node, node)

        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Instrument stack/queue mutations on simple local variable receivers."""
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.attr in CONTAINER_METHODS
            and not node.keywords
            and not any(isinstance(arg, ast.Starred) for arg in node.args)
        ):
            visited_args = [self.visit(arg) for arg in node.args]
            args_tuple = ast.Tuple(elts=visited_args, ctx=ast.Load())
            container_call = ast.Call(
                func=ast.Name(id="__trace_container_call__", ctx=ast.Load()),
                args=[
                    func.value,
                    ast.Constant(value=func.value.id),
                    ast.Constant(value=func.attr),
                    args_tuple,
                    ast.Constant(value=node.lineno),
                ],
                keywords=[],
            )
            return ast.copy_location(container_call, node)

        return self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        """Instrument binary comparisons: left <op> right."""
        if len(node.ops) == 1 and len(node.comparators) == 1:
            op_type = type(node.ops[0])
            op_str = COMPARE_OPS.get(op_type)
            if op_str is not None:
                # Extract array/index metadata if operands are single subscripts
                left_arr, left_idx = self._extract_subscript_info(node.left)
                right_arr, right_idx = self._extract_subscript_info(node.comparators[0])

                # Membership tests can target an auxiliary set or map on the right.
                container_name = (
                    node.comparators[0].id
                    if op_str in ("in", "not in")
                    and isinstance(node.comparators[0], ast.Name)
                    else None
                )

                # Mark inside_compare so child subscripts aren't wrapped in __trace_read__
                prev_inside = self._inside_compare
                self._inside_compare = True
                try:
                    left_expr = self.visit(node.left)
                    right_expr = self.visit(node.comparators[0])
                finally:
                    self._inside_compare = prev_inside

                compare_call = ast.Call(
                    func=ast.Name(id="__trace_compare__", ctx=ast.Load()),
                    args=[
                        left_expr,
                        right_expr,
                        ast.Constant(value=op_str),
                        ast.Constant(value=node.lineno),
                        left_arr,
                        left_idx,
                        right_arr,
                        right_idx,
                        ast.Constant(value=container_name),
                    ],
                    keywords=[],
                )
                return ast.copy_location(compare_call, node)

        return self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
        """Instrument array read operations in Load context (ignoring slices)."""
        if (
            isinstance(node.ctx, ast.Load)
            and not self._inside_compare
            and not isinstance(node.slice, ast.Slice)
        ):
            # Transform to __trace_read__(arr, idx, lineno, container_name)
            container_name = (
                node.value.id if isinstance(node.value, ast.Name) else None
            )
            read_call = ast.Call(
                func=ast.Name(id="__trace_read__", ctx=ast.Load()),
                args=[
                    self.visit(node.value),
                    self.visit(node.slice),
                    ast.Constant(value=node.lineno),
                    ast.Constant(value=container_name),
                ],
                keywords=[],
            )
            return ast.copy_location(read_call, node)

        return self.generic_visit(node)

    def _extract_subscript_info(self, node: ast.AST) -> tuple[ast.AST, ast.AST]:
        """Extract (array_node, slice_node) if node is a single-index Subscript, else (None, None)."""
        if isinstance(node, ast.Subscript) and not isinstance(node.slice, ast.Slice):
            return node.value, node.slice
        return ast.Constant(value=None), ast.Constant(value=None)


def instrument_code(source_code: str) -> ast.AST:
    """Parse and instrument Python source code for algorithm tracing.

    Args:
        source_code: User-submitted Python code.

    Returns:
        Transformed ast.AST ready for compilation.
    """
    tree = ast.parse(source_code)
    instrumenter = TraceInstrumenter()
    transformed_tree = instrumenter.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    return transformed_tree
