"""
Aggregate commit evaluations into contributor profiles.

Builds distribution-based metrics from individual commit evaluations.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
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
        email = commits[0].email if commits[0].email else ""

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
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            commits = [
                c for c in all_commits
                if datetime.fromisoformat(c.timestamp.replace('Z', '+00:00')) >= cutoff
            ]
            start_date = cutoff.isoformat()
            end_date = datetime.now(timezone.utc).isoformat()

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
