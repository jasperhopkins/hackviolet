# MVP Implementation Plan: Git Attribution Analyzer

## Overview
This MVP focuses on delivering a functional Streamlit-based git attribution tool that analyzes commit contributions using Claude Sonnet 4.5. The MVP is intentionally scoped to demonstrate core value with minimal complexity.

## Key Changes from Original Spec
- **Model**: Using Claude Sonnet 4.5 (`claude-sonnet-4-20250514`) instead of Sonnet 4
- **UI Framework**: Streamlit for rapid MVP development
- **Scope**: Single-page app focused on commit history analysis
- **Initial Load**: Last 5 commits, with "Load More" button functionality
- **Future Phase**: Aggregate contributor stats page (deferred)

---

## MVP Scope & Features

### Core Functionality
1. **Input**: Git repository URL (HTTPS or SSH)
2. **Process**: 
   - Clone repository to temporary directory
   - Extract metadata for last 5 commits
   - AI evaluation of each commit across 6 dimensions
   - Display results in Streamlit UI
3. **Interaction**: "Load More Commits" button to analyze next 5 commits
4. **Output**: Clean, readable commit analysis cards

### Out of Scope (Post-MVP)
- Aggregate contributor profiles
- Team comparison views
- Advanced agent exploration with git tools
- Caching and database persistence
- Export to PDF/markdown
- Timeline visualizations

---

## Technical Architecture

### Technology Stack
```
- Python 3.10+
- Streamlit (UI framework)
- GitPython (git operations)
- Anthropic SDK (LLM integration)
- Pydantic (data validation)
```

### Project Structure
```
hackviolet/
├── pages/
│   └── 6_CommitAnalysis.py         # New Streamlit page
├── lib/
│   ├── __init__.py
│   ├── git_handler.py              # Repository cloning & metadata extraction
│   ├── ai_evaluator.py             # LLM commit evaluation
│   └── schemas.py                  # Pydantic models
├── requirements.txt                # Dependencies
└── design_docs/
    ├── git-attribution-project-spec.md
    └── mvp-implementation-plan.md
```

---

## Implementation Steps

### Phase 1: Setup & Infrastructure (1-2 hours)

**1.1 Dependencies**
```bash
pip install streamlit gitpython anthropic pydantic python-dotenv
```

**1.2 Environment Configuration**
- Create `.env` file for Anthropic API key
- Add `.gitignore` entries for temp directories and `.env`
- Set up Streamlit secrets management

**1.3 Project Structure**
- Create `lib/` directory for core logic
- Create `lib/__init__.py`, `lib/git_handler.py`, `lib/ai_evaluator.py`, `lib/schemas.py`

### Phase 2: Data Models (30 minutes)

**2.1 Define Pydantic Schemas** (`lib/schemas.py`)
```python
from pydantic import BaseModel, Field
from typing import List

class CommitMetadata(BaseModel):
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
    # Identity
    commit_hash: str
    author: str
    timestamp: str
    message: str
    
    # 6 core dimensions (1-5 scale)
    technical_complexity: int = Field(ge=1, le=5)
    scope_of_impact: int = Field(ge=1, le=5)
    code_quality_delta: int = Field(ge=1, le=5)
    risk_criticality: int = Field(ge=1, le=5)
    knowledge_sharing: int = Field(ge=1, le=5)
    innovation: int = Field(ge=1, le=5)
    
    # Contextual metadata
    categories: List[str]
    impact_summary: str
    key_files: List[str]
    reasoning: str
    
    # Basic stats
    lines_added: int
    lines_removed: int
    files_changed: int
```

### Phase 3: Git Operations (2-3 hours)

**3.1 Repository Handler** (`lib/git_handler.py`)

Key Functions:
- `clone_repository(git_url: str) -> Repo`
  - Clone to `/tmp/git_analysis_<hash>/`
  - Handle authentication errors gracefully
  - Return GitPython Repo object

- `extract_commit_metadata(repo: Repo, skip: int = 0, limit: int = 5) -> List[CommitMetadata]`
  - Get commits with pagination (skip/limit)
  - Extract author, timestamp, message, file stats
  - Return structured metadata

- `get_commit_diff(repo: Repo, commit_hash: str) -> str`
  - Get unified diff for commit
  - Truncate if > 4000 characters (token management)
  - Return diff string for LLM context

- `cleanup_repository(repo_path: str)`
  - Delete temporary clone directory
  - Handle cleanup errors gracefully

**3.2 Error Handling**
- Invalid git URLs
- Authentication failures (SSH keys, tokens)
- Network errors
- Empty repositories
- Corrupted git history

### Phase 4: AI Evaluation (3-4 hours)

