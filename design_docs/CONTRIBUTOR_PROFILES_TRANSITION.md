# Transition Plan: MVP to Contributor Profile Analytics

## Executive Summary

This document outlines the architectural and implementation steps to evolve from individual commit analysis to aggregate contributor profiles with distribution-based impact metrics. The new system will fairly represent both high-volume contributors and quality-focused developers while avoiding the pitfalls of simple averaging.

---

## Current State Analysis

### Existing Data Model
- **CommitEvaluation**: Individual commit with 6 dimensions (1-5 scale)
- **Storage**: Session-state only, no persistence
- **Metrics**: Single `get_average_score()` method (problematic)
- **View**: Commit-by-commit card display

### Known Limitations
1. **Averaging Bias**: Punishes frequent committers with occasional low-impact commits
2. **No Historical Context**: Cannot compare time periods
3. **Loss of Distribution**: High/medium/low impact patterns hidden
4. **Trivial Commits**: Small fixes drag down overall scores unfairly
5. **Single-Dimension Reduction**: Rich 6D data collapsed to one number

---

## New Architecture: Contributor Profiles

### 1. Data Model Extensions

#### 1.1 New Schema: `ContributorProfile`
```python
# lib/schemas.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

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
```

#### 1.2 Modified Schema: `CommitEvaluation`
```python
# Add to existing CommitEvaluation class

class CommitEvaluation(BaseModel):
    # ... existing fields ...

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
```

---

### 2. Business Logic Layer

#### 2.1 New Module: `lib/contributor_aggregator.py`

