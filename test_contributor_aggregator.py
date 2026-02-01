"""
Simple test script for contributor aggregator functionality.

Run with: python test_contributor_aggregator.py
"""

from datetime import datetime, timedelta
from lib.schemas import CommitEvaluation
from lib.contributor_aggregator import ContributorAggregator


def create_test_commit(
    author: str,
    email: str,
    scores: dict,
    timestamp: datetime = None,
    message: str = "Test commit"
) -> CommitEvaluation:
    """Helper to create test commits."""
    if timestamp is None:
        timestamp = datetime.now()

    return CommitEvaluation(
        commit_hash=f"abc{hash(author + str(timestamp))}",
        author=author,
        email=email,
        timestamp=timestamp.isoformat(),
        message=message,
        **scores,
        categories=["test"],
        impact_summary="Test impact",
        key_files=["test.py"],
        reasoning="Test reasoning",
        lines_added=10,
        lines_removed=5,
        files_changed=1
    )


def test_impact_levels():
    """Test impact level categorization."""
    print("Testing impact level categorization...")

    # High impact commit (avg = 4.5)
    high = create_test_commit("Alice", "alice@example.com", {
        "technical_complexity": 5,
        "scope_of_impact": 5,
        "code_quality_delta": 4,
        "risk_criticality": 4,
        "knowledge_sharing": 4,
        "innovation": 5
    })
    assert high.get_impact_level() == "high", "High impact classification failed"
    assert high.get_average_score() == 4.5, "High impact score calculation failed"

    # Medium impact commit (avg = 3.0)
    medium = create_test_commit("Bob", "bob@example.com", {
        "technical_complexity": 3,
        "scope_of_impact": 3,
        "code_quality_delta": 3,
        "risk_criticality": 3,
        "knowledge_sharing": 3,
        "innovation": 3
    })
    assert medium.get_impact_level() == "medium", "Medium impact classification failed"
    assert medium.get_average_score() == 3.0, "Medium impact score calculation failed"

    # Low impact commit (avg = 2.0)
    low = create_test_commit("Charlie", "charlie@example.com", {
        "technical_complexity": 2,
        "scope_of_impact": 2,
        "code_quality_delta": 2,
        "risk_criticality": 2,
        "knowledge_sharing": 2,
        "innovation": 2
    })
    assert low.get_impact_level() == "low", "Low impact classification failed"
    assert low.get_average_score() == 2.0, "Low impact score calculation failed"

    # Trivial commit (avg = 1.0)
    trivial = create_test_commit("Diana", "diana@example.com", {
        "technical_complexity": 1,
        "scope_of_impact": 1,
        "code_quality_delta": 1,
        "risk_criticality": 1,
        "knowledge_sharing": 1,
        "innovation": 1
    })
    assert trivial.get_impact_level() == "trivial", "Trivial impact classification failed"
    assert trivial.is_trivial(), "Trivial check failed"
    assert trivial.get_average_score() == 1.0, "Trivial impact score calculation failed"

    print("✓ Impact level tests passed!")


