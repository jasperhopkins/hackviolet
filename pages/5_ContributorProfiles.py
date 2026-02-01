"""
Contributor Profile Analytics - Streamlit Page

Analyze individual contributors by evaluating all their commits.
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

# ===================== NAV =====================
st.markdown("""
<style>
.nav-wrap { display:flex; justify-content:center; gap:14px; margin:18px 0 24px; }
.nav-wrap .stButton>button{
  background:rgba(255,255,255,0.12);
  color:#FFFFFF;
  border:1px solid rgba(255,255,255,0.25);
  border-radius:18px;
  padding:10px 22px;
  font-weight:700;
  font-size:16px;
  box-shadow:0 3px 6px rgba(0,0,0,.15);
  transition:.15s ease;
}
.nav-wrap .stButton>button:hover{
  background:rgba(255,255,255,0.18);
  transform:translateY(-2px);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nav-wrap">', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1], gap="small")
with c1:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("1_Home.py")
with c2:
    if st.button("🎥 Demo", use_container_width=True):
        st.switch_page("pages/2_DemoVideo.py")
with c3:
    if st.button("🔍 CodeOrigin", use_container_width=True):
        st.switch_page("pages/4_CommitAnalysis.py")
with c4:
    if st.button("👥 Contributors", use_container_width=True):
        st.switch_page("pages/5_ContributorProfiles.py")
with c5:
    if st.button("ℹ️ About Us", use_container_width=True):
        st.switch_page("pages/3_Info.py")
st.markdown('</div>', unsafe_allow_html=True)
# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.contributor_aggregator import ContributorAggregator
from lib.schemas import ContributorProfile, TimeBasedMetrics
from lib.ai_evaluator import AIEvaluator


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
    st.markdown("Analyze individual contributors by evaluating all their commits")

    # Initialize session state
    if 'repo_url' not in st.session_state:
        st.session_state.repo_url = ""
    if 'total_commits' not in st.session_state:
        st.session_state.total_commits = 0

    # Repository input section
    st.subheader("📦 Repository")

    col1, col2 = st.columns([3, 1])

    with col1:
        repo_url = st.text_input(
            "Git Repository URL",
            value=st.session_state.repo_url,
            placeholder="https://github.com/user/repo.git or git@github.com:user/repo.git",
            help="Enter a public repository URL (HTTPS or SSH) - synced across pages",
            key="contributor_repo_url"
        )
        # Update session state when changed
        if repo_url != st.session_state.repo_url:
            st.session_state.repo_url = repo_url

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        clone_clicked = st.button("🔄 Clone Repository", type="primary", use_container_width=True)

    # Clone button logic
    if clone_clicked:
        if not repo_url:
            st.error("Please enter a repository URL")
        else:
            try:
                from lib.git_handler import GitHandler

                with st.spinner("Cloning repository..."):
                    # Create new handler
                    handler = GitHandler()
                    handler.clone_repository(repo_url)

                    # Store in session state
                    st.session_state.git_handler = handler
                    st.session_state.repo_url = repo_url
                    st.session_state.total_commits = handler.get_total_commits()

                st.success(f"✓ Cloned successfully! Total commits: {st.session_state.total_commits}")
                st.rerun()

            except Exception as e:
                st.error(f"Failed to clone repository: {str(e)}")

    st.divider()

    # Check if git handler is available
    if 'git_handler' not in st.session_state or st.session_state.git_handler is None:
        st.warning("⚠️ No repository loaded. Please clone a repository above or use the Commit Analysis page.")
        st.page_link("pages/4_CommitAnalysis.py", label="Go to Commit Analysis", icon="🔍")
        return

    git_handler = st.session_state.git_handler

    # Display repository info if cloned
    if st.session_state.total_commits > 0:
        st.info(f"📊 Repository: **{st.session_state.repo_url}** • Total commits: **{st.session_state.total_commits}**")

    st.divider()

    # Get all contributors
    try:
        with st.spinner("Loading contributors..."):
            contributors = git_handler.get_all_contributors()
    except Exception as e:
        st.error(f"Error loading contributors: {e}")

        # If repository is invalid, offer to re-clone
        if "no longer exists" in str(e).lower() or "does not exist" in str(e).lower():
            st.warning("The repository needs to be re-cloned. Please clone it again using the form above.")
            # Clear the invalid handler
            st.session_state.git_handler = None

        return

    if not contributors:
        st.info("No contributors found in the repository.")
        return

    # Display contributor selection
    st.subheader("📊 Select a Contributor to Analyze")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Create contributor options with commit count
        contributor_options = [
            f"{c['name']} ({c['email']}) - {c['commit_count']} commits"
            for c in contributors
        ]

        selected_index = st.selectbox(
            "Choose a contributor",
            range(len(contributor_options)),
            format_func=lambda i: contributor_options[i],
            help="Select a contributor to analyze all their commits"
        )

        selected_contributor = contributors[selected_index]

    with col2:
        st.metric("Total Contributors", len(contributors))

    st.divider()

    # Show selected contributor info
    st.markdown(f"### Analyzing: {selected_contributor['name']}")
    st.caption(f"📧 {selected_contributor['email']} • {selected_contributor['commit_count']} commits")

    # Initialize session state for contributor evaluations
    if 'contributor_evaluations' not in st.session_state:
        st.session_state.contributor_evaluations = {}

    contributor_key = f"{selected_contributor['name']}_{selected_contributor['email']}"

    # Check if we already have evaluations for this contributor
    if contributor_key in st.session_state.contributor_evaluations:
        st.success("✅ Evaluations already loaded for this contributor")
        evaluations = st.session_state.contributor_evaluations[contributor_key]
    else:
        # Analyze button
        if st.button("🔍 Analyze All Commits", type="primary", use_container_width=True):
            # Get API key
            if 'api_key' not in st.session_state or not st.session_state.api_key:
                st.error("⚠️ API key not found. Please enter your API key in the Commit Analysis page.")
                st.page_link("pages/4_CommitAnalysis.py", label="Go to Commit Analysis", icon="🔍")
                return

            # Extract all commits by this author
            try:
                with st.spinner(f"Extracting commits by {selected_contributor['name']}..."):
                    commits = git_handler.extract_commits_by_author(
                        selected_contributor['name'],
                        selected_contributor['email']
                    )

                if not commits:
                    st.warning("No commits found for this contributor.")
                    return

                st.info(f"Found {len(commits)} commits. Starting AI evaluation...")

                # Initialize AI evaluator
                evaluator = AIEvaluator(st.session_state.api_key)
                evaluations = []

                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Evaluate each commit
                for i, commit in enumerate(commits):
                    status_text.text(f"Evaluating commit {i+1}/{len(commits)}: {commit.hash[:8]}")

                    # Get diff
                    diff = git_handler.get_commit_diff(commit.hash)

                    # Evaluate
                    evaluation = evaluator.evaluate_commit(commit, diff)
                    evaluations.append(evaluation)

                    # Update progress
                    progress_bar.progress((i + 1) / len(commits))

                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()

                # Store in session state
                st.session_state.contributor_evaluations[contributor_key] = evaluations

                st.success(f"✅ Successfully evaluated {len(evaluations)} commits!")

            except Exception as e:
                st.error(f"Error analyzing commits: {e}")
                return
        else:
            st.info("👆 Click the button above to analyze all commits for this contributor")
            return

    # Build and display profile
    if evaluations:
        st.divider()

        # Time period selector
        col1, col2 = st.columns([1, 3])

        with col1:
            time_period = st.selectbox(
                "Time Period",
                ["All Time", "Last Year", "Last Month", "Last Week"],
                help="Filter metrics by time period"
            )

        st.divider()

        # Build profile
        with st.spinner("Building contributor profile..."):
            aggregator = ContributorAggregator(evaluations)
            profiles = aggregator.build_profiles()

            if profiles:
                display_contributor_card(profiles[0], time_period)


if __name__ == "__main__":
    main()