```python
"""
Aggregate commit evaluations into contributor profiles.

Builds distribution-based metrics from individual commit evaluations.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from .schemas import (
    CommitEvaluation,
    ContributorProfile,
    TimeBasedMetrics,
    ImpactDistribution,
    DimensionDistribution,
    PeakContribution
)


class ContributorAggregator:
    """Aggregates commit evaluations into contributor profiles."""

    def __init__(self, evaluations: List[CommitEvaluation]):
        """
        Initialize aggregator with commit evaluations.

        Args:
            evaluations: List of all commit evaluations
        """
        self.evaluations = evaluations

    def build_profiles(self) -> List[ContributorProfile]:
        """
        Build contributor profiles from evaluations.

        Returns:
            List of ContributorProfile objects, sorted by impact
        """
        # Group commits by author
        author_commits: Dict[str, List[CommitEvaluation]] = defaultdict(list)
        for eval in self.evaluations:
            author_commits[eval.author].append(eval)

        # Build profile for each author
        profiles = []
        for author, commits in author_commits.items():
            profile = self._build_single_profile(author, commits)
            profiles.append(profile)

        # Sort by high-impact commit count (descending)
        profiles.sort(
            key=lambda p: p.all_time.impact_distribution.high_impact_count,
            reverse=True
        )

        return profiles

    def _build_single_profile(
        self,
        author: str,
        commits: List[CommitEvaluation]
    ) -> ContributorProfile:
        """Build profile for a single contributor."""

        # Extract email (assuming consistent per author)
        email = commits[0].email if hasattr(commits[0], 'email') else ""

        # Sort commits by timestamp
        sorted_commits = sorted(
            commits,
            key=lambda c: datetime.fromisoformat(c.timestamp.replace('Z', '+00:00'))
        )

        # Date range
        first_date = sorted_commits[0].timestamp
        last_date = sorted_commits[-1].timestamp

        first_dt = datetime.fromisoformat(first_date.replace('Z', '+00:00'))
        last_dt = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
        days_active = (last_dt - first_dt).days + 1

        # Build time-based metrics
        all_time = self._build_time_metrics("all_time", commits)
        last_year = self._build_time_metrics("last_year", commits, days=365)
        last_month = self._build_time_metrics("last_month", commits, days=30)
        last_week = self._build_time_metrics("last_week", commits, days=7)

        # Category breakdown
        category_counts = defaultdict(int)
        for commit in commits:
            for category in commit.categories:
                category_counts[category] += 1

        return ContributorProfile(
            author_name=author,
            email=email,
            all_time=all_time,
            last_year=last_year if last_year.impact_distribution.total_commits > 0 else None,
            last_month=last_month if last_month.impact_distribution.total_commits > 0 else None,
            last_week=last_week if last_week.impact_distribution.total_commits > 0 else None,
            total_commits=len(commits),
            first_commit_date=first_date,
            last_commit_date=last_date,
            days_active=days_active,
            category_counts=dict(category_counts)
        )

    def _build_time_metrics(
        self,
        period_name: str,
        all_commits: List[CommitEvaluation],
        days: Optional[int] = None
    ) -> TimeBasedMetrics:
        """
        Build metrics for a specific time period.

        Args:
            period_name: Name of the period
            all_commits: All commits for this author
            days: Number of days to look back (None = all time)
        """
        # Filter commits by time period
        if days is None:
            commits = all_commits
            start_date = None
            end_date = None
        else:
            cutoff = datetime.now() - timedelta(days=days)
            commits = [
                c for c in all_commits
                if datetime.fromisoformat(c.timestamp.replace('Z', '+00:00')) >= cutoff
            ]
            start_date = cutoff.isoformat()
            end_date = datetime.now().isoformat()

        # Build impact distribution
        impact_dist = ImpactDistribution()
        for commit in commits:
            level = commit.get_impact_level()
            if level == "high":
                impact_dist.high_impact_count += 1
            elif level == "medium":
                impact_dist.medium_impact_count += 1
            elif level == "low":
                impact_dist.low_impact_count += 1
            else:  # trivial
                impact_dist.trivial_count += 1

        # Build dimension distributions
        dimension_dists = self._build_dimension_distributions(commits)

        # Calculate totals
        total_lines_added = sum(c.lines_added for c in commits)
        total_lines_removed = sum(c.lines_removed for c in commits)
        total_files_changed = sum(c.files_changed for c in commits)

        # Find top 3 commits
        top_commits = sorted(
            commits,
            key=lambda c: c.get_average_score(),
            reverse=True
        )[:3]

        top_3 = [
            PeakContribution(
                commit_hash=c.commit_hash,
                message=c.message,
                timestamp=c.timestamp,
                overall_score=c.get_average_score(),
                dimension_scores={
                    "technical_complexity": c.technical_complexity,
                    "scope_of_impact": c.scope_of_impact,
                    "code_quality_delta": c.code_quality_delta,
                    "risk_criticality": c.risk_criticality,
                    "knowledge_sharing": c.knowledge_sharing,
                    "innovation": c.innovation
                },
                impact_summary=c.impact_summary
            )
            for c in top_commits
        ]

        return TimeBasedMetrics(
            period_name=period_name,
            start_date=start_date,
            end_date=end_date,
            impact_distribution=impact_dist,
            dimension_distributions=dimension_dists,
            total_lines_added=total_lines_added,
            total_lines_removed=total_lines_removed,
            total_files_changed=total_files_changed,
            top_3_commits=top_3
        )

    def _build_dimension_distributions(
        self,
        commits: List[CommitEvaluation]
    ) -> List[DimensionDistribution]:
        """Build distributions for each of the 6 dimensions."""

        dimensions = [
            "technical_complexity",
            "scope_of_impact",
            "code_quality_delta",
            "risk_criticality",
            "knowledge_sharing",
            "innovation"
        ]

        distributions = []

        for dim_name in dimensions:
            dist = DimensionDistribution(dimension_name=dim_name)

            for commit in commits:
                score = getattr(commit, dim_name)
                if score == 1:
                    dist.score_1_count += 1
                elif score == 2:
                    dist.score_2_count += 1
                elif score == 3:
                    dist.score_3_count += 1
                elif score == 4:
                    dist.score_4_count += 1
                elif score == 5:
                    dist.score_5_count += 1

            distributions.append(dist)

        return distributions
```

---

### 3. Data Persistence Layer

#### 3.1 New Module: `lib/storage.py`

**Why Persistence?**
- Current session state is lost on page refresh
- Contributor profiles require expensive re-computation
- Enable historical tracking and caching

**Storage Options:**

