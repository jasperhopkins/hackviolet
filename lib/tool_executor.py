"""
Tool Executor for Agentic Commit Analysis

Manages tool execution with limit enforcement and tracking.
"""

import time
from typing import Dict, Any, Callable, Optional
from collections import defaultdict

from .git_handler import GitHandler
from .tool_registry import ToolRegistry, TOOL_LIMITS, GLOBAL_LIMITS
from .git_tools import GitTools
from .file_tools import FileTools


class LimitExceededError(Exception):
    """Raised when tool usage limits are exceeded."""
    pass


class ToolExecutor:
    """Executes tools with limit checking and usage tracking."""

    def __init__(self, git_handler: GitHandler, limits: Dict[str, int] = None):
        self.git_handler = git_handler
        self.limits = limits or TOOL_LIMITS
        self.global_limits = GLOBAL_LIMITS

        # Initialize tool implementations
        self.git_tools = GitTools(git_handler)
        self.file_tools = FileTools(git_handler)

        # Usage tracking
        self.usage = defaultdict(int)
        self.total_calls = 0
        self.start_time = None
        self.tool_history = []

    def start_session(self):
        """Start a new tool execution session."""
        self.usage.clear()
        self.total_calls = 0
        self.start_time = time.time()
        self.tool_history.clear()

    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        ui_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with limit checking and UI updates.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            ui_callback: Optional callback for UI updates

        Returns:
            Tool execution result

        Raises:
            LimitExceededError: If limits are exceeded
            Exception: If tool execution fails
        """

        # Initialize session if not started
        if self.start_time is None:
            self.start_session()

        # Check limits before execution
        self._check_limits(tool_name)

        # Get command preview for UI
        command_preview = self._get_command_preview(tool_name, parameters)

        # Notify UI: Starting
        if ui_callback:
            ui_callback({
                "event": "tool_start",
                "tool_name": tool_name,
                "parameters": parameters,
                "command": command_preview,
                "usage": dict(self.usage),
                "total_calls": self.total_calls
            })

        try:
            # Execute tool
            start = time.time()
            result = self._execute(tool_name, parameters)
            duration = time.time() - start

            # Update counters
            self.usage[tool_name] += 1
            self.total_calls += 1

            # Record in history
            self.tool_history.append({
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result,
                "duration": duration,
                "timestamp": time.time()
            })

            # Notify UI: Success
            if ui_callback:
                ui_callback({
                    "event": "tool_success",
                    "tool_name": tool_name,
                    "duration": duration,
                    "result_preview": self._get_result_preview(tool_name, result),
                    "usage": dict(self.usage),
                    "total_calls": self.total_calls
                })

            return result

        except Exception as e:
            # Notify UI: Error
            if ui_callback:
                ui_callback({
                    "event": "tool_error",
                    "tool_name": tool_name,
                    "error": str(e),
                    "usage": dict(self.usage),
                    "total_calls": self.total_calls
                })
            raise

    def _check_limits(self, tool_name: str):
        """Check if tool can be executed within limits."""

        # Check if session started
        if self.start_time is None:
            return  # Will be started in execute_tool

        # Check global timeout
        elapsed = time.time() - self.start_time
        if elapsed > self.global_limits['max_execution_time_seconds']:
            raise LimitExceededError(
                f"Global execution time limit exceeded ({elapsed:.1f}s > "
                f"{self.global_limits['max_execution_time_seconds']}s)"
            )

        # Check global call limit
        if self.total_calls >= self.global_limits['max_total_tool_calls']:
            raise LimitExceededError(
                f"Global tool call limit exceeded ({self.total_calls} >= "
                f"{self.global_limits['max_total_tool_calls']})"
            )

        # Check per-tool limit
        if tool_name in self.limits:
            if self.usage[tool_name] >= self.limits[tool_name]:
                raise LimitExceededError(
                    f"Tool '{tool_name}' call limit exceeded "
                    f"({self.usage[tool_name]} >= {self.limits[tool_name]})"
                )

    def _execute(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute the actual tool method."""

        # Git tools
        if tool_name == "git_log_search":
            return self.git_tools.git_log_search(**parameters)
        elif tool_name == "git_show_commit":
            return self.git_tools.git_show_commit(**parameters)
        elif tool_name == "git_blame_file":
            return self.git_tools.git_blame_file(**parameters)
        elif tool_name == "git_file_history":
            return self.git_tools.git_file_history(**parameters)
        elif tool_name == "git_diff_commits":
            return self.git_tools.git_diff_commits(**parameters)

        # File tools
        elif tool_name == "read_file":
            return self.file_tools.read_file(**parameters)
        elif tool_name == "list_directory":
            return self.file_tools.list_directory(**parameters)
        elif tool_name == "search_in_files":
            return self.file_tools.search_in_files(**parameters)
        elif tool_name == "find_function_definition":
            return self.file_tools.find_function_definition(**parameters)
        elif tool_name == "get_related_commits":
            return self.file_tools.get_related_commits(**parameters)

        else:
            raise Exception(f"Unknown tool: {tool_name}")

    def _get_command_preview(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Generate human-readable command preview."""

        # Try git tools first
        if hasattr(self.git_tools, tool_name):
            return self.git_tools.get_command_preview(tool_name, parameters)

        # Try file tools
        if hasattr(self.file_tools, tool_name):
            return self.file_tools.get_command_preview(tool_name, parameters)

        # Fallback
        return f"{tool_name}({', '.join(f'{k}={v}' for k, v in parameters.items())})"

    def _get_result_preview(self, tool_name: str, result: Any) -> str:
        """Generate short preview of result for UI."""

        if result is None:
            return "No result"

        # Handle different result types
        if isinstance(result, list):
            count = len(result)
            if count == 0:
                return "No results found"
            elif count == 1:
                return "Found 1 result"
            else:
                return f"Found {count} results"

        elif isinstance(result, dict):
            keys = list(result.keys())[:3]
            return f"Result with keys: {', '.join(keys)}"

        elif isinstance(result, str):
            if len(result) > 100:
                return f"{result[:100]}... ({len(result)} chars)"
            return result

        return str(result)[:100]

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of tool usage."""

        elapsed = time.time() - self.start_time if self.start_time else 0

        return {
            "total_calls": self.total_calls,
            "elapsed_time": elapsed,
            "per_tool_usage": dict(self.usage),
            "remaining_calls": {
                tool: limit - self.usage.get(tool, 0)
                for tool, limit in self.limits.items()
            },
            "global_limit_remaining": self.global_limits['max_total_tool_calls'] - self.total_calls,
            "time_limit_remaining": max(0, self.global_limits['max_execution_time_seconds'] - elapsed)
        }

    def get_tool_history(self) -> list:
        """Get history of all tool executions."""
        return self.tool_history.copy()
