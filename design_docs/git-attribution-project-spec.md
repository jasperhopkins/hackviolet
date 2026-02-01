# Git Contribution Attribution & Analysis Tool - Project Specification

## Project Overview

A women's empowerment hackathon project to create an intelligent code contribution attribution system for non-technical stakeholders. The tool leverages LLMs to provide meaningful insights into code contributions, moving beyond archaic metrics (lines of code, files changed) to create a more meritocratic software environment where exceptional individual contributors can be properly recognized.

## Core Problem Statement

Traditional code metrics are inadequate for evaluating contributions:
- Lines of code changed is meaningless (trivial changes vs. critical fixes)
- Files touched doesn't reflect impact or difficulty
- Commit count encourages gaming the system
- No visibility into code quality, complexity, or cross-system impact
- Critical maintenance work and bug fixes are undervalued

## Solution Approach

An AI-powered analysis tool that:
1. Clones git repositories and extracts metadata
2. Uses constrained agentic exploration to understand code context
3. Evaluates contributions across multiple meaningful dimensions
4. Presents insights in an interpretable format for non-technical stakeholders
5. Avoids creating new gameable metrics while providing actionable insights

---

## Technical Architecture

### High-Level Flow

```
User Input (git repo URL)
    ↓
Clone Repository (temporary local copy)
    ↓
Phase 1: Structured Metadata Extraction (GitPython)
    ↓
Phase 2: Agentic Deep Analysis (LLM with constrained git tools)
    ↓
Multi-dimensional Evaluation
    ↓
Dashboard/Report Generation
```

### Technology Stack

**Language:** Python

**Git Interface:**
- **Primary:** GitPython (Pythonic wrapper around git commands)
- **Fallback:** subprocess + native git commands for specific operations
- **Avoid:** Direct `.git` directory parsing (unstable, complex)

**LLM Provider:**
- **Recommended:** Anthropic Claude (Sonnet 4)
  - Best-in-class tool use and code understanding
  - 200k token context window
  - Native tool calling API
  - Extended thinking for complex analysis
- **Cost:** ~$3/M input tokens, ~$15/M output tokens
- **Estimated:** $5-20 for analyzing 100 commits with deep exploration

**Agent Framework:**
- **Avoid:** LangChain (unnecessary abstraction, version instability)
- **Recommended:** Custom agent loop (~100-150 lines, full control)
- **Optional:** Pydantic for structured outputs, Instructor for schema enforcement

### Repository Handling Strategy

**Clone and Analyze Approach** (Provider-Agnostic)

**Rationale:**
- Works with any git provider (GitHub, GitLab, Bitbucket, self-hosted)
- No need for provider-specific OAuth or API integrations
- Complete metadata access without rate limits
- Uses existing user git credentials (SSH keys, tokens)

**User Flow:**
1. User provides git clone URL: `git@github.com:org/repo.git`
2. Application clones to temporary directory
3. Runs analysis (git log, diff, blame)
4. Presents insights
5. Cleans up or caches clone for re-analysis

**Optimizations:**
- Shallow clones (`--depth`) for large repos if full history not needed
- Bare repos if working tree not required
- Caching for repeated analyses

---

## Agentic Architecture

### Hybrid Approach: Structured + Agentic

**Phase 1: Deterministic Metadata Extraction**

Using GitPython/subprocess, extract:
- All commits with author, timestamp, message
- Files changed per commit
- Basic diff stats
- Commit relationships (parents, merges)

**Phase 2: Constrained Agent Exploration**

Agent has access to limited, read-only git tools:
- `git show <commit>` - Full commit details
- `git diff <commit>^..<commit>` - See changes
- `git log --follow <file>` - Track file history
- `git blame <file>` - Line-by-line attribution
- `git show <commit>:<file>` - View file at specific commit
- `git grep <pattern> <commit>` - Search code at point in time
- `git log --grep=<pattern>` - Search commit messages

**Constraints:**
- Read-only operations only
- Rate limiting (max 50 tool calls per analysis)
- Scoped to relevant commits/files
- Token budget per analysis

### Agent Implementation

