"""Execution runner for managing isolated user code execution."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from src.execution.result import ExecutionResult, ExecutionStatus

DEFAULT_TIMEOUT_SECONDS = 3.0


def execute_code(
    code: str,
    initial_array: list[int],
    function_name: Optional[str] = None,
) -> ExecutionResult:
    """Convenience in-process execution wrapper."""
    from src.execution.worker import execute_code as _worker_execute

    return _worker_execute(
        code=code,
        initial_array=initial_array,
        function_name=function_name,
    )


class CodeRunner:
    """Manages the execution of user algorithms in an isolated subprocess."""

    def __init__(
        self,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        python_executable: Optional[str] = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.python_executable = python_executable or sys.executable
        self.project_root = Path(__file__).resolve().parent.parent.parent

    def run_in_process(
        self,
        code: str,
        initial_array: list[int],
        function_name: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute user code directly in-process (for testing and quick execution)."""
        return execute_code(
            code=code,
            initial_array=initial_array,
            function_name=function_name,
        )

    def run(
        self,
        code: str,
        initial_array: list[int],
        function_name: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> ExecutionResult:
        """Execute user code in a separate Python process with timeout enforcement.

        Args:
            code: User-provided Python source code.
            initial_array: Input array of integers.
            function_name: Optional name of the entry function.
            timeout_seconds: Max execution time before terminating the subprocess.

        Returns:
            ExecutionResult containing execution status, final array, and error details.
        """
        effective_timeout = timeout_seconds if timeout_seconds is not None else self.timeout_seconds
        payload = {
            "code": code,
            "initial_array": initial_array,
            "function_name": function_name,
        }
        payload_bytes = json.dumps(payload).encode("utf-8")

        cmd = [self.python_executable, "-m", "src.execution.worker"]

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root),
            )
        except Exception as exc:
            return ExecutionResult.internal_error(
                message=f"Failed to spawn execution worker process: {exc}"
            )

        try:
            stdout_bytes, stderr_bytes = process.communicate(
                input=payload_bytes,
                timeout=effective_timeout,
            )
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.communicate(timeout=1.0)
            except Exception:
                pass
            return ExecutionResult.timeout(
                timeout_seconds=effective_timeout,
                partial_array=list(initial_array),
            )
        except Exception as exc:
            process.kill()
            return ExecutionResult.internal_error(
                message=f"Subprocess communication error: {exc}"
            )

        stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()

        if not stdout_str:
            err_msg = f"Worker process exited with code {process.returncode}."
            if stderr_str:
                err_msg += f" Stderr: {stderr_str}"
            return ExecutionResult.internal_error(message=err_msg)

        try:
            return ExecutionResult.from_json(stdout_str)
        except Exception as exc:
            return ExecutionResult.internal_error(
                message=f"Failed to parse worker output: {exc}. Raw output: {stdout_str[:200]}"
            )