def test_single_contributor_profile():
    """Test profile generation for a single contributor."""
    print("\nTesting single contributor profile...")

    commits = [
        # High impact
        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 5, "scope_of_impact": 5,
            "code_quality_delta": 4, "risk_criticality": 4,
            "knowledge_sharing": 4, "innovation": 5
        }, message="Major feature"),

        # Medium impact
        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 3, "scope_of_impact": 3,
            "code_quality_delta": 3, "risk_criticality": 3,
            "knowledge_sharing": 3, "innovation": 3
        }, message="Bug fix"),

        # Trivial
        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 1, "scope_of_impact": 1,
            "code_quality_delta": 1, "risk_criticality": 1,
            "knowledge_sharing": 1, "innovation": 1
        }, message="Typo fix")
    ]

    aggregator = ContributorAggregator(commits)
    profiles = aggregator.build_profiles()

    assert len(profiles) == 1, "Should have 1 profile"

    profile = profiles[0]
    assert profile.author_name == "Alice", "Author name mismatch"
    assert profile.email == "alice@example.com", "Email mismatch"
    assert profile.total_commits == 3, "Total commits mismatch"

    # Check impact distribution
    dist = profile.all_time.impact_distribution
    assert dist.high_impact_count == 1, "High impact count wrong"
    assert dist.medium_impact_count == 1, "Medium impact count wrong"
    assert dist.trivial_count == 1, "Trivial count wrong"
    assert dist.total_commits == 3, "Total in distribution wrong"

    # Check percentages
    assert abs(dist.high_impact_percentage - 33.33) < 0.1, "High impact % wrong"
    assert abs(dist.medium_impact_percentage - 33.33) < 0.1, "Medium impact % wrong"
    assert abs(dist.trivial_percentage - 33.33) < 0.1, "Trivial % wrong"

    print("✓ Single contributor profile tests passed!")


def test_multiple_contributors():
    """Test profile generation for multiple contributors."""
    print("\nTesting multiple contributors...")

    now = datetime.now()

    commits = [
        # Alice - 2 high impact commits
        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 5, "scope_of_impact": 5,
            "code_quality_delta": 4, "risk_criticality": 4,
            "knowledge_sharing": 4, "innovation": 5
        }, now),
        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 4, "scope_of_impact": 4,
            "code_quality_delta": 4, "risk_criticality": 5,
            "knowledge_sharing": 4, "innovation": 4
        }, now - timedelta(days=1)),

        # Bob - 1 high impact, 2 medium
        create_test_commit("Bob", "bob@example.com", {
            "technical_complexity": 5, "scope_of_impact": 5,
            "code_quality_delta": 5, "risk_criticality": 5,
            "knowledge_sharing": 5, "innovation": 5
        }, now),
        create_test_commit("Bob", "bob@example.com", {
            "technical_complexity": 3, "scope_of_impact": 3,
            "code_quality_delta": 3, "risk_criticality": 3,
            "knowledge_sharing": 3, "innovation": 3
        }, now - timedelta(days=1)),
        create_test_commit("Bob", "bob@example.com", {
            "technical_complexity": 3, "scope_of_impact": 3,
            "code_quality_delta": 3, "risk_criticality": 3,
            "knowledge_sharing": 3, "innovation": 3
        }, now - timedelta(days=2))
    ]

    aggregator = ContributorAggregator(commits)
    profiles = aggregator.build_profiles()

    assert len(profiles) == 2, "Should have 2 profiles"

    # Profiles should be sorted by high-impact count
    # Alice has 2 high-impact, Bob has 1, so Alice should be first
    assert profiles[0].author_name == "Alice", "Sorting by high-impact failed"
    assert profiles[1].author_name == "Bob", "Sorting by high-impact failed"

    # Check Alice
    alice = profiles[0]
    assert alice.total_commits == 2, "Alice commit count wrong"
    assert alice.all_time.impact_distribution.high_impact_count == 2, "Alice high impact wrong"

    # Check Bob
    bob = profiles[1]
    assert bob.total_commits == 3, "Bob commit count wrong"
    assert bob.all_time.impact_distribution.high_impact_count == 1, "Bob high impact wrong"
    assert bob.all_time.impact_distribution.medium_impact_count == 2, "Bob medium impact wrong"

    print("✓ Multiple contributors tests passed!")


