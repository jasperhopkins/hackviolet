"""
Git repository handler for cloning and extracting commit metadata.

Uses GitPython to interact with git repositories.
"""

import os
import tempfile
import shutil
import hashlib
from git import Repo, GitCommandError
from typing import List, Optional
from .schemas import CommitMetadata


class GitHandler:
    """Handler for git repository operations."""
    
    def __init__(self):
        self.temp_dir: Optional[str] = None
        self.repo: Optional[Repo] = None
        self._total_commits: Optional[int] = None
    
    def clone_repository(self, git_url: str) -> Repo:
        """
        Clone a git repository to a temporary directory.
        
        Args:
            git_url: Git clone URL (HTTPS or SSH)
            
        Returns:
            GitPython Repo object
            
        Raises:
            GitCommandError: If cloning fails
        """
        # Create a unique temp directory based on URL hash
        url_hash = hashlib.md5(git_url.encode()).hexdigest()[:8]
        self.temp_dir = os.path.join(tempfile.gettempdir(), f"git_analysis_{url_hash}")
        
        # Remove existing directory if it exists
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        try:
            # Clone the repository
            self.repo = Repo.clone_from(git_url, self.temp_dir, depth=None)
            self._total_commits = None  # Reset cache
            return self.repo
        except GitCommandError as e:
            error_msg = str(e)
            if "Authentication failed" in error_msg or "Could not read from remote" in error_msg:
                raise Exception(f"Authentication failed. Please check your credentials or use a public repository.")
            elif "not found" in error_msg.lower():
                raise Exception(f"Repository not found. Please check the URL.")
            else:
                raise Exception(f"Failed to clone repository: {error_msg}")
    
    def extract_commit_metadata(self, skip: int = 0, limit: int = 5) -> List[CommitMetadata]:
        """
        Extract metadata for commits with pagination.
        
        Args:
            skip: Number of commits to skip
            limit: Maximum number of commits to return
            
        Returns:
            List of CommitMetadata objects
        """
        if not self.repo:
            raise Exception("Repository not cloned. Call clone_repository() first.")
        
        commits = []
        
        try:
            # Iterate through commits with skip and limit
            for i, commit in enumerate(self.repo.iter_commits()):
                if i < skip:
                    continue
                if i >= skip + limit:
                    break
                
                # Extract file changes
                files_changed = []
                insertions = 0
                deletions = 0
                
                try:
                    # Get stats from commit
                    stats = commit.stats.files
                    files_changed = list(stats.keys())
                    insertions = commit.stats.total.get('insertions', 0)
                    deletions = commit.stats.total.get('deletions', 0)
                except Exception:
                    # Handle commits without stats (e.g., first commit)
                    pass
                
                # Build metadata object
                metadata = CommitMetadata(
                    hash=commit.hexsha,
                    author=commit.author.name,
                    email=commit.author.email,
                    timestamp=commit.committed_datetime.isoformat(),
                    message=commit.message.strip(),
                    files_changed=files_changed,
                    insertions=insertions,
                    deletions=deletions,
                    lines_changed=insertions + deletions
                )
                
                commits.append(metadata)
        
        except Exception as e:
            raise Exception(f"Failed to extract commit metadata: {str(e)}")
        
        return commits
    
    def get_commit_diff(self, commit_hash: str, max_length: int = 4000) -> str:
        """
        Get unified diff for a specific commit.
        
        Args:
            commit_hash: The commit hash
            max_length: Maximum length of diff to return (for token management)
            
        Returns:
            Diff string, truncated if necessary
        """
        if not self.repo:
            raise Exception("Repository not cloned. Call clone_repository() first.")
        
        try:
            commit = self.repo.commit(commit_hash)
            
            # Get parent commit (for diff)
            if not commit.parents:
                # First commit - show entire commit
                diff_text = commit.diff(None, create_patch=True)
            else:
                # Normal commit - diff with parent
                diff_text = commit.diff(commit.parents[0], create_patch=True)
            
            # Convert diff to string
            diff_str = ""
            for diff_item in diff_text:
                try:
                    diff_str += str(diff_item) + "\n"
                except Exception:
                    diff_str += f"[Binary or unreadable diff for {diff_item.a_path or diff_item.b_path}]\n"
            
            # Truncate if too long
            if len(diff_str) > max_length:
                # Keep beginning and end
                keep_size = max_length // 2 - 100
                diff_str = (
                    diff_str[:keep_size] +
                    f"\n\n... [TRUNCATED {len(diff_str) - max_length} characters] ...\n\n" +
                    diff_str[-keep_size:]
                )
            
            return diff_str
        
        except Exception as e:
            return f"[Unable to generate diff: {str(e)}]"
    
    def get_total_commits(self) -> int:
        """
        Get total number of commits in the repository.
        
        Returns:
            Total commit count
        """
        if not self.repo:
            raise Exception("Repository not cloned. Call clone_repository() first.")
        
        # Cache the result
        if self._total_commits is None:
            try:
                self._total_commits = sum(1 for _ in self.repo.iter_commits())
            except Exception:
                self._total_commits = 0
        
        return self._total_commits
    
    def get_repo_info(self) -> dict:
        """
        Get basic repository information.
        
        Returns:
            Dictionary with repo info (branch, remote, etc.)
        """
        if not self.repo:
            raise Exception("Repository not cloned. Call clone_repository() first.")
        
        try:
            return {
                'active_branch': self.repo.active_branch.name,
                'remotes': [remote.name for remote in self.repo.remotes],
                'total_commits': self.get_total_commits(),
            }
        except Exception as e:
            return {
                'error': str(e),
                'total_commits': self.get_total_commits(),
            }
    
    def cleanup(self):
        """Remove temporary repository clone."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
                self.repo = None
                self._total_commits = None
            except Exception as e:
                print(f"Warning: Failed to cleanup temporary directory: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()
