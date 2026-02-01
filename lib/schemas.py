"""
Data models for git commit analysis.

Defines Pydantic schemas for commit metadata and evaluations.
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class CommitMetadata(BaseModel):
    """Raw metadata extracted from a git commit."""
    
    hash: str
    author: str
    email: str
    timestamp: str
    message: str
    files_changed: List[str]
    insertions: int
    deletions: int
    lines_changed: int


class CommitEvaluation(BaseModel):
    """AI evaluation of a commit across multiple dimensions."""
    
    # Identity
    commit_hash: str
    author: str
    timestamp: str
    message: str
    
    # 6 core dimensions (1-5 scale)
    technical_complexity: int = Field(ge=1, le=5, description="How difficult was this change to implement?")
    scope_of_impact: int = Field(ge=1, le=5, description="How many systems/components does this affect?")
    code_quality_delta: int = Field(ge=1, le=5, description="Did this improve or degrade code quality?")
    risk_criticality: int = Field(ge=1, le=5, description="How critical is this to system reliability/security?")
    knowledge_sharing: int = Field(ge=1, le=5, description="How well documented and tested is this change?")
    innovation: int = Field(ge=1, le=5, description="How novel or creative is the solution?")
    
    # Contextual metadata
    categories: List[str] = Field(default_factory=list, description="Categories like bug_fix, feature, refactor, etc.")
    impact_summary: str = Field(default="", description="1-2 sentence high-level summary")
    key_files: List[str] = Field(default_factory=list, description="Most important files changed")
    reasoning: str = Field(default="", description="Detailed justification for scores")
    
    # Basic stats
    lines_added: int = 0
    lines_removed: int = 0
    files_changed: int = 0
    
    def get_average_score(self) -> float:
        """Calculate average score across all dimensions."""
        return (
            self.technical_complexity +
            self.scope_of_impact +
            self.code_quality_delta +
            self.risk_criticality +
            self.knowledge_sharing +
            self.innovation
        ) / 6.0
