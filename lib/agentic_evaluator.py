"""
Agentic Commit Evaluator

AI-powered commit evaluation with autonomous context gathering using Claude with tool use.
"""

import anthropic
import json
from typing import Dict, Any, Callable, Optional
from .schemas import CommitMetadata, CommitEvaluation
from .git_handler import GitHandler
from .tool_registry import ToolRegistry, GLOBAL_LIMITS
from .tool_executor import ToolExecutor, LimitExceededError


class AgenticEvaluator:
    """Evaluates commits using an AI agent with tool-use capabilities."""

    def __init__(self, api_key: str, git_handler: GitHandler):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.git_handler = git_handler

        # Initialize components
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(git_handler)

    def evaluate_commit(
        self,
        commit: CommitMetadata,
        diff: str,
        ui_callback: Optional[Callable] = None
    ) -> CommitEvaluation:
        """
        Evaluate a commit using agentic context gathering.

        Args:
            commit: Commit metadata
            diff: Commit diff
            ui_callback: Optional callback for UI updates

        Returns:
            CommitEvaluation with scores and analysis
        """

        # Start tool execution session
        self.tool_executor.start_session()

        try:
            # Phase 1: Agentic context gathering with tool use
            context = self._gather_context_with_agent(commit, diff, ui_callback)

            # Phase 2: Final evaluation with gathered context
            evaluation = self._final_evaluation(commit, diff, context, ui_callback)

            return evaluation

        except LimitExceededError as e:
            # Limits exceeded - fall back to basic evaluation
            if ui_callback:
                ui_callback({
                    "event": "agent_thinking",
                    "message": f"Limit exceeded: {e}. Using basic evaluation..."
                })

            return self._create_basic_evaluation(commit, diff, str(e))

        except Exception as e:
            # Other error - fall back to basic evaluation
            if ui_callback:
                ui_callback({
                    "event": "agent_thinking",
                    "message": f"Error: {e}. Using basic evaluation..."
                })

            return self._create_basic_evaluation(commit, diff, str(e))

    def _gather_context_with_agent(
        self,
        commit: CommitMetadata,
        diff: str,
        ui_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Use Claude with tool use to gather additional context."""

        if ui_callback:
            ui_callback({
                "event": "agent_thinking",
                "message": "Agent analyzing commit and determining context needs..."
            })

        # Build initial prompt for agent
        initial_prompt = self._build_context_gathering_prompt(commit, diff)

        # Get tool schemas for Claude
        tool_schemas = self.tool_registry.get_anthropic_tool_schemas()

        # Agentic loop with tool use
        messages = [{"role": "user", "content": initial_prompt}]
        gathered_context = []
        max_iterations = GLOBAL_LIMITS['max_iterations']

        for iteration in range(max_iterations):
            try:
                # Call Claude with tools
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.3,
                    tools=tool_schemas,
                    messages=messages
                )

                # Check if agent wants to use tools
                if response.stop_reason == "tool_use":
                    # Process tool use requests
                    tool_results = []

                    for content_block in response.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input

                            if ui_callback:
                                ui_callback({
                                    "event": "agent_thinking",
                                    "message": f"Agent decided to use: {tool_name}"
                                })

                            # Execute tool
                            try:
                                result = self.tool_executor.execute_tool(
                                    tool_name,
                                    tool_input,
                                    ui_callback=ui_callback
                                )

                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": content_block.id,
                                    "content": json.dumps(result, default=str)
                                })

                                # Store context
                                gathered_context.append({
                                    "tool": tool_name,
                                    "input": tool_input,
                                    "output": result
                                })

                            except Exception as e:
                                # Tool execution failed
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": content_block.id,
                                    "content": f"Error: {str(e)}",
                                    "is_error": True
                                })

                    # Add assistant response and tool results to conversation
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})

                elif response.stop_reason == "end_turn":
                    # Agent finished gathering context
                    if ui_callback:
                        ui_callback({
                            "event": "agent_thinking",
                            "message": "Agent finished context gathering"
                        })
                    break

                else:
                    # Unexpected stop reason
                    break

            except anthropic.APIError as e:
                if ui_callback:
                    ui_callback({
                        "event": "agent_thinking",
                        "message": f"API Error: {str(e)}"
                    })
                break

        return {
            "gathered_context": gathered_context,
            "tool_usage": self.tool_executor.get_usage_summary()
        }

    def _final_evaluation(
        self,
        commit: CommitMetadata,
        diff: str,
        context: Dict[str, Any],
        ui_callback: Optional[Callable]
    ) -> CommitEvaluation:
        """Perform final evaluation with gathered context."""

        if ui_callback:
            ui_callback({
                "event": "agent_thinking",
                "message": "Performing final evaluation with gathered context..."
            })

        # Build evaluation prompt with context
        eval_prompt = self._build_evaluation_prompt(commit, diff, context)

        try:
            # Call Claude for final evaluation (no tools)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.3,
                messages=[{"role": "user", "content": eval_prompt}]
            )

            # Extract response text
            response_text = ""
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    response_text += content_block.text

            # Parse evaluation
            evaluation = self._parse_evaluation(response_text, commit)

            if ui_callback:
                ui_callback({"event": "agent_complete"})

            return evaluation

        except Exception as e:
            return self._create_basic_evaluation(commit, diff, f"Evaluation failed: {str(e)}")

    def _build_context_gathering_prompt(self, commit: CommitMetadata, diff: str) -> str:
        """Build prompt for context gathering phase."""

        file_list = "\n".join(f"  - {file}" for file in commit.files_changed[:20])
        if len(commit.files_changed) > 20:
            file_list += f"\n  ... and {len(commit.files_changed) - 20} more files"

        return f"""You are analyzing a git commit to evaluate its contribution quality. You have access to tools to gather additional context about the codebase and related commits.

COMMIT INFORMATION:
Hash: {commit.hash[:12]}
Author: {commit.author}
Date: {commit.timestamp}
Message: {commit.message}

FILES CHANGED ({len(commit.files_changed)}):
{file_list}

STATISTICS:
+{commit.insertions} -{commit.deletions} lines

DIFF PREVIEW (first 2000 chars):
{diff[:2000]}

YOUR TASK:
Decide if you need additional context to accurately evaluate this commit. You can use the available tools to:
- Check the history of modified files
- Read file contents to understand context
- Find related commits
- Search for patterns or definitions
- Explore the codebase structure

GUIDELINES:
1. Not every commit needs additional context - simple changes (typos, formatting) don't require tools
2. Use tools strategically - you have usage limits
3. Focus on gathering context that will meaningfully improve evaluation accuracy
4. When you have sufficient context, stop gathering and indicate you're done

If you need additional context, use the available tools. When you're done gathering context (or if you don't need any), just respond with "CONTEXT_GATHERING_COMPLETE".