**4.1 LLM Integration** (`lib/ai_evaluator.py`)

Key Functions:
- `evaluate_commit(commit_data: CommitMetadata, diff: str, api_key: str) -> CommitEvaluation`
  - Build prompt with commit context
  - Call Claude Sonnet 4.5 API
  - Parse structured response
  - Return CommitEvaluation object

**4.2 Prompt Engineering**

Template:
```
You are analyzing a code commit to evaluate its contribution across multiple dimensions.

COMMIT INFORMATION:
Hash: {commit_hash}
Author: {author}
Date: {timestamp}
Message: {commit_message}

FILES CHANGED ({file_count}):
{file_list}

DIFF PREVIEW:
{diff_snippet}

TASK: Evaluate this commit across 6 dimensions (1-5 scale):

1. TECHNICAL COMPLEXITY
   How difficult was this change to implement?
   1 = Config/typo fix, 5 = Novel algorithm/complex architecture

2. SCOPE OF IMPACT
   How many systems/components does this affect?
   1 = Single function, 5 = Cross-system architectural change

3. CODE QUALITY DELTA
   Did this improve or degrade code quality?
   1 = Quality degradation, 3 = Neutral, 5 = Major improvement

4. RISK & CRITICALITY
   How critical is this to system reliability/security?
   1 = Low-risk feature, 5 = Security fix/production critical

5. KNOWLEDGE SHARING
   How well documented and tested is this change?
   1 = No docs/tests, 5 = Excellent documentation and test coverage

6. INNOVATION
   How novel or creative is the solution?
   1 = Routine implementation, 5 = Novel approach/creative solution

ADDITIONAL ANALYSIS:
- Categorize the commit (bug_fix, feature, refactor, security, testing, documentation, etc.)
- Summarize the impact in 1-2 sentences
- List the most important files changed
- Provide detailed reasoning for your scores

Respond with a JSON object matching this schema:
{
  "technical_complexity": <1-5>,
  "scope_of_impact": <1-5>,
  "code_quality_delta": <1-5>,
  "risk_criticality": <1-5>,
  "knowledge_sharing": <1-5>,
  "innovation": <1-5>,
  "categories": ["category1", "category2"],
  "impact_summary": "1-2 sentence summary",
  "key_files": ["file1", "file2"],
  "reasoning": "Detailed justification for scores"
}
```

**4.3 Response Parsing**
- Use Anthropic's JSON mode or structured outputs
- Fallback to regex parsing if needed
- Validate against Pydantic schema
- Handle LLM errors/rate limits

**4.4 Cost Management**
- Truncate large diffs (keep first/last sections)
- Limit to ~2000 tokens per commit analysis
- Estimated cost: ~$0.05-0.10 per commit

### Phase 5: Streamlit UI (3-4 hours)

**5.1 Page Layout** (`pages/6_CommitAnalysis.py`)

Structure:
```
┌─────────────────────────────────────────────┐
│  🔍 Git Commit Attribution Analyzer         │
├─────────────────────────────────────────────┤
│  Repository URL: [________________] [Clone] │
│  Status: ✓ Cloned • 1,234 commits total    │
├─────────────────────────────────────────────┤
│  📊 Commit Analysis (Showing 1-5 of 1,234) │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Commit: abc123f                     │   │
│  │ Author: Alice Chen • 2024-12-15    │   │
│  │ Message: Fix race condition...     │   │
│  │                                     │   │
│  │ Dimensions:                         │   │
│  │ Technical Complexity:    ⭐⭐⭐⭐⭐  │   │
│  │ Scope of Impact:         ⭐⭐⭐⭐   │   │
│  │ Code Quality:            ⭐⭐⭐⭐⭐  │   │
│  │ Risk & Criticality:      ⭐⭐⭐⭐⭐  │   │
│  │ Knowledge Sharing:       ⭐⭐⭐     │   │
│  │ Innovation:              ⭐⭐⭐⭐   │   │
│  │                                     │   │
│  │ Categories: bug_fix, security       │   │
│  │ Impact: Fixed critical race...      │   │
│  │ [Show Details ▼]                    │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [...4 more commits...]                    │
│                                             │
│  [Load More Commits (5-10)]                │
└─────────────────────────────────────────────┘
```

**5.2 Streamlit Components**

Key UI Elements:
- `st.text_input()` for repo URL
- `st.button()` for clone action
- `st.session_state` for maintaining state (repo, commits, offset)
- `st.expander()` for commit detail cards
- `st.progress()` for analysis progress
- `st.spinner()` for loading states
- `st.error()` for error messages
- `st.success()` for completion messages

