"""
Git Commit Attribution Analyzer - Streamlit Page

AI-powered analysis of code contributions across 6 dimensions.
"""

import streamlit as st
import os
import sys

st.set_page_config(page_title="Commit Analysis • CodeOrigin", page_icon="🔍", layout="wide")

c1, c2, c3, c4 = st.columns(4)
with c1: st.page_link("1_Home.py", label="Home", icon="🏠")
with c2: st.page_link("pages/2_DemoVideo.py", label="Demo", icon="🎥")
with c3: st.page_link("pages/4_CommitAnalysis.py", label="CodeOrigin", icon="🔍")
with c4: st.page_link("pages/3_Info.py", label="About Us", icon="👥")


# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.git_handler import GitHandler
from lib.ai_evaluator import AIEvaluator
from lib.schemas import CommitEvaluation

# Page config
st.set_page_config(page_title="Commit Analysis", page_icon="🔍", layout="wide")

# Initialize session state
if 'evaluated_commits' not in st.session_state:
    st.session_state.evaluated_commits = []
if 'current_offset' not in st.session_state:
    st.session_state.current_offset = 0
if 'git_handler' not in st.session_state:
    st.session_state.git_handler = None
if 'repo_url' not in st.session_state:
    st.session_state.repo_url = ""
if 'total_commits' not in st.session_state:
    st.session_state.total_commits = 0


def analyze_commits(handler: GitHandler, offset: int, limit: int, api_key: str):
    """
    Analyze a batch of commits.
    
    Args:
        handler: GitHandler instance
        offset: Number of commits to skip
        limit: Number of commits to analyze
        api_key: Anthropic API key
    """
    try:
        # Extract commit metadata
        commits = handler.extract_commit_metadata(skip=offset, limit=limit)
        
        if not commits:
            st.warning("No more commits to analyze.")
            return
        
        # Create AI evaluator
        evaluator = AIEvaluator(api_key)
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Analyze each commit
        for i, commit in enumerate(commits):
            status_text.text(f"Analyzing commit {i+1}/{len(commits)}: {commit.hash[:8]}...")
            
            # Get diff
            diff = handler.get_commit_diff(commit.hash)
            
            # Evaluate with AI
            evaluation = evaluator.evaluate_commit(commit, diff)
            
            # Add to session state
            st.session_state.evaluated_commits.append(evaluation)
            
            # Update progress
            progress_bar.progress((i + 1) / len(commits))
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        st.success(f"✓ Successfully analyzed {len(commits)} commits!")
        
    except Exception as e:
        st.error(f"Error analyzing commits: {str(e)}")


def display_commit_card(evaluation: CommitEvaluation):
    """
    Display a single commit evaluation card.
    
    Args:
        evaluation: CommitEvaluation object
    """
    # Create expander with commit summary
    with st.expander(
        f"**{evaluation.commit_hash[:8]}** • {evaluation.author} • {evaluation.message[:60]}{'...' if len(evaluation.message) > 60 else ''}",
        expanded=False
    ):
        # Display timestamp and basic info
        st.caption(f"📅 {evaluation.timestamp[:10]} • 📝 {evaluation.files_changed} files • +{evaluation.lines_added} -{evaluation.lines_removed}")
        
        # Display full message if truncated
        if len(evaluation.message) > 60:
            st.markdown(f"**Message:** {evaluation.message}")
        
        st.divider()
        
        # Display dimensions in two columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Dimensions**")
            st.metric("Technical Complexity", f"{'⭐' * evaluation.technical_complexity} ({evaluation.technical_complexity}/5)")
            st.metric("Scope of Impact", f"{'⭐' * evaluation.scope_of_impact} ({evaluation.scope_of_impact}/5)")
            st.metric("Code Quality", f"{'⭐' * evaluation.code_quality_delta} ({evaluation.code_quality_delta}/5)")
        
        with col2:
            st.markdown("**📈 Additional Metrics**")
            st.metric("Risk & Criticality", f"{'⭐' * evaluation.risk_criticality} ({evaluation.risk_criticality}/5)")
            st.metric("Knowledge Sharing", f"{'⭐' * evaluation.knowledge_sharing} ({evaluation.knowledge_sharing}/5)")
            st.metric("Innovation", f"{'⭐' * evaluation.innovation} ({evaluation.innovation}/5)")
        
        st.divider()
        
        # Display categories
        if evaluation.categories:
            st.markdown(f"**🏷️ Categories:** {', '.join(evaluation.categories)}")
        
        # Display impact summary
        st.markdown(f"**💡 Impact:** {evaluation.impact_summary}")
        
        # Display key files
        if evaluation.key_files:
            st.markdown(f"**📂 Key Files:** {', '.join(evaluation.key_files[:5])}")
        
        # Show detailed reasoning in collapsible section
        with st.expander("📋 Show Detailed Reasoning"):
            st.markdown(evaluation.reasoning)