**Option A: SQLite (Recommended for MVP+)**
```python
"""
SQLite-based persistence for commit evaluations and profiles.
"""

import sqlite3
import json
from typing import List, Optional
from pathlib import Path

from .schemas import CommitEvaluation, ContributorProfile


class CommitDatabase:
    """SQLite database for commit evaluations."""

    def __init__(self, db_path: str = "commit_analysis.db"):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_db()

    def _initialize_db(self):
        """Create tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Commits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commits (
                commit_hash TEXT PRIMARY KEY,
                author TEXT NOT NULL,
                email TEXT,
                timestamp TEXT NOT NULL,
                message TEXT,
                repo_url TEXT NOT NULL,
                technical_complexity INTEGER,
                scope_of_impact INTEGER,
                code_quality_delta INTEGER,
                risk_criticality INTEGER,
                knowledge_sharing INTEGER,
                innovation INTEGER,
                categories TEXT,  -- JSON array
                impact_summary TEXT,
                key_files TEXT,  -- JSON array
                reasoning TEXT,
                lines_added INTEGER,
                lines_removed INTEGER,
                files_changed INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Index for fast author lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_author
            ON commits(author)
        """)

        # Index for time-based queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON commits(timestamp)
        """)

        self.conn.commit()

    def save_evaluation(self, evaluation: CommitEvaluation, repo_url: str):
        """Save a single commit evaluation."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO commits VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
            )
        """, (
            evaluation.commit_hash,
            evaluation.author,
            getattr(evaluation, 'email', ''),
            evaluation.timestamp,
            evaluation.message,
            repo_url,
            evaluation.technical_complexity,
            evaluation.scope_of_impact,
            evaluation.code_quality_delta,
            evaluation.risk_criticality,
            evaluation.knowledge_sharing,
            evaluation.innovation,
            json.dumps(evaluation.categories),
            evaluation.impact_summary,
            json.dumps(evaluation.key_files),
            evaluation.reasoning,
            evaluation.lines_added,
            evaluation.lines_removed,
            evaluation.files_changed
        ))

        self.conn.commit()

    def get_evaluations_by_repo(self, repo_url: str) -> List[CommitEvaluation]:
        """Retrieve all evaluations for a repository."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM commits WHERE repo_url = ?
            ORDER BY timestamp DESC
        """, (repo_url,))

        rows = cursor.fetchall()
        return [self._row_to_evaluation(row) for row in rows]

    def get_evaluations_by_author(
        self,
        author: str,
        repo_url: Optional[str] = None
    ) -> List[CommitEvaluation]:
        """Retrieve all evaluations for an author."""
        cursor = self.conn.cursor()

        if repo_url:
            cursor.execute("""
                SELECT * FROM commits
                WHERE author = ? AND repo_url = ?
                ORDER BY timestamp DESC
            """, (author, repo_url))
        else:
            cursor.execute("""
                SELECT * FROM commits
                WHERE author = ?
                ORDER BY timestamp DESC
            """, (author,))

        rows = cursor.fetchall()
        return [self._row_to_evaluation(row) for row in rows]

    def _row_to_evaluation(self, row) -> CommitEvaluation:
        """Convert database row to CommitEvaluation."""
        return CommitEvaluation(
            commit_hash=row[0],
            author=row[1],
            timestamp=row[3],
            message=row[4],
            technical_complexity=row[6],
            scope_of_impact=row[7],
            code_quality_delta=row[8],
            risk_criticality=row[9],
            knowledge_sharing=row[10],
            innovation=row[11],
            categories=json.loads(row[12]) if row[12] else [],
            impact_summary=row[13] or "",
            key_files=json.loads(row[14]) if row[14] else [],
            reasoning=row[15] or "",
            lines_added=row[16] or 0,
            lines_removed=row[17] or 0,
            files_changed=row[18] or 0
        )

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
```

**Option B: JSON File Storage (Simpler, good for MVP+)**
```python
"""
JSON file-based persistence for commit evaluations.
"""

import json
from pathlib import Path
from typing import List, Dict

from .schemas import CommitEvaluation


class JSONStorage:
    """JSON file storage for evaluations."""

    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save_evaluations(self, repo_url: str, evaluations: List[CommitEvaluation]):
        """Save evaluations to JSON file."""
        # Create safe filename from repo URL
        filename = self._url_to_filename(repo_url)
        filepath = self.storage_dir / f"{filename}.json"

        # Convert to JSON-serializable format
        data = {
            "repo_url": repo_url,
            "evaluations": [eval.model_dump() for eval in evaluations]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_evaluations(self, repo_url: str) -> List[CommitEvaluation]:
        """Load evaluations from JSON file."""
        filename = self._url_to_filename(repo_url)
        filepath = self.storage_dir / f"{filename}.json"

        if not filepath.exists():
            return []

        with open(filepath, 'r') as f:
            data = json.load(f)

        return [CommitEvaluation(**eval_dict) for eval_dict in data["evaluations"]]

    def _url_to_filename(self, repo_url: str) -> str:
        """Convert repo URL to safe filename."""
        import hashlib
        return hashlib.md5(repo_url.encode()).hexdigest()
```

---

### 4. UI Layer: Contributor Profile Page

#### 4.1 New Page: `pages/5_ContributorProfiles.py`