**5.3 State Management**

Session State Variables:
```python
if 'repo_path' not in st.session_state:
    st.session_state.repo_path = None
if 'repo_url' not in st.session_state:
    st.session_state.repo_url = None
if 'evaluated_commits' not in st.session_state:
    st.session_state.evaluated_commits = []
if 'current_offset' not in st.session_state:
    st.session_state.current_offset = 0
if 'total_commits' not in st.session_state:
    st.session_state.total_commits = 0
```

**5.4 User Flow**

1. User enters git URL
2. Click "Clone Repository" button
3. Show progress spinner while cloning
4. Display repository info (total commits, default branch)
5. Automatically analyze first 5 commits
6. Show progress bar during analysis
7. Display commit cards with evaluations
8. "Load More" button appears at bottom
9. Click to analyze next 5 commits
10. New results append to display

**5.5 Streamlit-Specific Design Considerations**

Limitations to Work Around:
- No real-time updates (must trigger rerun)
- Limited layout customization (use columns/expanders)
- Session state persists during session only
- No direct file upload for repos (URL only)

Design Solutions:
- Use `st.columns()` for dimension display (2-3 columns)
- Use `st.expander()` for detailed reasoning
- Use color-coded metrics with `st.metric()` or custom HTML
- Use `st.rerun()` for incremental loading

### Phase 6: Integration & Testing (2-3 hours)

**6.1 Integration**
- Connect git handler → AI evaluator → Streamlit UI
- Test full flow end-to-end
- Handle edge cases (empty repos, large repos, private repos)

**6.2 Test Cases**
- Small repo (< 50 commits): Full analysis
- Medium repo (100-500 commits): Pagination
- Large repo (1000+ commits): Performance
- Private repo: Authentication handling
- Invalid URL: Error handling
- Network failure: Graceful degradation

**6.3 Manual Testing**
- Test with 3-4 different repositories
- Verify LLM evaluations make sense
- Check UI responsiveness
- Validate cost per analysis

---

## Implementation Code Outline

### `lib/git_handler.py`
```python
import os
import tempfile
import shutil
from git import Repo, GitCommandError
from typing import List, Optional
from .schemas import CommitMetadata

class GitHandler:
    def __init__(self):
        self.temp_dir = None
        self.repo = None
    
    def clone_repository(self, git_url: str) -> Repo:
        """Clone repository to temporary directory"""
        # Create temp directory
        # Clone with GitPython
        # Return Repo object
        pass
    
    def extract_commit_metadata(self, skip: int = 0, limit: int = 5) -> List[CommitMetadata]:
        """Extract metadata for commits with pagination"""
        # Use repo.iter_commits() with skip/limit
        # Build CommitMetadata objects
        # Return list
        pass
    
    def get_commit_diff(self, commit_hash: str, max_length: int = 4000) -> str:
        """Get diff for specific commit, truncated if needed"""
        # Get commit object
        # Generate diff
        # Truncate if too long
        # Return diff string
        pass
    
    def get_total_commits(self) -> int:
        """Get total commit count in repository"""
        pass
    
    def cleanup(self):
        """Remove temporary repository clone"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
```

### `lib/ai_evaluator.py`
```python
import anthropic
import json
from typing import Dict, Any
from .schemas import CommitMetadata, CommitEvaluation

class AIEvaluator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def evaluate_commit(self, commit: CommitMetadata, diff: str) -> CommitEvaluation:
        """Evaluate a commit using Claude Sonnet 4.5"""
        # Build prompt
        # Call Anthropic API
        # Parse JSON response
        # Return CommitEvaluation
        pass
    
    def _build_prompt(self, commit: CommitMetadata, diff: str) -> str:
        """Construct evaluation prompt"""
        pass
    
    def _parse_response(self, response_text: str, commit: CommitMetadata) -> CommitEvaluation:
        """Parse LLM response into CommitEvaluation"""
        # Extract JSON from response
        # Add commit metadata
        # Validate with Pydantic
        # Return object
        pass
```