def main():
    """Main Streamlit app."""
    
    # Header
    st.title("🔍 Git Commit Attribution Analyzer")
    st.markdown("AI-powered analysis of code contributions using Claude Sonnet 4.5")
    
    # Get API key from secrets or user input
    api_key = None
    if 'ANTHROPIC_API_KEY' in st.secrets:
        api_key = st.secrets['ANTHROPIC_API_KEY']
    else:
        st.warning("⚠️ No API key found in secrets. Please enter your Anthropic API key below.")
        api_key = st.text_input("Anthropic API Key", type="password", help="Your API key will not be stored")
    
    if not api_key:
        st.info("👆 Please provide an Anthropic API key to continue.")
        return
    
    st.divider()
    
    # Repository input section
    st.subheader("📦 Repository")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        repo_url = st.text_input(
            "Git Repository URL",
            value=st.session_state.repo_url,
            placeholder="https://github.com/user/repo.git or git@github.com:user/repo.git",
            help="Enter a public repository URL (HTTPS or SSH)"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        clone_clicked = st.button("🔄 Clone & Analyze", type="primary", use_container_width=True)
    
    # Clone and analyze button logic
    if clone_clicked:
        if not repo_url:
            st.error("Please enter a repository URL")
        else:
            with st.spinner("Cloning repository..."):
                try:
                    # Create new handler
                    handler = GitHandler()
                    handler.clone_repository(repo_url)
                    
                    # Store in session state
                    st.session_state.git_handler = handler
                    st.session_state.repo_url = repo_url
                    st.session_state.current_offset = 0
                    st.session_state.evaluated_commits = []
                    st.session_state.total_commits = handler.get_total_commits()
                    
                    # Get repo info
                    repo_info = handler.get_repo_info()
                    
                    st.success(f"✓ Cloned successfully! Total commits: {st.session_state.total_commits}")
                    
                    # Automatically analyze first 5 commits
                    with st.spinner("Analyzing first 5 commits..."):
                        analyze_commits(handler, 0, 5, api_key)
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to clone repository: {str(e)}")
    
    # Display repository info if cloned
    if st.session_state.git_handler and st.session_state.total_commits > 0:
        st.info(f"📊 Repository: **{st.session_state.repo_url}** • Total commits: **{st.session_state.total_commits}**")
    
    st.divider()
    
    # Display analyzed commits
    if st.session_state.evaluated_commits:
        st.subheader(f"📊 Commit Analysis ({len(st.session_state.evaluated_commits)} commits analyzed)")
        
        # Display each commit
        for evaluation in st.session_state.evaluated_commits:
            display_commit_card(evaluation)
        
        st.divider()
        
        # Load more button
        if st.session_state.git_handler and len(st.session_state.evaluated_commits) < st.session_state.total_commits:
            remaining = st.session_state.total_commits - len(st.session_state.evaluated_commits)
            next_batch = min(5, remaining)
            
            if st.button(f"➕ Load More Commits ({next_batch} more)", use_container_width=True):
                with st.spinner(f"Analyzing next {next_batch} commits..."):
                    st.session_state.current_offset = len(st.session_state.evaluated_commits)
                    analyze_commits(
                        st.session_state.git_handler,
                        st.session_state.current_offset,
                        next_batch,
                        api_key
                    )
                st.rerun()
        else:
            if st.session_state.git_handler:
                st.success("✅ All commits have been analyzed!")
    
    elif st.session_state.git_handler:
        st.info("👆 Click 'Clone & Analyze' to start analyzing commits")
    else:
        st.info("👆 Enter a repository URL and click 'Clone & Analyze' to get started")


if __name__ == "__main__":
    main()