```python
"""
Contributor Profile Analytics - Streamlit Page

Distribution-based impact metrics for contributors.
"""

import streamlit as st
import sys
import os
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Contributor Profiles • CodeOrigin",
    page_icon="👥",
    layout="wide"
)

# Navigation
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.page_link("1_Home.py", label="Home", icon="🏠")
with c2: st.page_link("pages/2_DemoVideo.py", label="Demo", icon="🎥")
with c3: st.page_link("pages/4_CommitAnalysis.py", label="CodeOrigin", icon="🔍")
with c4: st.page_link("pages/5_ContributorProfiles.py", label="Contributors", icon="👥")
with c5: st.page_link("pages/3_Info.py", label="About Us", icon="ℹ️")

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.contributor_aggregator import ContributorAggregator
from lib.schemas import ContributorProfile, TimeBasedMetrics


def plot_impact_distribution(metrics: TimeBasedMetrics, title: str):
    """Create stacked bar chart for impact distribution."""

    dist = metrics.impact_distribution

    # Create stacked bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='High Impact',
        x=['Commits'],
        y=[dist.high_impact_count],
        text=[f"{dist.high_impact_count} ({dist.high_impact_percentage:.1f}%)"],
        textposition='inside',
        marker_color='#2ecc71',
        hovertemplate='<b>High Impact</b><br>Count: %{y}<br>Percentage: ' +
                      f'{dist.high_impact_percentage:.1f}%<extra></extra>'
    ))

    fig.add_trace(go.Bar(
        name='Medium Impact',
        x=['Commits'],
        y=[dist.medium_impact_count],
        text=[f"{dist.medium_impact_count} ({dist.medium_impact_percentage:.1f}%)"],
        textposition='inside',
        marker_color='#3498db',
        hovertemplate='<b>Medium Impact</b><br>Count: %{y}<br>Percentage: ' +
                      f'{dist.medium_impact_percentage:.1f}%<extra></extra>'
    ))

    fig.add_trace(go.Bar(
        name='Low Impact',
        x=['Commits'],
        y=[dist.low_impact_count],
        text=[f"{dist.low_impact_count} ({dist.low_impact_percentage:.1f}%)"],
        textposition='inside',
        marker_color='#f39c12',
        hovertemplate='<b>Low Impact</b><br>Count: %{y}<br>Percentage: ' +
                      f'{dist.low_impact_percentage:.1f}%<extra></extra>'
    ))

    fig.add_trace(go.Bar(
        name='Trivial',
        x=['Commits'],
        y=[dist.trivial_count],
        text=[f"{dist.trivial_count} ({dist.trivial_percentage:.1f}%)"],
        textposition='inside',
        marker_color='#95a5a6',
        hovertemplate='<b>Trivial</b><br>Count: %{y}<br>Percentage: ' +
                      f'{dist.trivial_percentage:.1f}%<extra></extra>'
    ))

    fig.update_layout(
        barmode='stack',
        title=title,
        showlegend=True,
        height=300,
        xaxis_title="",
        yaxis_title="Number of Commits"
    )

    return fig


def plot_dimension_radar(metrics: TimeBasedMetrics, contributor_name: str):
    """Create radar chart for dimension quality percentages."""

    categories = []
    percentages = []

    for dim_dist in metrics.dimension_distributions:
        # Format dimension name
        name = dim_dist.dimension_name.replace('_', ' ').title()
        categories.append(name)
        percentages.append(dim_dist.high_quality_percentage)

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=percentages,
        theta=categories,
        fill='toself',
        name=contributor_name,
        line_color='#3498db'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        title="High-Quality Commits by Dimension (%)",
        height=400
    )

    return fig


def display_contributor_card(profile: ContributorProfile, selected_period: str):
    """Display comprehensive contributor profile card."""

    # Select time period
    period_map = {
        "All Time": profile.all_time,
        "Last Year": profile.last_year,
        "Last Month": profile.last_month,
        "Last Week": profile.last_week
    }

    metrics = period_map.get(selected_period)

    if metrics is None:
        st.warning(f"No data available for {selected_period}")
        return

    # Header
    st.markdown(f"### 👤 {profile.author_name}")
    st.caption(f"📧 {profile.email} • 📅 Active for {profile.days_active} days")

    st.divider()

    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Commits",
            metrics.impact_distribution.total_commits,
            help="Total commits in selected period"
        )

    with col2:
        st.metric(
            "High Impact",
            f"{metrics.impact_distribution.high_impact_count} " +
            f"({metrics.impact_distribution.high_impact_percentage:.1f}%)",
            help="Commits with average score >= 4.0"
        )

    with col3:
        st.metric(
            "Lines Changed",
            f"+{metrics.total_lines_added:,} -{metrics.total_lines_removed:,}",
            help="Lines added and removed"
        )

    with col4:
        st.metric(
            "Files Touched",
            f"{metrics.total_files_changed:,}",
            help="Total files changed"
        )

    st.divider()

    # Charts Row
    col1, col2 = st.columns(2)

    with col1:
        # Impact distribution
        fig_impact = plot_impact_distribution(metrics, f"Impact Distribution ({selected_period})")
        st.plotly_chart(fig_impact, use_container_width=True)

    with col2:
        # Dimension radar
        fig_radar = plot_dimension_radar(metrics, profile.author_name)
        st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()

    # Peak Contributions
    if metrics.top_3_commits:
        st.markdown(f"#### 🏆 Top 3 Contributions ({selected_period})")

        for i, peak in enumerate(metrics.top_3_commits, 1):
            with st.expander(
                f"#{i} • {peak.commit_hash[:8]} • Score: {peak.overall_score:.2f} • {peak.message[:60]}",
                expanded=False
            ):
                st.markdown(f"**Impact:** {peak.impact_summary}")
                st.caption(f"📅 {peak.timestamp[:10]}")

                # Show dimension breakdown
                cols = st.columns(3)
                for idx, (dim_name, score) in enumerate(peak.dimension_scores.items()):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        display_name = dim_name.replace('_', ' ').title()
                        st.metric(display_name, f"{'⭐' * score} ({score}/5)")

    st.divider()

    # Category Breakdown
    if profile.category_counts:
        st.markdown("#### 🏷️ Contribution Categories")

        # Sort categories by count
        sorted_categories = sorted(
            profile.category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Display as columns
        num_cols = min(4, len(sorted_categories))
        cols = st.columns(num_cols)

        for idx, (category, count) in enumerate(sorted_categories[:8]):
            col_idx = idx % num_cols
            with cols[col_idx]:
                st.metric(category.replace('_', ' ').title(), count)


def main():
    """Main Streamlit app."""

    st.title("👥 Contributor Profile Analytics")
    st.markdown("Distribution-based impact metrics for code contributors")

    # Check if we have evaluated commits
    if 'evaluated_commits' not in st.session_state or not st.session_state.evaluated_commits:
        st.warning("⚠️ No commit data available. Please analyze commits first.")
        st.page_link("pages/4_CommitAnalysis.py", label="Go to Commit Analysis", icon="🔍")
        return

    st.divider()

    # Build contributor profiles
    with st.spinner("Building contributor profiles..."):
        aggregator = ContributorAggregator(st.session_state.evaluated_commits)
        profiles = aggregator.build_profiles()

    if not profiles:
        st.info("No contributor profiles found.")
        return

    # Summary metrics
    st.subheader("📊 Repository Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Contributors", len(profiles))

    with col2:
        total_commits = sum(p.total_commits for p in profiles)
        st.metric("Total Commits", total_commits)

    with col3:
        total_high_impact = sum(
            p.all_time.impact_distribution.high_impact_count
            for p in profiles
        )
        st.metric("High Impact Commits", total_high_impact)

    with col4:
        total_lines = sum(
            p.all_time.total_lines_added + p.all_time.total_lines_removed
            for p in profiles
        )
        st.metric("Total Lines Changed", f"{total_lines:,}")

    st.divider()

    # Time period selector
    st.subheader("🔍 Contributor Profiles")

    col1, col2 = st.columns([1, 3])

    with col1:
        time_period = st.selectbox(
            "Time Period",
            ["All Time", "Last Year", "Last Month", "Last Week"],
            help="Filter metrics by time period"
        )

    st.divider()

    # Display profiles
    for profile in profiles:
        with st.container():
            display_contributor_card(profile, time_period)
            st.markdown("---")


if __name__ == "__main__":
    main()
```