```python
class GitAnalysisAgent:
    def __init__(self, repo_path, anthropic_key):
        self.repo = Repo(repo_path)
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        self.tools = self._setup_tools()
        self.conversation_history = []
        self.tool_call_count = 0
        self.max_tool_calls = 50
    
    def analyze_commit(self, commit_hash, max_iterations=10):
        """
        Analyze a commit with agent exploration.
        Returns structured CommitEvaluation.
        """
        # Agent loop with tool use
        pass
    
    def _execute_tools(self, tool_requests):
        """Execute git commands based on LLM tool calls"""
        # Enforce rate limits
        # Execute git operations
        # Return results to LLM
        pass
```

### Agent Use Cases

1. **Bug Fix Analysis:**
   - Trace when buggy code was introduced
   - Understand root cause complexity
   - Identify affected systems via grep/blame
   - Assess downstream impact

2. **Cross-File Impact:**
   - Follow imports and dependencies
   - Understand how changes ripple through codebase
   - Identify integration points

3. **Refactoring Scope:**
   - Determine breadth of refactor
   - Assess tech debt reduction
   - Validate test coverage improvements

4. **Context Gathering:**
   - Pull related commits
   - Find referenced issues/tickets in messages
   - Build narrative of feature development

---

## Evaluation Metrics Framework

### Core Philosophy

**DO NOT:** Create a single "contribution score" or point system
- Reductive and gameable
- Misses context and nuance
- Encourages unhealthy competition

**DO:** Multi-dimensional scoring with narrative context
- Multiple interpretable dimensions
- Qualitative insights alongside quantitative
- Emphasize complementary strengths, not ranking

### Tier 1: Impact Dimensions (AI-Evaluated, 1-5 Scale)

**1. Technical Complexity**
- 1: Simple config/typo fixes
- 3: Standard feature implementation
- 5: Novel algorithms, complex architecture
- *Employer Value:* Identifies engineers who tackle hard problems

**2. Scope of Impact**
- 1: Single function/file
- 3: Module-level changes
- 5: Cross-system/architectural changes
- *Employer Value:* Shows ability to work at scale

**3. Code Quality Improvement**
- 1: Quality degradation (tech debt added)
- 3: Neutral (no quality change)
- 5: Major refactoring, tech debt reduction
- *Employer Value:* Long-term codebase health

**4. Risk & Criticality**
- 1: Low-risk, isolated changes
- 3: Standard production code
- 5: Security fixes, critical system changes
- *Employer Value:* Trust with high-stakes work

**5. Knowledge Sharing**
- 1: No documentation, poor comments
- 3: Adequate inline comments
- 5: Excellent docs, comprehensive tests, examples
- *Employer Value:* Team enablement, onboarding impact

**6. Innovation**
- 1: Copy/paste or trivial changes
- 3: Standard implementation
- 5: Novel approach, creative problem-solving
- *Employer Value:* Problem-solving ability, thought leadership

### Tier 2: Contextual Metadata (AI-Extracted)

**Categories:**
- Bug fix
- New feature
- Refactoring
- Performance optimization
- Security fix
- Testing
- Documentation
- Infrastructure/DevOps

**Dependencies & Impact:**
- "Unblocked 3 other developers"
- "Enabled feature X"
- "Required by PRs #123, #456"

**Collaboration Signals:**
- Pair programming indicators
- Mentoring junior developers
- Extensive code review participation

### Tier 3: Aggregate Insights (Computed)

**Individual Contributor Profile:**
- Impact distribution (% of commits in each dimension)
- Strengths profile ("Excels at: architectural changes, critical bug fixes")
- Consistency (sustained vs. sporadic contributions)
- Versatility (range of work types)

**Team-Level Insights:**
- Complementary strengths (not rankings)
- Coverage gaps ("Team needs more focus on testing")
- Quality trends over time
- Technical debt trajectory

---

## Data Models

### CommitEvaluation (Pydantic Schema)