### `pages/6_CommitAnalysis.py`
```python
import streamlit as st
import os
from lib.git_handler import GitHandler
from lib.ai_evaluator import AIEvaluator
from lib.schemas import CommitEvaluation

# Page config
st.set_page_config(page_title="Commit Analysis", page_icon="🔍")

# Initialize session state
if 'evaluated_commits' not in st.session_state:
    st.session_state.evaluated_commits = []
if 'current_offset' not in st.session_state:
    st.session_state.current_offset = 0
if 'git_handler' not in st.session_state:
    st.session_state.git_handler = None

# Header
st.title("🔍 Git Commit Attribution Analyzer")
st.markdown("AI-powered analysis of code contributions")

# Repository input
repo_url = st.text_input("Git Repository URL", placeholder="https://github.com/user/repo.git")

# Clone button
if st.button("Clone & Analyze"):
    if not repo_url:
        st.error("Please enter a repository URL")
    else:
        with st.spinner("Cloning repository..."):
            try:
                handler = GitHandler()
                handler.clone_repository(repo_url)
                st.session_state.git_handler = handler
                st.session_state.current_offset = 0
                st.session_state.evaluated_commits = []
                st.success(f"✓ Cloned • {handler.get_total_commits()} commits total")
            except Exception as e:
                st.error(f"Failed to clone: {str(e)}")

# Analysis section
if st.session_state.git_handler:
    handler = st.session_state.git_handler
    
    # Auto-analyze first batch if empty
    if len(st.session_state.evaluated_commits) == 0:
        with st.spinner("Analyzing commits..."):
            analyze_commits(handler, st.session_state.current_offset, 5)
    
    # Display commits
    st.markdown(f"### 📊 Commit Analysis (Showing {len(st.session_state.evaluated_commits)} commits)")
    
    for evaluation in st.session_state.evaluated_commits:
        display_commit_card(evaluation)
    
    # Load more button
    if st.button("Load More Commits"):
        st.session_state.current_offset += 5
        with st.spinner("Analyzing more commits..."):
            analyze_commits(handler, st.session_state.current_offset, 5)
        st.rerun()

def analyze_commits(handler: GitHandler, offset: int, limit: int):
    """Analyze batch of commits"""
    # Get commit metadata
    # For each commit: get diff and evaluate
    # Append to session_state.evaluated_commits
    pass

def display_commit_card(evaluation: CommitEvaluation):
    """Display a single commit evaluation card"""
    with st.expander(f"**{evaluation.commit_hash[:7]}** • {evaluation.author} • {evaluation.message[:60]}..."):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Technical Complexity", f"{'⭐' * evaluation.technical_complexity}")
            st.metric("Scope of Impact", f"{'⭐' * evaluation.scope_of_impact}")
            st.metric("Code Quality", f"{'⭐' * evaluation.code_quality_delta}")
        
        with col2:
            st.metric("Risk & Criticality", f"{'⭐' * evaluation.risk_criticality}")
            st.metric("Knowledge Sharing", f"{'⭐' * evaluation.knowledge_sharing}")
            st.metric("Innovation", f"{'⭐' * evaluation.innovation}")
        
        st.markdown(f"**Categories:** {', '.join(evaluation.categories)}")
        st.markdown(f"**Impact:** {evaluation.impact_summary}")
        st.markdown(f"**Files Changed:** {evaluation.files_changed} (+{evaluation.lines_added}, -{evaluation.lines_removed})")
        
        with st.expander("Show Reasoning"):
            st.markdown(evaluation.reasoning)
```

---

## Testing Strategy

### Test Repositories (Recommended)
1. **Small** (50-100 commits): Personal project or small library
2. **Medium** (500 commits): Mid-size open source project
3. **Large** (1000+ commits): Popular framework (for pagination testing)

### Manual Test Checklist
- [ ] Clone via HTTPS URL works
- [ ] Clone via SSH URL works (if user has keys configured)
- [ ] Invalid URL shows error
- [ ] First 5 commits load automatically
- [ ] "Load More" button works correctly
- [ ] Commit cards display all information
- [ ] Star ratings render correctly
- [ ] Reasoning expander works
- [ ] LLM evaluations are reasonable
- [ ] Progress indicators show during analysis
- [ ] Session state persists correctly

### Cost Testing
- Analyze 20 commits and track API costs
- Verify cost is within acceptable range ($0.05-0.10 per commit)
- Optimize prompt if costs are too high

---

## Deployment Checklist

### Pre-Deployment
- [ ] Install all dependencies in `requirements.txt`
- [ ] Set Anthropic API key in `.streamlit/secrets.toml`
- [ ] Test with at least 3 different repositories
- [ ] Verify error handling for edge cases
- [ ] Document known limitations
- [ ] Add usage instructions to page

### Launch
- [ ] Run: `streamlit run 1_Home.py`
- [ ] Navigate to Commit Analysis page
- [ ] Verify all functionality works
- [ ] Monitor API usage and costs
- [ ] Gather user feedback

---

## Cost Estimates

### Per-Commit Analysis
- Input tokens: ~1,000-1,500 (metadata + diff)
- Output tokens: ~300-500 (evaluation)
- Cost: ~$0.05-0.08 per commit