---

### 5. Implementation Roadmap

#### Phase 1: Core Infrastructure (Week 1)
**Goal**: Establish data models and aggregation logic

**Tasks**:
1. ✅ Add new schemas to `lib/schemas.py`
   - `ImpactDistribution`
   - `DimensionDistribution`
   - `PeakContribution`
   - `TimeBasedMetrics`
   - `ContributorProfile`
   - Add `get_impact_level()` and `is_trivial()` methods to `CommitEvaluation`

2. ✅ Create `lib/contributor_aggregator.py`
   - Implement `ContributorAggregator` class
   - Write unit tests for aggregation logic
   - Test with sample data

3. ✅ Add `email` field to `CommitMetadata` and `CommitEvaluation`
   - Update `lib/git_handler.py` to extract email
   - Update `lib/ai_evaluator.py` to include email in evaluations

**Validation Criteria**:
- Unit tests pass for all aggregation functions
- Manual testing with sample commits produces correct distributions
- No breaking changes to existing commit analysis page

---

#### Phase 2: Data Persistence (Week 2)
**Goal**: Enable saving and loading of evaluations

**Tasks**:
1. ✅ Choose storage approach (SQLite recommended)
   - Create `lib/storage.py`
   - Implement `CommitDatabase` class
   - Add migration support for schema changes

