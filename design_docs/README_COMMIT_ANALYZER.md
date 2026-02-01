# Git Commit Attribution Analyzer

AI-powered analysis of code contributions using Claude Sonnet 4.5.

## Features

- 🔍 Analyze git commits across 6 meaningful dimensions
- 🤖 AI-powered evaluation using Claude Sonnet 4.5
- 📊 Clean, interactive Streamlit UI
- 🔄 Incremental loading (5 commits at a time)
- 📈 Detailed reasoning for each evaluation

## Evaluation Dimensions

1. **Technical Complexity** - How difficult was this change to implement?
2. **Scope of Impact** - How many systems/components does this affect?
3. **Code Quality Delta** - Did this improve or degrade code quality?
4. **Risk & Criticality** - How critical is this to system reliability/security?
5. **Knowledge Sharing** - How well documented and tested is this change?
6. **Innovation** - How novel or creative is the solution?

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Anthropic API key:**
   
   Create `.streamlit/secrets.toml`:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-api03-your-key-here"
   ```

   Or enter it directly in the UI when prompted.

3. **Run the application:**
   ```bash
   streamlit run 1_Home.py
   ```

4. **Navigate to the Commit Analysis page** in the sidebar.

## Usage

1. Enter a git repository URL (HTTPS or SSH)
   - Example: `https://github.com/username/repo.git`
   - Example: `git@github.com:username/repo.git`

2. Click "Clone & Analyze"
   - The first 5 commits will be analyzed automatically

3. Review the evaluations
   - Click on each commit card to see detailed analysis
   - View the AI's reasoning for each score

4. Load more commits
   - Click "Load More Commits" to analyze the next 5

## Project Structure

```
hackviolet/
├── lib/
│   ├── __init__.py           # Package initialization
│   ├── schemas.py            # Pydantic data models
│   ├── git_handler.py        # Git operations
│   └── ai_evaluator.py       # AI evaluation logic
├── pages/
│   └── 6_CommitAnalysis.py   # Streamlit UI page
├── requirements.txt          # Python dependencies
└── .streamlit/
    └── secrets.toml          # API keys (not in git)
```

## Cost Estimates

- **Per commit:** ~$0.05-0.08
- **20 commits:** ~$1.00-1.60
- **50 commits:** ~$2.50-4.00

Costs depend on commit size and complexity.

## Limitations (MVP)

- No caching - re-analyzing same commits costs API calls
- No persistence - session state lost on page refresh
- Linear processing - commits analyzed one at a time
- No agent exploration - basic evaluation only
- Diff truncation - very large commits may lose context

## Future Enhancements

- Aggregate contributor profiles
- Team comparison views
- Caching with SQLite
- Export to PDF/Markdown
- Timeline visualizations
- Advanced agent exploration with git tools

## Technical Details

- **LLM Model:** Claude Sonnet 4.5 (`claude-sonnet-4-20250514`)
- **Git Interface:** GitPython
- **UI Framework:** Streamlit
- **Data Validation:** Pydantic

## Troubleshooting

**"Authentication failed"**
- For private repos, ensure you have SSH keys set up
- Try using HTTPS URL with personal access token
- Use public repositories for testing

**"Repository not found"**
- Check the URL is correct
- Ensure the repository exists and is accessible

**"No API key found"**
- Add your Anthropic API key to `.streamlit/secrets.toml`
- Or enter it in the UI when prompted

## License

Part of the CodeOrigin project for HackViolet.