```python
from pydantic import BaseModel, Field

class CommitEvaluation(BaseModel):
    """Structured evaluation of a single commit"""
    
    # Identity
    commit_hash: str
    author: str
    timestamp: str
    message: str
    
    # Core dimensions (1-5 scale)
    technical_complexity: int = Field(ge=1, le=5)
    scope_of_impact: int = Field(ge=1, le=5)
    code_quality_delta: int = Field(ge=1, le=5)
    risk_criticality: int = Field(ge=1, le=5)
    knowledge_sharing: int = Field(ge=1, le=5)
    innovation: int = Field(ge=1, le=5)
    
    # Contextual metadata
    categories: list[str]  # ["bug_fix", "security", "refactor"]
    impact_summary: str  # 1-2 sentence high-level summary
    dependencies: list[str]  # What this enabled/unblocked
    affected_systems: list[str]  # Components/modules touched
    
    # Supporting evidence
    reasoning: str  # Detailed justification for scores
    key_files: list[str]  # Most important files changed
    related_commits: list[str]  # Related work by this or others
    lines_added: int
    lines_removed: int
    files_changed: int

class ContributorProfile(BaseModel):
    """Aggregate profile for a contributor"""
    
    name: str
    email: str
    total_commits: int
    date_range: tuple[str, str]
    
    # Dimension aggregates
    avg_technical_complexity: float
    avg_scope_of_impact: float
    avg_code_quality: float
    avg_risk_criticality: float
    avg_knowledge_sharing: float
    avg_innovation: float
    
    # Distribution analysis
    complexity_distribution: dict[int, int]  # {1: 5, 2: 10, ...}
    category_breakdown: dict[str, int]  # {"bug_fix": 23, "feature": 45}
    
    # Notable contributions (top 5 by various dimensions)
    most_complex: list[str]  # commit hashes
    highest_impact: list[str]
    most_critical: list[str]
    
    # Narrative
    strengths: list[str]  # ["System architecture", "Security"]
    growth_areas: list[str]  # ["Frontend work", "Documentation"]
    summary: str  # AI-generated paragraph
```

---

## LLM Prompting Strategy

### Commit Analysis Prompt Template

```
You are analyzing a code commit to evaluate its contribution across multiple dimensions.

COMMIT INFORMATION:
Hash: {commit_hash}
Author: {author}
Date: {timestamp}
Message: {commit_message}

FILES CHANGED: {file_list}

DIFF PREVIEW:
{diff_snippet}

TASK:
Evaluate this commit across these dimensions (1-5 scale):

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
- Categorize the commit (bug_fix, feature, refactor, security, etc.)
- Summarize the impact in 1-2 sentences
- Identify what this enabled or unblocked
- List the most important files changed
- Note any related commits or dependencies

You have access to git tools to explore the repository for context:
- git_show_commit: See full commit details
- git_blame_file: See line-by-line attribution
- git_file_history: Track how a file evolved
- git_search_code: Find patterns in the codebase

Use these tools to gather context before providing your evaluation.
Focus especially on understanding cross-file impacts for complex changes.

Provide scores with detailed justification.
```

### Tool Definitions for Claude

```python
tools = [
    {
        "name": "git_show_commit",
        "description": "Show complete details of a specific commit including full diff",
        "input_schema": {
            "type": "object",
            "properties": {
                "commit_hash": {
                    "type": "string",
                    "description": "The commit hash to examine"
                }
            },
            "required": ["commit_hash"]
        }
    },
    {
        "name": "git_blame_file",
        "description": "Show line-by-line attribution for a file at a specific commit",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to file relative to repo root"
                },
                "commit_hash": {
                    "type": "string",
                    "description": "Optional commit hash, defaults to current"
                }
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "git_file_history",
        "description": "Show commit history for a specific file, following renames",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to file relative to repo root"
                },
                "max_commits": {
                    "type": "integer",
                    "description": "Maximum number of commits to return (default 10)"
                }
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "git_search_code",
        "description": "Search for a pattern in the codebase at a specific commit",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (supports regex)"
                },
                "commit_hash": {
                    "type": "string",
                    "description": "Optional commit hash, defaults to current"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Optional file pattern to limit search (e.g., '*.py')"
                }
            },
            "required": ["pattern"]
        }
    }
]
```

---

## Output Format & Presentation

### Individual Contributor View

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTRIBUTOR: Alice Chen
PERIOD: Q4 2024 (Oct 1 - Dec 31)
TOTAL COMMITS: 87
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPACT PROFILE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
High Complexity (4-5):       ████████░░ 37 commits (43%)
Cross-System Impact (4-5):   ██████░░░░ 24 commits (28%)
Quality Improvements (4-5):  █████████░ 41 commits (47%)
Critical/Security (4-5):     ███░░░░░░░ 12 commits (14%)
Knowledge Sharing (4-5):     ███████░░░ 31 commits (36%)
Innovation (4-5):            █████░░░░░ 19 commits (22%)