2. ✅ Integrate persistence into commit analysis page
   - Modify `pages/4_CommitAnalysis.py` to save evaluations
   - Load existing evaluations on page load
   - Add "Clear Data" button for testing

3. ✅ Add repository metadata tracking
   - Store repo URL, clone date, last update
   - Enable multi-repository support

**Validation Criteria**:
- Evaluations persist across page refreshes
- Database queries are performant (<100ms for typical queries)
- Proper error handling for database operations

---

#### Phase 3: Contributor Profile UI (Week 3)
**Goal**: Build comprehensive contributor profile page

**Tasks**:
1. ✅ Create `pages/5_ContributorProfiles.py`
   - Basic page layout with navigation
   - Profile card component
   - Time period selector

2. ✅ Implement visualizations
   - Impact distribution stacked bar chart
   - Dimension quality radar chart
   - Peak contributions list
   - Category breakdown

3. ✅ Add interactivity
   - Sort contributors by different metrics
   - Filter by commit type/category
   - Search by contributor name

**Validation Criteria**:
- All charts render correctly
- Time period filtering works
- UI is responsive and performs well with 50+ contributors

---

#### Phase 4: Advanced Features (Week 4)
**Goal**: Polish and enhance analytics capabilities

**Tasks**:
1. ✅ Comparative analytics
   - Compare two contributors side-by-side
   - Team composition analysis
   - Trend analysis over time

2. ✅ Export functionality
   - Export profile to PDF
   - Export data to CSV
   - Share profile links

3. ✅ Advanced filters
   - Filter by file types
   - Filter by commit size
   - Filter by specific date ranges

**Validation Criteria**:
- Comparison view is intuitive
- Export functions work reliably
- Filters combine correctly

---

### 6. Testing Strategy

