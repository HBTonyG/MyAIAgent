"""
Code quality analyzer module.

This module handles:
- Analyzing code quality
- Researching best practices
- Generating quality scores
- Comparing against standards
"""

from typing import Dict, List, Any, Optional
from api_client import APIClient


class QualityAnalyzer:
    """Analyzes code quality and generates improvement suggestions."""
    
    def __init__(self, api_client: APIClient):
        """
        Initialize quality analyzer.
        
        Args:
            api_client: API client for meta-prompting
        """
        self.api_client = api_client
    
    def analyze_project_quality(self, project_context: Dict[str, Any],
                               quality_criteria: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze overall project quality.
        
        Args:
            project_context: Project context from ProjectAnalyzer
            quality_criteria: List of criteria to evaluate (e.g., ['accessibility', 'performance'])
        
        Returns:
            Dictionary with quality scores and analysis
        """
        if quality_criteria is None:
            quality_criteria = ['code_style', 'user_experience', 'performance']
        
        project_type = project_context.get('project_type', 'general')
        files = project_context.get('files', {})
        
        # Build analysis prompt
        file_contents_summary = self._build_file_summary(files)
        
        analysis_prompt = f"""Analyze the quality of this {project_type} project and provide scores (0-100) for each criterion.

Project files:
{file_contents_summary}

Quality criteria to evaluate: {', '.join(quality_criteria)}

For each criterion, provide:
1. A score from 0-100
2. Specific issues found
3. Improvement suggestions

Format your response as JSON:
{{
  "scores": {{
    "accessibility": 75,
    "performance": 60,
    ...
  }},
  "overall_score": 70,
  "issues": [
    {{"criterion": "accessibility", "severity": "high", "description": "..."}},
    ...
  ],
  "improvements": [
    {{"criterion": "accessibility", "priority": "high", "suggestion": "..."}},
    ...
  ]
}}"""

        response = self.api_client.send_prompt(analysis_prompt, temperature=0.3)
        
        if response.get('error'):
            return {
                'overall_score': 0,
                'scores': {},
                'error': response['error']
            }
        
        # Parse response
        return self._parse_quality_response(response.get('response', ''), quality_criteria)
    
    def research_best_practices(self, project_type: str, focus_area: str) -> str:
        """
        Research best practices for a specific area.
        
        Args:
            project_type: Type of project (website, python, etc.)
            focus_area: Area to research (e.g., 'user_experience', 'accessibility')
        
        Returns:
            Research findings as text
        """
        research_prompt = f"""Research and provide best practices for {focus_area} in {project_type} projects.

Focus on:
- Current industry standards
- Common patterns and approaches
- Specific actionable recommendations
- Examples where helpful

Provide a concise summary of key best practices."""

        response = self.api_client.send_prompt(research_prompt, temperature=0.2)
        
        if response.get('error'):
            return f"Error researching best practices: {response['error']}"
        
        return response.get('response', '')
    
    def generate_improvement_suggestions(self, project_context: Dict[str, Any],
                                       quality_analysis: Dict[str, Any],
                                       best_practices: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate specific improvement suggestions.
        
        Args:
            project_context: Project context
            quality_analysis: Results from analyze_project_quality
            best_practices: Optional best practices research
        
        Returns:
            List of improvement suggestions
        """
        scores = quality_analysis.get('scores', {})
        issues = quality_analysis.get('issues', [])
        
        # Find lowest scoring areas
        sorted_criteria = sorted(scores.items(), key=lambda x: x[1])
        priority_areas = [criterion for criterion, score in sorted_criteria[:3]]
        
        suggestions = []
        
        for criterion in priority_areas:
            score = scores.get(criterion, 0)
            if score >= 90:  # Skip if already high
                continue
            
            # Get relevant issues
            criterion_issues = [i for i in issues if i.get('criterion') == criterion]
            
            improvement_prompt = f"""Generate specific, actionable improvement suggestions for a {project_context.get('project_type')} project.

Criterion: {criterion}
Current Score: {score}/100

Issues found:
{self._format_issues(criterion_issues)}

Best Practices:
{best_practices or 'N/A'}

Project files (sample):
{self._build_file_summary(project_context.get('files', {}), max_files=3)}

Provide:
1. Specific code changes needed
2. Files that need modification
3. Expected improvement in score

Format as JSON with actionable suggestions."""

            response = self.api_client.send_prompt(improvement_prompt, temperature=0.4)
            
            if not response.get('error'):
                suggestion = {
                    'criterion': criterion,
                    'current_score': score,
                    'priority': 'high' if score < 60 else 'medium',
                    'suggestion': response.get('response', ''),
                    'issues': criterion_issues
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _build_file_summary(self, files: Dict[str, Any], max_files: int = 10) -> str:
        """Build a summary of project files for analysis."""
        file_list = list(files.items())[:max_files]
        
        summary = []
        for path, info in file_list:
            content = info.get('content', '')[:500]  # First 500 chars
            summary.append(f"\n--- {path} ({info.get('size', 0)} bytes) ---")
            summary.append(content[:500])
        
        if len(files) > max_files:
            summary.append(f"\n... and {len(files) - max_files} more files")
        
        return '\n'.join(summary)
    
    def _format_issues(self, issues: List[Dict[str, Any]]) -> str:
        """Format issues for prompt."""
        if not issues:
            return "No specific issues identified."
        
        formatted = []
        for issue in issues:
            formatted.append(f"- [{issue.get('severity', 'medium')}] {issue.get('description', '')}")
        
        return '\n'.join(formatted)
    
    def _parse_quality_response(self, response_text: str, criteria: List[str]) -> Dict[str, Any]:
        """Parse quality analysis response from API."""
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                
                # Ensure scores exist for all criteria
                scores = data.get('scores', {})
                for criterion in criteria:
                    if criterion not in scores:
                        scores[criterion] = 50  # Default score
                
                return {
                    'overall_score': data.get('overall_score', sum(scores.values()) / len(scores) if scores else 0),
                    'scores': scores,
                    'issues': data.get('issues', []),
                    'improvements': data.get('improvements', []),
                    'raw_response': response_text
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: parse scores manually
        scores = {}
        for criterion in criteria:
            # Look for score in response
            pattern = rf'{criterion}["\']?\s*:?\s*(\d+)'
            match = re.search(pattern, response_text, re.IGNORECASE)
            scores[criterion] = int(match.group(1)) if match else 50
        
        overall = sum(scores.values()) / len(scores) if scores else 0
        
        return {
            'overall_score': overall,
            'scores': scores,
            'issues': [],
            'improvements': [],
            'raw_response': response_text
        }