CONTRIBUTION BREAKDOWN:
Bug Fixes:        ████████████░░ 28 commits (32%)
New Features:     ██████████░░░░ 23 commits (26%)
Refactoring:      ███████░░░░░░░ 18 commits (21%)
Security:         ███░░░░░░░░░░░  8 commits (9%)
Documentation:    ████░░░░░░░░░░ 10 commits (11%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOTABLE CONTRIBUTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔒 CRITICAL: Fixed race condition in token validation
   Commit: abc123f
   Impact: High-severity security vulnerability affecting 50k users
   Complexity: Required deep understanding of async/concurrency patterns
   Dependencies: Enabled secure API v2 rollout
   
🏗️ ARCHITECTURAL: Refactored payment processing module
   PR: #456
   Impact: Reduced technical debt, improved test coverage by 40%
   Scope: Cross-team dependency, touched 3 microservices
   Innovation: Introduced event-sourcing pattern to team
   Dependencies: Enabled PCI compliance work
   
📚 KNOWLEDGE: Documented API integration patterns
   Commit: def789a
   Impact: Onboarded 3 new developers, referenced in 47 subsequent PRs
   Quality: Comprehensive examples with error handling
   
⚡ PERFORMANCE: Optimized database query layer
   Commit: ghi012b
   Impact: Reduced API response time by 60% (p95)
   Complexity: Required query plan analysis and index optimization
   
🐛 CRITICAL: Fixed data corruption in backup system
   Commit: jkl345c
   Impact: Prevented potential data loss for 200+ customers
   Risk: Production hotfix, deployed under pressure

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRENGTHS & GROWTH AREAS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STRENGTHS:
• System architecture and design
• Security-focused development
• Mentorship and knowledge sharing
• Critical bug diagnosis and resolution
• Cross-team collaboration

GROWTH OPPORTUNITIES:
• Frontend development and UI work
• Performance optimization and profiling
• Infrastructure and DevOps contributions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Alice is a strong senior engineer who excels at tackling complex 
architectural challenges and security-critical work. Her contributions 
consistently demonstrate deep technical expertise and a focus on long-term 
code quality. She's particularly effective at reducing technical debt and 
creating foundational improvements that enable other developers. Her 
documentation and knowledge-sharing efforts have measurably improved team 
productivity. Alice would benefit from expanding into frontend and 
performance work to become more full-stack versatile.
```

### Team Comparison View (Not a Leaderboard!)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEAM STRENGTHS OVERVIEW
Engineering Team • Q4 2024
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMPLEMENTARY STRENGTHS:

Alice Chen:          🏗️ Architecture  🔒 Security  📚 Mentorship
Bob Kumar:           🐛 Bug Diagnosis ⚡ Performance 🧪 Testing
Carmen Rodriguez:    🎨 Frontend      📱 UX/UI      ♿ Accessibility
David Park:          🔧 DevOps        🏗️ Infrastructure 📊 Monitoring

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEAM COVERAGE ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strong Coverage:
✓ Backend architecture and design
✓ Security and critical bug fixes
✓ Infrastructure and DevOps
✓ Frontend/UI development

Needs Attention:
⚠ API documentation (only 12% of commits)
⚠ Performance optimization (only 8% of commits)
⚠ Integration testing (only 15% of commits)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUALITY TRENDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Code Quality Δ:        ↗ +12% (improving)
Test Coverage:         → Stable at 78%
Technical Debt:        ↘ -8% (reducing)
Documentation:         ↗ +15% (improving)
```

### Dashboard Visualizations

**Radar Chart (Individual):**
- 6 axes for each dimension
- Visual comparison to team average
- Shows well-rounded vs. specialized contributors

**Timeline View:**
- Scatter plot of commits over time
- Color-coded by impact level
- Tooltip shows commit details

**Heatmap (Team):**
- Contributors × Dimensions
- Shows team coverage and gaps
- Not for ranking, for understanding balance

---

## Implementation Phases

### Phase 1: MVP (Hackathon Demo)

**Goals:**
- Basic cloning and metadata extraction
- Simple 6-dimension scoring (without deep agent exploration)
- Individual contributor profile view
- 1-2 detailed commit analysis examples

**Deliverables:**
- CLI tool that accepts git URL
- Generates markdown report for single contributor
- Demonstrates clear improvement over traditional metrics

**Implementation Tasks:**
1. Set up GitPython integration
2. Extract commit metadata for all contributors
3. Create basic LLM prompt for commit evaluation
4. Implement CommitEvaluation Pydantic model
5. Generate simple text-based report
6. Create 2-3 demo examples (bug fix, refactor, feature)

**Time Estimate:** 12-16 hours

### Phase 2: Agentic Enhancement (Post-Hackathon)

**Goals:**
- Add constrained agent exploration
- Deep analysis for complex commits
- Timeline visualization
- Team comparison view

**Deliverables:**
- Agent with git tool access
- Interactive exploration for selected commits
- HTML dashboard with charts
- Team-level insights

**Implementation Tasks:**
1. Build GitTools class with rate limiting
2. Implement agent loop with Anthropic tool use
3. Create visualization layer (Plotly/Chart.js)
4. Build team aggregation logic
5. Generate HTML reports with embedded charts

**Time Estimate:** 20-24 hours

### Phase 3: Production Features (Future)

**Goals:**
- Web UI (Streamlit/Flask)
- Caching and incremental updates
- Integration with PR review data
- Customizable dimension weights
- Export to PDF/slides

**Implementation Tasks:**
1. Build web interface
2. Add database for caching evaluations
3. Integrate with GitHub/GitLab APIs for PR context
4. Allow custom metric configuration
5. Export functionality

**Time Estimate:** 40+ hours

---

## Project Structure

```
git-attribution-analyzer/
├── README.md
├── requirements.txt
├── setup.py
│
├── analyzer/
│   ├── __init__.py
│   ├── repo.py              # Repository cloning and management
│   ├── extractor.py         # Metadata extraction (GitPython)
│   ├── agent.py             # LLM agent implementation
│   ├── tools.py             # Git tool definitions for agent
│   ├── evaluator.py         # Commit evaluation logic
│   └── schemas.py           # Pydantic models
│
├── analysis/
│   ├── __init__.py
│   ├── metrics.py           # Dimension calculation
│   ├── aggregation.py       # Contributor/team aggregation
│   └── insights.py          # AI summary generation
│
├── output/
│   ├── __init__.py
│   ├── markdown.py          # Markdown report generation
│   ├── html.py              # HTML dashboard generation
│   └── templates/           # Jinja2 templates
│
├── ui/
│   └── cli.py               # Command-line interface
│
├── tests/
│   ├── test_extractor.py
│   ├── test_agent.py
│   ├── test_evaluator.py
│   └── fixtures/            # Sample repos for testing
│
└── examples/
    ├── sample_report.md
    └── demo_repos.txt
```

---

## Key Implementation Details

### Repository Cloning

```python
def clone_repository(git_url: str, temp_dir: str = None) -> Repo:
    """
    Clone a git repository for analysis.
    
    Args:
        git_url: Git clone URL (https or ssh)
        temp_dir: Optional directory, creates temp if None
    
    Returns:
        GitPython Repo object
    """
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="git_analysis_")
    
    try:
        repo = Repo.clone_from(git_url, temp_dir)
        return repo
    except GitCommandError as e:
        raise Exception(f"Failed to clone repository: {e}")
```

### Metadata Extraction

```python
def extract_commits(repo: Repo, 
                   author: str = None,
                   since: str = None,
                   until: str = None) -> list[dict]:
    """
    Extract commit metadata from repository.
    
    Args:
        repo: GitPython Repo object
        author: Filter by author email/name
        since: ISO date string for start
        until: ISO date string for end
    
    Returns:
        List of commit metadata dicts
    """
    commits = []
    
    kwargs = {}
    if author:
        kwargs['author'] = author
    if since:
        kwargs['since'] = since
    if until:
        kwargs['until'] = until
    
    for commit in repo.iter_commits(**kwargs):
        commits.append({
            'hash': commit.hexsha,
            'author': commit.author.name,
            'email': commit.author.email,
            'timestamp': commit.committed_datetime.isoformat(),
            'message': commit.message,
            'files': list(commit.stats.files.keys()),
            'insertions': commit.stats.total['insertions'],
            'deletions': commit.stats.total['deletions'],
            'lines_changed': commit.stats.total['lines'],
        })
    
    return commits
```

### Agent Tool Execution

```python
class GitTools:
    """Constrained git tools for LLM agent"""
    
    def __init__(self, repo: Repo, max_calls: int = 50):
        self.repo = repo
        self.call_count = 0
        self.max_calls = max_calls
    
    def _check_limit(self):
        if self.call_count >= self.max_calls:
            raise Exception("Tool call limit reached")
        self.call_count += 1
    
    def show_commit(self, commit_hash: str) -> str:
        """Show full commit details including diff"""
        self._check_limit()
        commit = self.repo.commit(commit_hash)
        return commit.diff(commit.parents[0], create_patch=True)
    
    def blame_file(self, filepath: str, commit_hash: str = None) -> str:
        """Show line-by-line attribution"""
        self._check_limit()
        commit = self.repo.commit(commit_hash) if commit_hash else self.repo.head.commit
        blame = self.repo.blame(commit, filepath)
        # Format blame output
        return formatted_blame
    
    def file_history(self, filepath: str, max_commits: int = 10) -> list[dict]:
        """Get commit history for a file"""
        self._check_limit()
        commits = list(self.repo.iter_commits(paths=filepath, max_count=max_commits))
        return [{'hash': c.hexsha, 'message': c.message, 'author': c.author.name} 
                for c in commits]
    
    def search_code(self, pattern: str, commit_hash: str = None) -> str:
        """Search for pattern in codebase"""
        self._check_limit()
        # Use git grep
        result = self.repo.git.grep(pattern, commit_hash or 'HEAD')
        return result
```

### LLM Integration

```python
def evaluate_commit_with_agent(commit_data: dict, 
                               repo: Repo,
                               api_key: str) -> CommitEvaluation:
    """
    Evaluate a commit using LLM agent with git tools.
    
    Args:
        commit_data: Extracted commit metadata
        repo: GitPython Repo object
        api_key: Anthropic API key
    
    Returns:
        CommitEvaluation model
    """
    client = anthropic.Anthropic(api_key=api_key)
    tools = GitTools(repo)
    
    # Build initial prompt
    prompt = f"""
    Analyze this commit and evaluate it across 6 dimensions (1-5 scale):
    
    Commit: {commit_data['hash']}
    Author: {commit_data['author']}
    Message: {commit_data['message']}
    Files: {', '.join(commit_data['files'])}
    
    Use git tools to explore context as needed.
    Provide structured evaluation with justification.
    """
    
    messages = [{"role": "user", "content": prompt}]
    
    # Agent loop
    for iteration in range(10):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=get_tool_definitions(),
            messages=messages
        )
        
        # Check if done
        if response.stop_reason == "end_turn":
            # Parse final evaluation
            return parse_evaluation(response.content)
        
        # Execute tools
        if response.stop_reason == "tool_use":
            tool_results = execute_tools(response.content, tools)
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            continue
    
    raise Exception("Agent exceeded iteration limit")
```

---

## Anti-Patterns to Avoid

### ❌ Don't Do This

1. **Single numerical score**
   - "Alice: 847 points, Bob: 412 points"
   - Creates unhealthy competition
   - Oversimplifies contributions

2. **Public leaderboards**
   - Ranking developers destroys collaboration
   - Gaming incentives
   - Demoralizing for maintenance work

3. **Ignoring context**
   - Junior vs senior comparisons
   - Different tech stacks
   - Project phase (greenfield vs maintenance)

4. **Over-automation**
   - Using scores for performance reviews without human judgment
   - Automated promotion decisions
   - Punishment based on metrics

5. **Letting agents run wild**
   - Unlimited tool calls
   - No rate limiting
   - Accessing unrelated parts of codebase

### ✅ Do This Instead

1. **Multi-dimensional profiles**
   - Show strengths and growth areas
   - Narrative context
   - Celebrate diversity of contributions

2. **Team insights, not rankings**
   - Complementary strengths
   - Coverage analysis
   - Trend identification

3. **Context-aware analysis**
   - Role-appropriate expectations
   - Project phase consideration
   - Technology stack awareness

4. **Human-in-the-loop**
   - Metrics inform, don't decide
   - Manager interpretation required
   - Focus on growth, not punishment

5. **Constrained agent exploration**
   - Rate limits
   - Scoped access
   - Clear guardrails

---

## Marketing & Demo Strategy

### Hackathon Pitch

**Problem:**
"Traditional code metrics are broken. Lines of code and commit counts tell you nothing about impact. A 5-line security fix is more valuable than a 500-line boilerplate feature, but traditional tools can't tell the difference."

**Solution:**
"We built an AI-powered contribution analyzer that understands what code actually does. It evaluates contributions across 6 meaningful dimensions: complexity, scope, quality, criticality, knowledge sharing, and innovation."

**Demo Flow:**

1. **Show traditional metrics** (lines changed, files touched)
   - "Alice changed 1,234 lines across 87 commits"
   - "Tells us nothing about impact"

2. **Show AI analysis of same contributor**
   - Multi-dimensional profile
   - Highlight critical bug fix (10 lines, huge impact)
   - Show architectural refactor (invisible in LOC)

3. **Deep dive on one commit** (agent exploration)
   - Show agent discovering cross-file dependencies
   - Tracing bug to original introduction
   - Understanding downstream impact

4. **Team view** (not leaderboard)
   - Complementary strengths
   - "Team has strong backend, needs frontend focus"

**Key Differentiation:**
- "Beyond gameable metrics"
- "AI understands context and impact"
- "Empowers recognition of hidden contributions"
- "Especially valuable for women and underrepresented contributors doing unglamorous but critical work"

### Women's Empowerment Angle

**Problem Context:**
- Women often do "invisible" work (mentoring, documentation, code review)
- Bug fixes and maintenance undervalued vs flashy features
- Traditional metrics favor quantity over quality
- Impostor syndrome amplified by bad metrics

**How This Helps:**
- Makes invisible contributions visible
- Values quality and impact over quantity
- Recognizes mentorship and knowledge sharing
- Provides objective, multidimensional evaluation
- Reduces bias from subjective manager assessment

### Success Metrics for Hackathon

**Judges care about:**
1. **Impact:** Does this solve a real problem?
2. **Technical execution:** Does it actually work?
3. **Innovation:** Is this a novel approach?
4. **Feasibility:** Can this be built and deployed?

**Demo Preparation:**
1. Analyze 2-3 open source repos (different sizes)
2. Prepare 5 specific examples showing AI insights
3. Have live demo ready (pre-computed for speed)
4. Show comparison: traditional vs AI metrics
5. One deep agent exploration example

---

## Open Questions & Future Considerations

### Technical

1. **Scalability:** How to handle repos with 100k+ commits?
   - Incremental analysis
   - Sampling strategies
   - Parallel processing

2. **Cost optimization:** LLM costs for large-scale analysis
   - Tiered analysis (quick vs deep)
   - Caching evaluations
   - Batch processing

3. **Accuracy:** How to validate AI evaluations?
   - Human spot-checking
   - Inter-rater reliability
   - Benchmark against expert assessment

### Product

1. **Privacy:** Handling proprietary code
   - On-premise deployment option
   - API key management
   - Data retention policies

2. **Integration:** Where does this fit in workflow?
   - CI/CD integration
   - GitHub App
   - Slack/email reports
   - Performance review season tool

3. **Customization:** Different teams have different needs
   - Configurable dimensions
   - Custom weights
   - Industry-specific categories

### Ethical

1. **Misuse prevention:** How to stop this becoming another surveillance tool?
   - Clear usage guidelines
   - Transparency requirements
   - No automated punishment

2. **Bias:** Could AI evaluations encode human biases?
   - Fairness auditing
   - Diverse training examples
   - Regular bias checks

3. **Gaming:** How to prevent metric manipulation?
   - Multi-dimensional makes gaming harder
   - Focus on narrative over numbers
   - Human oversight required

---

## Success Criteria

### Hackathon (MVP)

✅ **Must Have:**
- Clone and analyze any git repo
- Extract basic metadata for all contributors
- AI evaluation of commits across 6 dimensions
- Generate readable markdown report
- 2-3 compelling demo examples

🎯 **Nice to Have:**
- Simple web UI
- Team comparison view
- Export to PDF

### Post-Hackathon (Production)

✅ **Must Have:**
- Agentic deep exploration
- Interactive visualizations
- Caching and incremental updates
- Team-level insights
- Export functionality

🎯 **Nice to Have:**
- GitHub/GitLab integration
- Scheduled reports
- Slack notifications
- Custom dimension configuration

---

## Getting Started Checklist

### Pre-Implementation

- [ ] Set up Python environment (3.10+)
- [ ] Get Anthropic API key
- [ ] Install GitPython: `pip install gitpython`
- [ ] Install Anthropic SDK: `pip install anthropic`
- [ ] Install Pydantic: `pip install pydantic`
- [ ] Choose test repository (suggest: small open-source project, 100-500 commits)

### Phase 1 Implementation Order

1. [ ] Create project structure
2. [ ] Implement repository cloning
3. [ ] Build metadata extractor
4. [ ] Define Pydantic schemas
5. [ ] Create basic LLM prompt
6. [ ] Implement simple evaluation (no agent)
7. [ ] Build markdown report generator
8. [ ] Test on sample repo
9. [ ] Create 3 demo examples
10. [ ] Prepare hackathon presentation

### Testing Strategy

- Unit tests for metadata extraction
- Integration tests with small test repo
- Manual validation of AI evaluations
- Performance testing (time per commit)
- Cost analysis (API usage per repo)

---

## Appendix: Example Outputs

### Example: Critical Bug Fix

```
COMMIT: abc123f4567890
AUTHOR: Alice Chen
DATE: 2024-12-15
MESSAGE: Fix race condition in token validation

EVALUATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Technical Complexity:     5/5 ⭐⭐⭐⭐⭐
Scope of Impact:          4/5 ⭐⭐⭐⭐
Code Quality Delta:       5/5 ⭐⭐⭐⭐⭐
Risk & Criticality:       5/5 ⭐⭐⭐⭐⭐
Knowledge Sharing:        3/5 ⭐⭐⭐
Innovation:               4/5 ⭐⭐⭐⭐

CATEGORIES: bug_fix, security, critical

IMPACT SUMMARY:
Fixed a severe race condition in the token validation system that could 
allow authentication bypass under high load. The bug affected approximately 
50,000 active users and was exploitable in production.

FILES CHANGED:
- auth/token_validator.py (+15, -8)
- tests/test_auth.py (+45, -0)

AGENT EXPLORATION FINDINGS:
The agent traced this bug to its introduction in commit def789 (6 months ago) 
during a performance optimization. The race condition occurred when multiple 
requests validated the same token simultaneously, causing inconsistent cache 
state. The fix introduces proper locking with minimal performance impact 
(<2ms overhead). Related security audit revealed 3 similar patterns that 
were preemptively fixed in commit ghi012.

DEPENDENCIES:
- Blocked: API v2 security certification
- Enabled: Secure rollout to enterprise customers
- Related: Follow-up cache refactor in commit jkl345

REASONING:
This is a textbook example of a high-impact contribution that traditional 
metrics would severely undervalue. Only 23 net lines changed, but the fix:
1. Required deep understanding of concurrency and async patterns
2. Addressed a critical security vulnerability
3. Involved careful performance analysis to avoid regression
4. Included comprehensive test coverage
5. Demonstrated proactive thinking (related fixes)

The complexity score of 5 reflects the difficulty of debugging race 
conditions and implementing thread-safe solutions. The criticality score 
of 5 reflects the security impact and production urgency.
```

### Example: Routine Feature (for contrast)

```
COMMIT: xyz987d6543210
AUTHOR: Bob Kumar
DATE: 2024-12-10
MESSAGE: Add dark mode toggle to settings

EVALUATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Technical Complexity:     2/5 ⭐⭐
Scope of Impact:          2/5 ⭐⭐
Code Quality Delta:       3/5 ⭐⭐⭐
Risk & Criticality:       1/5 ⭐
Knowledge Sharing:        4/5 ⭐⭐⭐⭐
Innovation:               2/5 ⭐⭐

CATEGORIES: feature, ui, frontend

IMPACT SUMMARY:
Added a user-facing toggle for dark mode in the settings panel. 
Straightforward implementation using existing theme system.

FILES CHANGED:
- ui/settings.jsx (+34, -2)
- styles/themes.css (+12, -0)
- tests/ui/test_settings.js (+18, -0)

REASONING:
This is a standard feature implementation with low technical complexity. 
The dark mode infrastructure already existed; this commit just added the 
UI control. Good test coverage and clear code, but not particularly 
innovative or challenging work. Appropriate for a mid-level developer.
```

---

## Final Notes

This specification represents a comprehensive plan for building an AI-powered git contribution attribution system. The key innovation is moving beyond simplistic metrics to multidimensional, context-aware evaluation that values diverse contributions fairly.

**Core Principles:**
1. No single scores or rankings
2. Multi-dimensional evaluation
3. Narrative context matters
4. Agent exploration for depth
5. Designed to empower, not surveil

**Implementation Priority:**
Focus on MVP for hackathon, then iterate based on feedback. The goal is to demonstrate clear value over traditional metrics with compelling examples.

**Success Depends On:**
- High-quality LLM prompting
- Constrained but useful agent exploration
- Clear, interpretable output format
- Strong demo examples
- Avoiding metric gaming pitfalls

Good luck with the hackathon! 🚀