#### Unit Tests
```python
# tests/test_contributor_aggregator.py

import pytest
from datetime import datetime, timedelta
from lib.contributor_aggregator import ContributorAggregator
from lib.schemas import CommitEvaluation


def create_test_commit(
    author: str,
    scores: dict,
    timestamp: datetime = None
) -> CommitEvaluation:
    """Helper to create test commits."""
    if timestamp is None:
        timestamp = datetime.now()

    return CommitEvaluation(
        commit_hash=f"abc{hash(author + str(timestamp))}",
        author=author,
        timestamp=timestamp.isoformat(),
        message="Test commit",
        **scores,
        categories=["test"],
        impact_summary="Test impact",
        key_files=["test.py"],
        reasoning="Test reasoning",
        lines_added=10,
        lines_removed=5,
        files_changed=1
    )


def test_impact_distribution_high():
    """Test that high-impact commits are categorized correctly."""
    commits = [
        create_test_commit("Alice", {
            "technical_complexity": 5,
            "scope_of_impact": 5,
            "code_quality_delta": 4,
            "risk_criticality": 4,
            "knowledge_sharing": 4,
            "innovation": 5
        })  # avg = 4.5 (high)
    ]

    aggregator = ContributorAggregator(commits)
    profiles = aggregator.build_profiles()

    assert len(profiles) == 1
    assert profiles[0].all_time.impact_distribution.high_impact_count == 1
    assert profiles[0].all_time.impact_distribution.high_impact_percentage == 100.0


def test_impact_distribution_trivial():
    """Test that trivial commits are separated."""
    commits = [
        create_test_commit("Bob", {
            "technical_complexity": 1,
            "scope_of_impact": 1,
            "code_quality_delta": 1,
            "risk_criticality": 1,
            "knowledge_sharing": 1,
            "innovation": 1
        })  # avg = 1.0 (trivial)
    ]

    aggregator = ContributorAggregator(commits)
    profiles = aggregator.build_profiles()

    assert profiles[0].all_time.impact_distribution.trivial_count == 1
    assert profiles[0].all_time.impact_distribution.trivial_percentage == 100.0


def test_time_period_filtering():
    """Test that time periods are calculated correctly."""
    now = datetime.now()
    last_week = now - timedelta(days=5)
    last_month = now - timedelta(days=20)
    last_year = now - timedelta(days=200)

    commits = [
        create_test_commit("Charlie", {"technical_complexity": 4, "scope_of_impact": 4,
                                       "code_quality_delta": 4, "risk_criticality": 4,
                                       "knowledge_sharing": 4, "innovation": 4}, last_week),
        create_test_commit("Charlie", {"technical_complexity": 3, "scope_of_impact": 3,
                                       "code_quality_delta": 3, "risk_criticality": 3,
                                       "knowledge_sharing": 3, "innovation": 3}, last_month),
        create_test_commit("Charlie", {"technical_complexity": 2, "scope_of_impact": 2,
                                       "code_quality_delta": 2, "risk_criticality": 2,
                                       "knowledge_sharing": 2, "innovation": 2}, last_year)
    ]

    aggregator = ContributorAggregator(commits)
    profiles = aggregator.build_profiles()

    profile = profiles[0]

    assert profile.all_time.impact_distribution.total_commits == 3
    assert profile.last_week.impact_distribution.total_commits == 1
    assert profile.last_month.impact_distribution.total_commits == 2
    assert profile.last_year.impact_distribution.total_commits == 3


def test_dimension_distribution():
    """Test dimension-specific distributions."""
    commits = [
        create_test_commit("Diana", {
            "technical_complexity": 5,
            "scope_of_impact": 3,
            "code_quality_delta": 4,
            "risk_criticality": 2,
            "knowledge_sharing": 5,
            "innovation": 1
        })
    ]

    aggregator = ContributorAggregator(commits)
    profiles = aggregator.build_profiles()

    profile = profiles[0]

    # Find technical_complexity distribution
    tech_dist = next(
        d for d in profile.all_time.dimension_distributions
        if d.dimension_name == "technical_complexity"
    )

    assert tech_dist.score_5_count == 1
    assert tech_dist.high_quality_count == 1
    assert tech_dist.high_quality_percentage == 100.0


def test_peak_contributions():
    """Test that top commits are identified correctly."""
    commits = [
        create_test_commit("Eve", {
            "technical_complexity": 5, "scope_of_impact": 5,
            "code_quality_delta": 5, "risk_criticality": 5,
            "knowledge_sharing": 5, "innovation": 5
        }),  # avg = 5.0
        create_test_commit("Eve", {
            "technical_complexity": 3, "scope_of_impact": 3,
            "code_quality_delta": 3, "risk_criticality": 3,
            "knowledge_sharing": 3, "innovation": 3
        }),  # avg = 3.0
        create_test_commit("Eve", {
            "technical_complexity": 4, "scope_of_impact": 4,
            "code_quality_delta": 4, "risk_criticality": 4,
            "knowledge_sharing": 4, "innovation": 4
        })  # avg = 4.0
    ]

    aggregator = ContributorAggregator(commits)
    profiles = aggregator.build_profiles()

    profile = profiles[0]
    top_commits = profile.all_time.top_3_commits

    assert len(top_commits) == 3
    assert top_commits[0].overall_score == 5.0
    assert top_commits[1].overall_score == 4.0
    assert top_commits[2].overall_score == 3.0
```

---

### 7. Impact Level Definitions

**Clear thresholds for commit categorization:**

| Level | Average Score | Description | Examples |
|-------|---------------|-------------|----------|
| **High Impact** | >= 4.0 | Significant, complex, or critical contributions | Major feature launches, architecture refactors, security fixes |
| **Medium Impact** | 2.5 - 3.9 | Standard feature work and bug fixes | New API endpoints, UI components, bug fixes |
| **Low Impact** | 1.5 - 2.4 | Minor improvements and small fixes | Documentation updates, minor refactors, small tweaks |
| **Trivial** | < 1.5 | Routine maintenance | Typo fixes, whitespace changes, config updates |

**Why these thresholds?**
- Separates truly impactful work from routine maintenance
- Allows recognition of both high-volume and high-quality contributors
- Trivial commits don't penalize active contributors
- Medium/low distinction captures "solid contributor" tier

---

### 8. Key Metrics Explained

#### Primary Metrics
1. **High Impact Count**: Absolute number of high-impact commits
   - *Rewards consistent high performers*
   - *Primary sort metric for contributor list*

2. **High Impact Percentage**: % of commits that are high-impact
   - *Rewards quality-focused developers*
   - *Balances volume-based metrics*