What context do you need to evaluate this commit?"""

    def _build_evaluation_prompt(
        self,
        commit: CommitMetadata,
        diff: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for final evaluation with gathered context."""

        file_list = "\n".join(f"  - {file}" for file in commit.files_changed[:20])
        if len(commit.files_changed) > 20:
            file_list += f"\n  ... and {len(commit.files_changed) - 20} more files"

        # Format gathered context
        context_summary = ""
        if context.get('gathered_context'):
            context_summary = "\n\nGATHERED CONTEXT:\n"
            for item in context['gathered_context']:
                tool_name = item['tool']
                output = item['output']
                context_summary += f"\n{tool_name}:\n{json.dumps(output, indent=2, default=str)[:1000]}\n"

        return f"""You are evaluating a git commit across 6 dimensions.

COMMIT INFORMATION:
Hash: {commit.hash[:12]}
Author: {commit.author}
Date: {commit.timestamp}
Message: {commit.message}

FILES CHANGED ({len(commit.files_changed)}):
{file_list}

STATISTICS:
+{commit.insertions} -{commit.deletions} lines

DIFF:
{diff[:3000]}{context_summary}

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
- Categorize the commit (bug_fix, feature, refactor, security, testing, documentation, performance, infrastructure, etc.)
- Summarize the impact in 1-2 sentences
- List the most important files changed (max 5)
- Provide detailed reasoning for your scores

Respond with ONLY a JSON object:
{{
  "technical_complexity": <1-5>,
  "scope_of_impact": <1-5>,
  "code_quality_delta": <1-5>,
  "risk_criticality": <1-5>,
  "knowledge_sharing": <1-5>,
  "innovation": <1-5>,
  "categories": ["category1", "category2"],
  "impact_summary": "summary",
  "key_files": ["file1", "file2"],
  "reasoning": "detailed reasoning"
}}"""

    def _parse_evaluation(self, response_text: str, commit: CommitMetadata) -> CommitEvaluation:
        """Parse LLM response into CommitEvaluation."""

        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                data = json.loads(response_text)

            # Validate and constrain scores
            for key in ['technical_complexity', 'scope_of_impact', 'code_quality_delta',
                       'risk_criticality', 'knowledge_sharing', 'innovation']:
                if key in data:
                    data[key] = max(1, min(5, int(data[key])))

            # Build evaluation object
            return CommitEvaluation(
                commit_hash=commit.hash,
                author=commit.author,
                email=commit.email,
                timestamp=commit.timestamp,
                message=commit.message,
                technical_complexity=data.get('technical_complexity', 3),
                scope_of_impact=data.get('scope_of_impact', 3),
                code_quality_delta=data.get('code_quality_delta', 3),
                risk_criticality=data.get('risk_criticality', 3),
                knowledge_sharing=data.get('knowledge_sharing', 3),
                innovation=data.get('innovation', 3),
                categories=data.get('categories', ['unknown']),
                impact_summary=data.get('impact_summary', 'No summary provided'),
                key_files=data.get('key_files', commit.files_changed[:5]),
                reasoning=data.get('reasoning', 'No reasoning provided'),
                lines_added=commit.insertions,
                lines_removed=commit.deletions,
                files_changed=len(commit.files_changed)
            )

        except Exception as e:
            return self._create_basic_evaluation(commit, "", f"Failed to parse: {str(e)}")

    def _create_basic_evaluation(
        self,
        commit: CommitMetadata,
        diff: str,
        error_msg: str
    ) -> CommitEvaluation:
        """Create fallback evaluation when agentic evaluation fails."""

        return CommitEvaluation(
            commit_hash=commit.hash,
            author=commit.author,
            email=commit.email,
            timestamp=commit.timestamp,
            message=commit.message,
            technical_complexity=3,
            scope_of_impact=3,
            code_quality_delta=3,
            risk_criticality=3,
            knowledge_sharing=3,
            innovation=3,
            categories=['evaluation_incomplete'],
            impact_summary=f"Agentic evaluation unavailable: {error_msg}",
            key_files=commit.files_changed[:5],
            reasoning=f"Used fallback evaluation due to: {error_msg}",
            lines_added=commit.insertions,
            lines_removed=commit.deletions,
            files_changed=len(commit.files_changed)
        )
