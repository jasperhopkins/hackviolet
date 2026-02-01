"""
Tool Registry for Agentic Commit Analysis

Defines available tools, their schemas, and usage limits.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    """Definition of a tool available to the agent."""
    name: str
    description: str
    parameters: Dict[str, Any]
    usage_limit: int
    category: str  # "git", "file", "code_analysis"
    icon: str


# Tool usage limits
TOOL_LIMITS = {
    "git_log_search": 3,
    "git_show_commit": 5,
    "git_blame_file": 3,
    "git_file_history": 3,
    "git_diff_commits": 2,
    "read_file": 8,
    "list_directory": 5,
    "search_in_files": 3,
    "find_function_definition": 5,
    "get_related_commits": 2,
}

# Global execution limits
GLOBAL_LIMITS = {
    "max_total_tool_calls": 20,
    "max_execution_time_seconds": 45,
    "max_context_tokens": 8000,
    "max_iterations": 8,
}

# Response size limits
RESPONSE_LIMITS = {
    "max_diff_size": 3000,
    "max_file_content_size": 5000,
    "max_git_log_entries": 20,
    "max_search_results": 30,
}


class ToolRegistry:
    """Registry of all available tools for the agent."""

    def __init__(self):
        self.tools = self._define_tools()

    def _define_tools(self) -> Dict[str, ToolDefinition]:
        """Define all available tools."""
        return {
            "git_log_search": ToolDefinition(
                name="git_log_search",
                description="Search commit history with filters. Use to find related commits by author, date range, or message content.",
                parameters={
                    "type": "object",
                    "properties": {
                        "author": {"type": "string", "description": "Filter by author name"},
                        "since": {"type": "string", "description": "Date filter (e.g., '2024-01-01')"},
                        "until": {"type": "string", "description": "Date filter (e.g., '2024-12-31')"},
                        "grep": {"type": "string", "description": "Search in commit messages"},
                        "path": {"type": "string", "description": "Filter by file path"},
                        "max_results": {"type": "integer", "description": "Max results (default 10, max 20)", "default": 10}
                    }
                },
                usage_limit=TOOL_LIMITS["git_log_search"],
                category="git",
                icon="🔍"
            ),
            "git_show_commit": ToolDefinition(
                name="git_show_commit",
                description="Get detailed information for a specific commit including metadata and optionally the diff.",
                parameters={
                    "type": "object",
                    "properties": {
                        "commit_hash": {"type": "string", "description": "The commit hash to show"},
                        "show_diff": {"type": "boolean", "description": "Include diff in output", "default": False}
                    },
                    "required": ["commit_hash"]
                },
                usage_limit=TOOL_LIMITS["git_show_commit"],
                category="git",
                icon="📝"
            ),
            "git_blame_file": ToolDefinition(
                name="git_blame_file",
                description="See line-by-line authorship for a file. Useful to understand who wrote specific code sections.",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"},
                        "commit_hash": {"type": "string", "description": "Commit to blame (optional, default HEAD)"},
                        "start_line": {"type": "integer", "description": "Start line number (optional)"},
                        "end_line": {"type": "integer", "description": "End line number (optional)"}
                    },
                    "required": ["file_path"]
                },
                usage_limit=TOOL_LIMITS["git_blame_file"],
                category="git",
                icon="👤"
            ),
            "git_file_history": ToolDefinition(
                name="git_file_history",
                description="Get commit history for a specific file. Shows how the file evolved over time.",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"},
                        "max_results": {"type": "integer", "description": "Max commits (default 10, max 20)", "default": 10}
                    },
                    "required": ["file_path"]
                },
                usage_limit=TOOL_LIMITS["git_file_history"],
                category="git",
                icon="📜"
            ),
            "git_diff_commits": ToolDefinition(
                name="git_diff_commits",
                description="Compare two commits to see what changed between them.",
                parameters={
                    "type": "object",
                    "properties": {
                        "commit_a": {"type": "string", "description": "First commit hash"},
                        "commit_b": {"type": "string", "description": "Second commit hash"},
                        "file_path": {"type": "string", "description": "Limit to specific file (optional)"}
                    },
                    "required": ["commit_a", "commit_b"]
                },
                usage_limit=TOOL_LIMITS["git_diff_commits"],
                category="git",
                icon="🔀"
            ),
            "read_file": ToolDefinition(
                name="read_file",
                description="Read contents of a file from the repository. Useful to understand context of changes.",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"},
                        "commit_hash": {"type": "string", "description": "Read at specific commit (optional, default current)"},
                        "max_lines": {"type": "integer", "description": "Max lines to read (default 200, max 500)", "default": 200}
                    },
                    "required": ["file_path"]
                },
                usage_limit=TOOL_LIMITS["read_file"],
                category="file",
                icon="📄"
            ),
            "list_directory": ToolDefinition(
                name="list_directory",
                description="List files in a directory. Useful to explore repository structure.",
                parameters={
                    "type": "object",
                    "properties": {
                        "directory_path": {"type": "string", "description": "Directory path (default '.')"},
                        "recursive": {"type": "boolean", "description": "List recursively", "default": False},
                        "max_depth": {"type": "integer", "description": "Max recursion depth (default 1, max 3)", "default": 1}
                    }
                },
                usage_limit=TOOL_LIMITS["list_directory"],
                category="file",
                icon="📁"
            ),
            "search_in_files": ToolDefinition(
                name="search_in_files",
                description="Search for a pattern across repository files. Useful to find similar code or patterns.",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Search pattern (regex)"},
                        "file_pattern": {"type": "string", "description": "File glob (e.g., '*.py')"},
                        "max_results": {"type": "integer", "description": "Max results (default 10, max 30)", "default": 10}
                    },
                    "required": ["pattern"]
                },
                usage_limit=TOOL_LIMITS["search_in_files"],
                category="file",
                icon="🔎"
            ),
            "find_function_definition": ToolDefinition(
                name="find_function_definition",
                description="Locate where a function or class is defined. Useful for understanding dependencies.",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Function or class name"},
                        "file_path": {"type": "string", "description": "Limit search to specific file (optional)"}
                    },
                    "required": ["name"]
                },
                usage_limit=TOOL_LIMITS["find_function_definition"],
                category="code_analysis",
                icon="🎯"
            ),
            "get_related_commits": ToolDefinition(
                name="get_related_commits",
                description="Find other commits that modified the same files. Shows related work.",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_paths": {"type": "array", "items": {"type": "string"}, "description": "List of file paths"},
                        "exclude_current": {"type": "boolean", "description": "Exclude current commit", "default": True},
                        "max_results": {"type": "integer", "description": "Max results (default 5, max 10)", "default": 5}
                    },
                    "required": ["file_paths"]
                },
                usage_limit=TOOL_LIMITS["get_related_commits"],
                category="code_analysis",
                icon="🔗"
            )
        }

    def get_tool(self, name: str) -> ToolDefinition:
        """Get tool definition by name."""
        return self.tools.get(name)

    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all tool definitions."""
        return list(self.tools.values())

    def get_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """Get tools by category."""
        return [tool for tool in self.tools.values() if tool.category == category]

    def get_anthropic_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get tool schemas in Anthropic API format."""
        schemas = []
        for tool in self.tools.values():
            schemas.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters
            })
        return schemas
