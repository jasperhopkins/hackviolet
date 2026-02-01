"""
Git Tools for Agentic Commit Analysis

Implements git operations as tools for the agent.
"""

import subprocess
import os
from typing import List, Dict, Any, Optional
from .git_handler import GitHandler
from .tool_registry import RESPONSE_LIMITS


class GitTools:
    """Git command tools for agent context gathering."""

    def __init__(self, git_handler: GitHandler):
        self.handler = git_handler
        self.repo_path = git_handler.temp_dir

    def git_log_search(
        self,
        author: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        grep: Optional[str] = None,
        path: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search commit history with filters."""

        # Validate repository
        if not self.repo_path or not os.path.exists(self.repo_path):
            raise Exception("Repository directory not found")

        # Build git command
        cmd = ['git', 'log', '--format=%H|%an|%ae|%ad|%s', '--date=iso']

        if author:
            cmd.extend(['--author', author])
        if since:
            cmd.extend(['--since', since])
        if until:
            cmd.extend(['--until', until])
        if grep:
            cmd.extend(['--grep', grep, '-i'])  # Case insensitive

        # Limit results
        limit = min(max_results, RESPONSE_LIMITS['max_git_log_entries'])
        cmd.extend(['-n', str(limit)])

        if path:
            cmd.extend(['--', path])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception(f"Git command failed: {result.stderr}")

            # Parse output
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|', 4)
                if len(parts) == 5:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4]
                    })

            return commits

        except subprocess.TimeoutExpired:
            raise Exception("Git log command timed out")
        except Exception as e:
            raise Exception(f"Failed to search git log: {str(e)}")

    def git_show_commit(
        self,
        commit_hash: str,
        show_diff: bool = False
    ) -> Dict[str, Any]:
        """Get detailed information for a specific commit."""

        if not self.repo_path or not os.path.exists(self.repo_path):
            raise Exception("Repository directory not found")

        # Get commit metadata
        cmd = ['git', 'show', '--format=%H|%an|%ae|%ad|%s|%b', '--no-patch', commit_hash]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                raise Exception(f"Commit not found: {commit_hash}")

            lines = result.stdout.strip().split('\n')
            if not lines:
                raise Exception("Empty git show output")

            parts = lines[0].split('|', 5)

            commit_info = {
                'hash': parts[0] if len(parts) > 0 else commit_hash,
                'author': parts[1] if len(parts) > 1 else 'Unknown',
                'email': parts[2] if len(parts) > 2 else '',
                'date': parts[3] if len(parts) > 3 else '',
                'message': parts[4] if len(parts) > 4 else '',
                'body': parts[5] if len(parts) > 5 else ''
            }

            # Get files changed
            stat_cmd = ['git', 'show', '--stat', '--format=', commit_hash]
            stat_result = subprocess.run(
                stat_cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            files_changed = []
            if stat_result.returncode == 0:
                for line in stat_result.stdout.strip().split('\n'):
                    if '|' in line:
                        file_path = line.split('|')[0].strip()
                        if file_path:
                            files_changed.append(file_path)

            commit_info['files_changed'] = files_changed

            # Optionally include diff
            if show_diff:
                diff = self.handler.get_commit_diff(commit_hash, max_length=RESPONSE_LIMITS['max_diff_size'])
                commit_info['diff'] = diff

            return commit_info

        except subprocess.TimeoutExpired:
            raise Exception("Git show command timed out")
        except Exception as e:
            raise Exception(f"Failed to show commit: {str(e)}")

    def git_blame_file(
        self,
        file_path: str,
        commit_hash: Optional[str] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """See line-by-line authorship for a file."""

        if not self.repo_path or not os.path.exists(self.repo_path):
            raise Exception("Repository directory not found")

        cmd = ['git', 'blame', '--line-porcelain']

        if commit_hash:
            cmd.append(commit_hash)

        if start_line and end_line:
            cmd.extend(['-L', f'{start_line},{end_line}'])

        cmd.append(file_path)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception(f"Git blame failed: {result.stderr}")

            # Parse porcelain format
            blame_data = []
            current_commit = {}

            for line in result.stdout.split('\n'):
                if not line:
                    continue

                if line[0] != '\t':  # Metadata line
                    parts = line.split(' ', 1)
                    key = parts[0]
                    value = parts[1] if len(parts) > 1 else ''

                    if len(key) == 40:  # Commit hash
                        if current_commit and 'content' in current_commit:
                            blame_data.append(current_commit)
                        current_commit = {'commit_hash': key}
                    elif key == 'author':
                        current_commit['author'] = value
                    elif key == 'author-time':
                        current_commit['timestamp'] = value
                else:  # Content line
                    current_commit['content'] = line[1:]  # Remove leading tab

            if current_commit and 'content' in current_commit:
                blame_data.append(current_commit)

            # Limit to reasonable size
            return blame_data[:200]

        except subprocess.TimeoutExpired:
            raise Exception("Git blame command timed out")
        except Exception as e:
            raise Exception(f"Failed to blame file: {str(e)}")

    def git_file_history(
        self,
        file_path: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Get commit history for a specific file."""

        if not self.repo_path or not os.path.exists(self.repo_path):
            raise Exception("Repository directory not found")

        limit = min(max_results, RESPONSE_LIMITS['max_git_log_entries'])
        cmd = [
            'git', 'log',
            '--format=%H|%an|%ad|%s',
            '--date=iso',
            f'-n', str(limit),
            '--', file_path
        ]

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
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'date': parts[2],
                        'message': parts[3]
                    })

            return commits

        except subprocess.TimeoutExpired:
            raise Exception("Git log command timed out")
        except Exception as e:
            raise Exception(f"Failed to get file history: {str(e)}")

    def git_diff_commits(
        self,
        commit_a: str,
        commit_b: str,
        file_path: Optional[str] = None
    ) -> str:
        """Compare two commits."""

        if not self.repo_path or not os.path.exists(self.repo_path):
            raise Exception("Repository directory not found")

        cmd = ['git', 'diff', commit_a, commit_b]

        if file_path:
            cmd.extend(['--', file_path])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception(f"Git diff failed: {result.stderr}")

            diff = result.stdout

            # Truncate if too long
            max_size = RESPONSE_LIMITS['max_diff_size']
            if len(diff) > max_size:
                keep_size = max_size // 2 - 100
                diff = (
                    diff[:keep_size] +
                    f"\n\n... [TRUNCATED {len(diff) - max_size} characters] ...\n\n" +
                    diff[-keep_size:]
                )

            return diff

        except subprocess.TimeoutExpired:
            raise Exception("Git diff command timed out")
        except Exception as e:
            raise Exception(f"Failed to diff commits: {str(e)}")

    def get_command_preview(self, method_name: str, params: Dict[str, Any]) -> str:
        """Generate human-readable command preview for UI."""

        if method_name == 'git_log_search':
            cmd = 'git log'
            if params.get('author'):
                cmd += f" --author='{params['author']}'"
            if params.get('since'):
                cmd += f" --since='{params['since']}'"
            if params.get('until'):
                cmd += f" --until='{params['until']}'"
            if params.get('grep'):
                cmd += f" --grep='{params['grep']}'"
            cmd += f" -n {params.get('max_results', 10)}"
            if params.get('path'):
                cmd += f" -- {params['path']}"
            return cmd

        elif method_name == 'git_show_commit':
            commit = params['commit_hash'][:8]
            cmd = f"git show {commit}"
            if params.get('show_diff'):
                cmd += " --patch"
            return cmd

        elif method_name == 'git_blame_file':
            cmd = f"git blame {params['file_path']}"
            if params.get('start_line') and params.get('end_line'):
                cmd += f" -L {params['start_line']},{params['end_line']}"
            return cmd

        elif method_name == 'git_file_history':
            cmd = f"git log -n {params.get('max_results', 10)} -- {params['file_path']}"
            return cmd

        elif method_name == 'git_diff_commits':
            a = params['commit_a'][:8]
            b = params['commit_b'][:8]
            cmd = f"git diff {a} {b}"
            if params.get('file_path'):
                cmd += f" -- {params['file_path']}"
            return cmd

        return f"{method_name}({params})"
