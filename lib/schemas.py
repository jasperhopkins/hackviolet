"""
Data models for git commit analysis.

Defines Pydantic schemas for commit metadata and evaluations.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
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
    email: str = ""
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

    def get_impact_level(self) -> str:
        """Categorize commit by impact level."""
        avg = self.get_average_score()
        if avg >= 4.0:
            return "high"
        elif avg >= 2.5:
            return "medium"
        elif avg >= 1.5:
            return "low"
        else:
            return "trivial"

    def is_trivial(self) -> bool:
        """Check if commit is trivial (avg < 1.5)."""
        return self.get_average_score() < 1.5


class ImpactDistribution(BaseModel):
    """Distribution of commits across impact levels."""

    high_impact_count: int = 0      # Commits with avg >= 4.0
    medium_impact_count: int = 0    # Commits with 2.5 <= avg < 4.0
    low_impact_count: int = 0       # Commits with 1.5 <= avg < 2.5
    trivial_count: int = 0          # Commits with avg < 1.5

    @property
    def total_commits(self) -> int:
        return (self.high_impact_count + self.medium_impact_count +
                self.low_impact_count + self.trivial_count)

    @property
    def high_impact_percentage(self) -> float:
        if self.total_commits == 0:
            return 0.0
        return (self.high_impact_count / self.total_commits) * 100

    @property
    def medium_impact_percentage(self) -> float:
        if self.total_commits == 0:
            return 0.0
        return (self.medium_impact_count / self.total_commits) * 100

    @property
    def low_impact_percentage(self) -> float:
        if self.total_commits == 0:
            return 0.0
        return (self.low_impact_count / self.total_commits) * 100

    @property
    def trivial_percentage(self) -> float:
        if self.total_commits == 0:
            return 0.0
        return (self.trivial_count / self.total_commits) * 100


class DimensionDistribution(BaseModel):
    """Distribution across a single dimension (1-5 scale)."""

    dimension_name: str

    # Count of commits at each level
    score_1_count: int = 0
    score_2_count: int = 0
    score_3_count: int = 0
    score_4_count: int = 0
    score_5_count: int = 0

    @property
    def total_commits(self) -> int:
        return (self.score_1_count + self.score_2_count +
                self.score_3_count + self.score_4_count +
                self.score_5_count)

    @property
    def high_quality_count(self) -> int:
        """Commits with score >= 4"""
        return self.score_4_count + self.score_5_count

    @property
    def high_quality_percentage(self) -> float:
        if self.total_commits == 0:
            return 0.0
        return (self.high_quality_count / self.total_commits) * 100


class PeakContribution(BaseModel):
    """Record of a contributor's peak contribution."""

    commit_hash: str
    message: str
    timestamp: str
    overall_score: float
    dimension_scores: Dict[str, int]  # dimension_name -> score
    impact_summary: str


class TimeBasedMetrics(BaseModel):
    """Metrics for a specific time period."""

    period_name: str  # "last_week", "last_month", "last_year", "all_time"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    impact_distribution: ImpactDistribution
    dimension_distributions: List[DimensionDistribution] = Field(default_factory=list)

    total_lines_added: int = 0
    total_lines_removed: int = 0
    total_files_changed: int = 0

    # Peak contributions in this period
    top_3_commits: List[PeakContribution] = Field(default_factory=list)


class ContributorProfile(BaseModel):
    """Aggregate profile for a single contributor."""

    # Identity
    author_name: str
    email: str

    # Time-based metrics
    all_time: TimeBasedMetrics
    last_year: Optional[TimeBasedMetrics] = None
    last_month: Optional[TimeBasedMetrics] = None
    last_week: Optional[TimeBasedMetrics] = None

    # Overall statistics
    total_commits: int
    first_commit_date: str
    last_commit_date: str
    days_active: int

    # Category breakdown
    category_counts: Dict[str, int] = Field(default_factory=dict)  # category -> count