3. **Dimension Quality Percentages**: % of commits with score >= 4 per dimension
   - *Shows specific strengths (e.g., "90% high quality in innovation")*
   - *Enables role-based comparisons (architects vs maintainers)*

#### Secondary Metrics
4. **Total Commits**: Volume indicator
5. **Lines Changed**: Code ownership proxy
6. **Files Touched**: Breadth of involvement
7. **Category Distribution**: Type of work breakdown

#### Comparative Fairness Examples

**Scenario 1: High-volume contributor**
- Alice: 100 commits, 30 high-impact (30%), 40 medium, 20 low, 10 trivial
- Bob: 10 commits, 8 high-impact (80%), 2 medium

**Old system (averages)**: Bob looks better (avg 4.2 vs Alice 3.1)
**New system**:
- Alice gets credit for 30 high-impact commits (volume)
- Bob gets credit for 80% high-impact rate (quality)
- Both are valuable, different roles

---

### 9. Migration Checklist

**Pre-launch:**
- [ ] Add email field to CommitMetadata extraction
- [ ] Implement all new schemas in lib/schemas.py
- [ ] Create ContributorAggregator with tests
- [ ] Set up storage layer (SQLite or JSON)
- [ ] Modify CommitAnalysis page to save evaluations
- [ ] Create ContributorProfiles page
- [ ] Test with sample repositories (small, medium, large)

**Launch:**
- [ ] Deploy new page to production
- [ ] Add navigation link to contributor profiles
- [ ] Update documentation

**Post-launch:**
- [ ] Gather user feedback
- [ ] Add requested filters/comparisons
- [ ] Optimize performance for large repositories
- [ ] Consider adding export features

---

### 10. Performance Considerations

**Scalability Targets:**
- 1,000 commits: < 1 second aggregation
- 10,000 commits: < 5 seconds aggregation
- 100,000 commits: < 30 seconds aggregation

**Optimization Strategies:**
1. **Caching**: Cache profiles in session state after first build
2. **Lazy Loading**: Only compute time periods when selected
3. **Indexing**: Database indexes on author and timestamp
4. **Pagination**: For repositories with 100+ contributors
5. **Background Jobs**: Pre-compute profiles for large repos

**Database Query Optimization:**
```sql
-- Fast author lookup
CREATE INDEX idx_author ON commits(author);

-- Fast time-range queries
CREATE INDEX idx_timestamp ON commits(timestamp);

-- Composite index for author + time
CREATE INDEX idx_author_time ON commits(author, timestamp);
```

---

### 11. Future Enhancements

**Phase 5+: Advanced Analytics**
1. **Team Composition Analysis**
   - Identify skill gaps (low percentages in certain dimensions)
   - Suggest code review pairings based on complementary strengths

2. **Trend Analysis**
   - Show contributor growth/decline over time
   - Identify burnout risks (decreasing quality percentages)

3. **Collaboration Metrics**
   - Co-authorship networks
   - Code review impact (if available from commits)

4. **Predictive Analytics**
   - Estimate time to complete features based on historical impact
   - Identify high-risk commits (low knowledge_sharing + high risk_criticality)

5. **Gamification**
   - Badges for milestones (100 high-impact commits, etc.)
   - Leaderboards with privacy controls

---

### 12. Success Metrics

**How to measure if the new system is working:**

1. **Fairness**: No single metric dominates contributor rankings
2. **Clarity**: Users can explain why contributor X ranks higher than Y
3. **Actionability**: Teams use the data to make decisions (promotions, assignments)
4. **Adoption**: Contributors check their profiles regularly
5. **Retention**: Profiles load in <2 seconds for typical repos

**User Feedback Questions:**
- "Do these profiles fairly represent your contributions?"
- "Can you identify areas for improvement from your profile?"
- "Do the distributions make sense compared to averages?"

---

## Conclusion

This transition plan provides a comprehensive roadmap from your current commit-level MVP to a sophisticated contributor analytics system. The distribution-based approach fairly represents both high-volume and high-quality contributors while avoiding the pitfalls of simple averaging.

**Key Benefits:**
✅ Fair to both frequent committers and quality-focused developers
✅ Trivial commits separated, not penalized
✅ Time-based comparisons enable trend analysis
✅ Multiple facets show complete contributor picture
✅ Peak contributions highlighted
✅ Extensible architecture for future enhancements

**Next Steps:**
1. Review and approve this plan
2. Begin Phase 1 implementation (data models)
3. Iterate with user feedback
4. Expand to advanced analytics

Good luck with the implementation! 🚀