### Typical Session
- Analyze 20 commits: ~$1.00-1.60
- Analyze 50 commits: ~$2.50-4.00
- Analyze 100 commits: ~$5.00-8.00

### Budget Management
- Implement rate limiting if needed
- Cache evaluations (future enhancement)
- Truncate very large diffs
- Allow users to select which commits to analyze

---

## Known Limitations (MVP)

### Technical
1. **No caching** - Re-analyzing same commits costs API calls
2. **No persistence** - Session state lost on page refresh
3. **Linear processing** - Commits analyzed one at a time
4. **No agent exploration** - Basic evaluation only (no git tool use)
5. **Diff truncation** - Very large commits may lose context

### UX
1. **No contributor aggregation** - Individual commits only
2. **No visualization** - Text-based display only
3. **No export** - Cannot save or share results
4. **No filtering** - Cannot filter by author or date
5. **Session-based** - No user accounts or history

### Streamlit Constraints
1. **No real-time updates** - Must trigger rerun
2. **Limited styling** - Basic component appearance
3. **No file upload** - URL input only
4. **Memory limits** - Large repos may cause issues

---

## Future Enhancements (Post-MVP)

### Phase 2: Aggregate Analytics (Next Priority)
- Contributor profile page
- Time range filtering
- Author selection
- Aggregate dimension averages
- Top commits by dimension

### Phase 3: Advanced Features
- Caching with SQLite
- Export to PDF/Markdown
- Visualization (charts, timeline)
- Agent exploration for complex commits
- Comparison mode (compare contributors)

### Phase 4: Production Features
- User authentication
- Persistent storage
- API for programmatic access
- GitHub/GitLab integration
- Webhook support for CI/CD

---

## Success Metrics

### MVP Success Criteria
- ✅ User can clone any public git repository
- ✅ System analyzes 5 commits automatically
- ✅ User can load more commits incrementally
- ✅ Evaluations are displayed clearly
- ✅ Total time from URL to first results: < 60 seconds
- ✅ Cost per commit: < $0.10
- ✅ System handles errors gracefully

### Quality Metrics
- LLM evaluations are reasonable (manual spot-check)
- No crashes with edge cases
- Clear error messages
- Responsive UI (no freezing)

---

## Timeline Estimate

### Development Time
- **Phase 1** (Setup): 1-2 hours
- **Phase 2** (Data Models): 30 minutes
- **Phase 3** (Git Operations): 2-3 hours
- **Phase 4** (AI Evaluation): 3-4 hours
- **Phase 5** (Streamlit UI): 3-4 hours
- **Phase 6** (Testing): 2-3 hours

**Total: 12-16.5 hours** (split across 2-3 days)

### Recommended Schedule
- **Day 1** (4-6 hours): Phases 1-3 (infrastructure + git)
- **Day 2** (4-6 hours): Phases 4-5 (AI + UI)
- **Day 3** (2-4 hours): Phase 6 (testing + polish)

---

## Getting Started

### Immediate Next Steps
1. **Install dependencies**
   ```bash
   cd /home/jasperh/Desktop/hackviolet
   pip install streamlit gitpython anthropic pydantic python-dotenv
   ```

2. **Set up API key**
   - Create `.streamlit/secrets.toml`
   - Add: `ANTHROPIC_API_KEY = "sk-..."`

3. **Create project structure**
   ```bash
   mkdir -p lib
   touch lib/__init__.py lib/git_handler.py lib/ai_evaluator.py lib/schemas.py
   touch pages/6_CommitAnalysis.py
   ```

4. **Start with schemas**
   - Implement Pydantic models in `lib/schemas.py`
   - This defines the data contract for the entire system

5. **Build git handler**
   - Implement `lib/git_handler.py`
   - Test cloning and metadata extraction independently

6. **Implement AI evaluator**
   - Build `lib/ai_evaluator.py`
   - Test with sample commit data

7. **Create Streamlit page**
   - Build `pages/6_CommitAnalysis.py`
   - Integrate all components

8. **Test & refine**
   - Test with real repositories
   - Fix bugs and edge cases
   - Polish UI

---

## Conclusion

This MVP implementation plan provides a clear, concrete path to building a functional git attribution analyzer. The focus is on demonstrating core value (AI-powered commit analysis) with minimal complexity (Streamlit, no caching, single page).

Key success factors:
- **Simple scope**: Commit-level analysis only
- **Rapid development**: Streamlit enables fast iteration
- **Cost-effective**: Basic evaluation without expensive agent exploration
- **Extensible**: Clean architecture allows easy enhancement

Once the MVP is working smoothly, the natural next step is adding the aggregate contributor analytics page, followed by advanced features like caching, visualization, and agent exploration.
