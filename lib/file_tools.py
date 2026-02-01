"""
File System Tools for Agentic Commit Analysis

Implements file operations as tools for the agent.
"""

import os
import subprocess
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from .git_handler import GitHandler
from .tool_registry import RESPONSE_LIMITS


class FileTools:
    """File system tools for agent context gathering."""

    def __init__(self, git_handler: GitHandler):
        self.handler = git_handler
        self.repo_path = git_handler.temp_dir

    def read_file(
        self,
        file_path: str,
        commit_hash: Optional[str] = None,
        max_lines: int = 200
    ) -> str:
        """Read contents of a file from the repository."""

        if not self.repo_path or not os.path.exists(self.repo_path):
            raise Exception("Repository directory not found")

        # Limit max lines
        max_lines = min(max_lines, 500)

        if commit_hash:
            # Read file at specific commit using git show
            cmd = ['git', 'show', f'{commit_hash}:{file_path}']

            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode != 0:
                    raise Exception(f"File not found in commit: {file_path}")

                content = result.stdout

            except subprocess.TimeoutExpired:
                raise Exception("Git show command timed out")
            except Exception as e:
                raise Exception(f"Failed to read file from commit: {str(e)}")
        else:
            # Read file from current working tree
            full_path = os.path.join(self.repo_path, file_path)

            if not os.path.exists(full_path):
                raise Exception(f"File not found: {file_path}")

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                raise Exception(f"Failed to read file: {str(e)}")

        # Truncate if needed
        lines = content.split('\n')
        if len(lines) > max_lines:
            truncated_lines = lines[:max_lines]
            content = '\n'.join(truncated_lines)
            content += f"\n\n... [TRUNCATED: {len(lines) - max_lines} more lines]"

        # Also check total size
        max_size = RESPONSE_LIMITS['max_file_content_size']
        if len(content) > max_size:
            content = content[:max_size] + "\n\n... [TRUNCATED: content too large]"

        return content

    def list_directory(
        self,
        directory_path: str = ".",
        recursive: bool = False,
        max_depth: int = 1
    ) -> List[str]:
        """List files in a directory."""

        if not self.repo_path or not os.path.exists(self.repo_path):
            raise Exception("Repository directory not found")

        # Limit max depth
        max_depth = min(max_depth, 3)

        full_path = os.path.join(self.repo_path, directory_path)

        if not os.path.exists(full_path):
            raise Exception(f"Directory not found: {directory_path}")

        if not os.path.isdir(full_path):
            raise Exception(f"Not a directory: {directory_path}")

        files = []

        try:
            if recursive:
                # Recursive listing with depth limit
                for root, dirs, filenames in os.walk(full_path):
                    # Calculate current depth
                    rel_root = os.path.relpath(root, full_path)
                    depth = len(rel_root.split(os.sep)) if rel_root != '.' else 0

                    if depth >= max_depth:
                        dirs.clear()  # Don't recurse deeper
                        continue

                    # Filter out .git directory
                    dirs[:] = [d for d in dirs if d != '.git']

                    for filename in filenames:
                        rel_path = os.path.relpath(
                            os.path.join(root, filename),
                            self.repo_path
                        )
                        files.append(rel_path)

                        # Limit total results
                        if len(files) >= 200:
                            break

                    if len(files) >= 200:
                        break
            else:
                # Non-recursive listing
                for item in os.listdir(full_path):
                    if item == '.git':
                        continue

                    item_path = os.path.join(full_path, item)
                    rel_path = os.path.relpath(item_path, self.repo_path)
                    files.append(rel_path)

                    if len(files) >= 200:
                        break

        except Exception as e:
            raise Exception(f"Failed to list directory: {str(e)}")

        return sorted(files)

    def search_in_files(
        self,
        pattern: str,
        file_pattern: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for a pattern across repository files."""

        if not self.repo_path or not os.path.exists(self.repo_path):
            raise Exception("Repository directory not found")

        # Limit max results
        max_results = min(max_results, RESPONSE_LIMITS['max_search_results'])

        # Use git grep for better performance and respecting .gitignore
        cmd = ['git', 'grep', '-n', '-i', '-E', pattern]

        if file_pattern:
            cmd.extend(['--', file_pattern])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            # git grep returns 1 if no matches, which is okay
            if result.returncode not in [0, 1]:
                raise Exception(f"Git grep failed: {result.stderr}")

            matches = []
            for line in result.stdout.strip().split('\n')[:max_results]:
                if not line:
                    continue

                # Parse: file:line:content
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    matches.append({
                        'file_path': parts[0],
                        'line_number': parts[1],
                        'match': parts[2].strip(),
                        'context': parts[2].strip()[:200]  # Truncate long lines
                    })

            return matches

        except subprocess.TimeoutExpired:
            raise Exception("Search timed out")
        except Exception as e:
            raise Exception(f"Failed to search files: {str(e)}")

    def find_function_definition(
        self,
        name: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Locate where a function or class is defined."""

        if not self.repo_path or not os.path.exists(self.repo_path):
            raise Exception("Repository directory not found")

        # Search for function/class definitions
        # Patterns for different languages
        patterns = [
            f'def\\s+{name}\\s*\\(',           # Python function
            f'class\\s+{name}\\s*[:({{]',      # Python/JS/Java class
            f'function\\s+{name}\\s*\\(',      # JavaScript function
            f'const\\s+{name}\\s*=.*=>',       # JS arrow function
            f'{name}\\s*:\\s*function',        # JS method
            f'public\\s+.*\\s+{name}\\s*\\(',  # Java/C# method
        ]

        for pattern in patterns:
            cmd = ['git', 'grep', '-n', '-E', pattern]

            if file_path:
                cmd.extend(['--', file_path])

            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and result.stdout.strip():
                    # Found a match
                    first_line = result.stdout.strip().split('\n')[0]
                    parts = first_line.split(':', 2)

                    if len(parts) >= 3:
                        return {
                            'file_path': parts[0],
                            'line_number': parts[1],
                            'definition_snippet': parts[2].strip()
                        }

            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue

        raise Exception(f"Function/class '{name}' not found")

    def get_related_commits(
        self,
        file_paths: List[str],
        exclude_current: bool = True,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find other commits that modified the same files."""

        if not self.repo_path or not os.path.exists(self.repo_path):
            raise Exception("Repository directory not found")

        if not file_paths:
            return []

        # Limit max results
        max_results = min(max_results, 10)

        # Get commits for all files
        cmd = [
            'git', 'log',
            '--format=%H|%an|%ad|%s',
            '--date=iso',
            f'-n', str(max_results * 2),  # Get more to account for deduplication
            '--'
        ] + file_paths[:10]  # Limit number of files

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception(f"Git log failed: {result.stderr}")

            commits = []
            seen_hashes = set()

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|', 3)
                if len(parts) == 4:
                    commit_hash = parts[0]

                    # Deduplicate
                    if commit_hash in seen_hashes:
                        continue
                    seen_hashes.add(commit_hash)

                    commits.append({
                        'hash': commit_hash,
                        'author': parts[1],
                        'date': parts[2],
                        'message': parts[3]
                    })

                    if len(commits) >= max_results:
                        break

            return commits

        except subprocess.TimeoutExpired:
            raise Exception("Git log command timed out")
        except Exception as e:
            raise Exception(f"Failed to get related commits: {str(e)}")

    def get_command_preview(self, method_name: str, params: Dict[str, Any]) -> str:
        """Generate human-readable command preview for UI."""

        if method_name == 'read_file':
            if params.get('commit_hash'):
                return f"git show {params['commit_hash'][:8]}:{params['file_path']}"
            return f"cat {params['file_path']}"

        elif method_name == 'list_directory':
            path = params.get('directory_path', '.')
            if params.get('recursive'):
                return f"ls -R {path}"
            return f"ls {path}"

        elif method_name == 'search_in_files':
            pattern = params['pattern']
            if params.get('file_pattern'):
                return f"git grep -i '{pattern}' -- '{params['file_pattern']}'"
            return f"git grep -i '{pattern}'"

        elif method_name == 'find_function_definition':
            name = params['name']
            if params.get('file_path'):
                return f"grep -n 'def {name}' {params['file_path']}"
            return f"grep -rn 'def {name}'"

        elif method_name == 'get_related_commits':
            files = params['file_paths']
            if len(files) > 2:
                file_str = f"{files[0]}, {files[1]}, ..."
            else:
                file_str = ', '.join(files)
            return f"git log -n {params.get('max_results', 5)} -- {file_str}"

        return f"{method_name}({params})"