def test_time_periods():
    """Test time period filtering."""
    print("\nTesting time period filtering...")

    now = datetime.now()

    commits = [
        # Recent (within last week)
        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 5, "scope_of_impact": 5,
            "code_quality_delta": 4, "risk_criticality": 4,
            "knowledge_sharing": 4, "innovation": 5
        }, now - timedelta(days=3)),

        # Within last month
        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 4, "scope_of_impact": 4,
            "code_quality_delta": 4, "risk_criticality": 4,
            "knowledge_sharing": 4, "innovation": 4
        }, now - timedelta(days=20)),

        # Within last year
        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 3, "scope_of_impact": 3,
            "code_quality_delta": 3, "risk_criticality": 3,
            "knowledge_sharing": 3, "innovation": 3
        }, now - timedelta(days=200))
    ]

    aggregator = ContributorAggregator(commits)
    profiles = aggregator.build_profiles()

    profile = profiles[0]

    # All time should have 3 commits
    assert profile.all_time.impact_distribution.total_commits == 3, "All time count wrong"

    # Last year should have 3 commits
    if profile.last_year:
        assert profile.last_year.impact_distribution.total_commits == 3, "Last year count wrong"

    # Last month should have 2 commits
    if profile.last_month:
        assert profile.last_month.impact_distribution.total_commits == 2, "Last month count wrong"

    # Last week should have 1 commit
    if profile.last_week:
        assert profile.last_week.impact_distribution.total_commits == 1, "Last week count wrong"

    print("✓ Time period tests passed!")


def test_dimension_distributions():
    """Test dimension-specific distributions."""
    print("\nTesting dimension distributions...")

    commits = [
        create_test_commit("Alice", "alice@example.com", {
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
    dim_dists = profile.all_time.dimension_distributions

    assert len(dim_dists) == 6, "Should have 6 dimension distributions"

    # Find technical_complexity distribution
    tech_dist = next(d for d in dim_dists if d.dimension_name == "technical_complexity")
    assert tech_dist.score_5_count == 1, "Tech complexity score 5 count wrong"
    assert tech_dist.high_quality_count == 1, "Tech complexity high quality count wrong"
    assert tech_dist.high_quality_percentage == 100.0, "Tech complexity high quality % wrong"

    # Find innovation distribution
    innov_dist = next(d for d in dim_dists if d.dimension_name == "innovation")
    assert innov_dist.score_1_count == 1, "Innovation score 1 count wrong"
    assert innov_dist.high_quality_count == 0, "Innovation high quality count wrong"

    print("✓ Dimension distribution tests passed!")


def test_peak_contributions():
    """Test peak contribution identification."""
    print("\nTesting peak contributions...")

    commits = [
        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 5, "scope_of_impact": 5,
            "code_quality_delta": 5, "risk_criticality": 5,
            "knowledge_sharing": 5, "innovation": 5
        }, message="Amazing feature"),  # avg = 5.0

        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 3, "scope_of_impact": 3,
            "code_quality_delta": 3, "risk_criticality": 3,
            "knowledge_sharing": 3, "innovation": 3
        }, message="Normal work"),  # avg = 3.0

        create_test_commit("Alice", "alice@example.com", {
            "technical_complexity": 4, "scope_of_impact": 4,
            "code_quality_delta": 4, "risk_criticality": 4,
            "knowledge_sharing": 4, "innovation": 4
        }, message="Good work")  # avg = 4.0
    ]

    aggregator = ContributorAggregator(commits)
    profiles = aggregator.build_profiles()

    profile = profiles[0]
    top_commits = profile.all_time.top_3_commits

    assert len(top_commits) == 3, "Should have 3 top commits"

    # Should be sorted by score (descending)
    assert top_commits[0].overall_score == 5.0, "Top commit score wrong"
    assert top_commits[1].overall_score == 4.0, "Second commit score wrong"
    assert top_commits[2].overall_score == 3.0, "Third commit score wrong"

    # Check that message is preserved
    assert "Amazing feature" in top_commits[0].message, "Top commit message wrong"

    print("✓ Peak contribution tests passed!")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running Contributor Aggregator Tests")
    print("=" * 60)

    try:
        test_impact_levels()
        test_single_contributor_profile()
        test_multiple_contributors()
        test_time_periods()
        test_dimension_distributions()
        test_peak_contributions()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe contributor aggregator implementation is working correctly.")
        print("You can now test the Streamlit app with real data.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
