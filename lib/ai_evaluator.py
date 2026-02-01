"""
AI-powered commit evaluation using Claude Sonnet 4.5.

Evaluates commits across 6 dimensions using structured LLM analysis.
"""

import anthropic
import json
import re
from typing import Dict, Any
from .schemas import CommitMetadata, CommitEvaluation


class AIEvaluator:
    """Evaluator for git commits using Claude Sonnet 4.5."""
    
    def __init__(self, api_key: str):
        """
        Initialize the AI evaluator.
        
        Args:
            api_key: Anthropic API key
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def evaluate_commit(self, commit: CommitMetadata, diff: str) -> CommitEvaluation:
        """
        Evaluate a commit using Claude Sonnet 4.5.
        
        Args:
            commit: Commit metadata
            diff: Commit diff text
            
        Returns:
            CommitEvaluation object with scores and analysis
        """
        # Build the evaluation prompt
        prompt = self._build_prompt(commit, diff)
        
        try:
            # Call Anthropic API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.3,  # Lower temperature for more consistent scoring
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract response text
            response_text = ""
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    response_text += content_block.text
            
            # Parse the response
            evaluation = self._parse_response(response_text, commit)
            return evaluation
            
        except anthropic.APIError as e:
            # Handle API errors gracefully
            return self._create_fallback_evaluation(commit, f"API Error: {str(e)}")
        except Exception as e:
            # Handle other errors
            return self._create_fallback_evaluation(commit, f"Error: {str(e)}")
    
    def _build_prompt(self, commit: CommitMetadata, diff: str) -> str:
        """
        Construct the evaluation prompt for the LLM.
        
        Args:
            commit: Commit metadata
            diff: Commit diff
            
        Returns:
            Formatted prompt string
        """
        file_list = "\n".join(f"  - {file}" for file in commit.files_changed[:20])  # Limit to 20 files
        if len(commit.files_changed) > 20:
            file_list += f"\n  ... and {len(commit.files_changed) - 20} more files"
        
        prompt = f"""You are analyzing a code commit to evaluate its contribution across multiple dimensions.

COMMIT INFORMATION:
Hash: {commit.hash[:12]}
Author: {commit.author}
Date: {commit.timestamp}
Message: {commit.message}

FILES CHANGED ({len(commit.files_changed)}):
{file_list}

STATISTICS:
+{commit.insertions} -{commit.deletions} lines

DIFF PREVIEW:
{diff[:3000]}

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

Respond with a JSON object matching this exact schema:
{{
  "technical_complexity": <1-5 integer>,
  "scope_of_impact": <1-5 integer>,
  "code_quality_delta": <1-5 integer>,
  "risk_criticality": <1-5 integer>,
  "knowledge_sharing": <1-5 integer>,
  "innovation": <1-5 integer>,
  "categories": ["category1", "category2"],
  "impact_summary": "1-2 sentence summary of the impact",
  "key_files": ["file1.py", "file2.js"],
  "reasoning": "Detailed justification for the scores, explaining why each dimension received its rating. Be specific and reference the code changes."
}}

Important: Return ONLY the JSON object, no additional text before or after."""

        return prompt
    
    def _parse_response(self, response_text: str, commit: CommitMetadata) -> CommitEvaluation:
        """
        Parse LLM response into CommitEvaluation object.
        
        Args:
            response_text: Raw LLM response
            commit: Original commit metadata
            
        Returns:
            CommitEvaluation object
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                # No JSON found, try parsing whole response
                data = json.loads(response_text)
            
            # Validate and constrain scores to 1-5 range
            for key in ['technical_complexity', 'scope_of_impact', 'code_quality_delta', 
                       'risk_criticality', 'knowledge_sharing', 'innovation']:
                if key in data:
                    data[key] = max(1, min(5, int(data[key])))
            
            # Build CommitEvaluation object
            evaluation = CommitEvaluation(
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
                reasoning=data.get('reasoning', 'No detailed reasoning provided'),
                lines_added=commit.insertions,
                lines_removed=commit.deletions,
                files_changed=len(commit.files_changed)
            )
            
            return evaluation
            
        except json.JSONDecodeError as e:
            # JSON parsing failed
            return self._create_fallback_evaluation(
                commit, 
                f"Failed to parse JSON response: {str(e)}\nResponse: {response_text[:200]}"
            )
        except Exception as e:
            # Other parsing errors
            return self._create_fallback_evaluation(
                commit,
                f"Failed to parse response: {str(e)}"
            )
    
    def _create_fallback_evaluation(self, commit: CommitMetadata, error_msg: str) -> CommitEvaluation:
        """
        Create a fallback evaluation when AI evaluation fails.
        
        Args:
            commit: Commit metadata
            error_msg: Error message
            
        Returns:
            Basic CommitEvaluation with neutral scores
        """
        # Provide neutral scores as fallback
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
            categories=['evaluation_failed'],
            impact_summary=f"Automatic evaluation unavailable. {error_msg}",
            key_files=commit.files_changed[:5],
            reasoning=f"Unable to perform AI evaluation: {error_msg}",
            lines_added=commit.insertions,
            lines_removed=commit.deletions,
            files_changed=len(commit.files_changed)
        )
