"""
Meta-prompting system for self-improvement.

This module handles:
- Analyzing logs after each run
- Generating optimization suggestions
- Applying changes to YAML configs (only, not Python code)
- User approval workflow
"""

import json
from typing import Dict, List, Any, Optional
from database import Database
from api_client import APIClient
from config_parser import ConfigParser


class SelfImprovement:
    """Meta-prompting system for agent self-improvement."""
    
    def __init__(self, database: Database, api_client: APIClient):
        """
        Initialize self-improvement system.
        
        Args:
            database: Database instance for log access
            api_client: API client for meta-prompting
        """
        self.database = database
        self.api_client = api_client
    
    def analyze_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a completed session and generate improvement suggestions.
        
        Args:
            session_id: Session ID to analyze
            
        Returns:
            Dictionary with improvement suggestions or None if analysis fails
        """
        # Get session logs
        logs = self.database.get_session_logs(session_id)
        
        if not logs:
            return None
        
        # Format logs for analysis
        log_summary = self._format_logs_for_analysis(logs)
        
        # Create meta-prompt
        meta_prompt = self._create_analysis_prompt()
        
        # Send to API
        response = self.api_client.send_meta_prompt(meta_prompt, log_summary)
        
        if response.get('error'):
            print(f"Error in meta-prompting: {response['error']}")
            return None
        
        # Parse improvement suggestions
        suggestions = self._parse_suggestions(response.get('response', ''))
        
        return {
            'session_id': session_id,
            'suggestions': suggestions,
            'raw_response': response.get('response')
        }
    
    def _format_logs_for_analysis(self, logs: List[Dict[str, Any]]) -> str:
        """Format logs into a readable summary for analysis."""
        summary_lines = []
        summary_lines.append("=== Session Log Summary ===\n")
        
        for i, log in enumerate(logs, 1):
            summary_lines.append(f"\n--- Step {i} ---")
            summary_lines.append(f"Prompt ID: {log.get('config_prompt_id', 'N/A')}")
            summary_lines.append(f"Prompt: {log.get('prompt_text', '')[:200]}...")
            if log.get('response_text'):
                summary_lines.append(f"Response: {log.get('response_text', '')[:300]}...")
            summary_lines.append(f"Tokens: {log.get('tokens_used', 'N/A')}")
        
        return "\n".join(summary_lines)
    
    def _create_analysis_prompt(self) -> str:
        """Create the meta-prompt for log analysis."""
        return """You are analyzing logs from an AI agent that executes prompt sequences defined in YAML configuration files.

Your task is to:
1. Identify inefficiencies in the prompt sequence
2. Suggest improvements to prompt wording for better results
3. Recommend better conditional logic or branching
4. Suggest optimizations to reduce token usage
5. Identify patterns that could be improved

IMPORTANT: You can ONLY suggest changes to YAML configuration files. Do NOT suggest changes to Python code.

Provide your suggestions in the following JSON format:
{
  "improvements": [
    {
      "type": "config_update",
      "description": "Brief description of the improvement",
      "target_file": "config/prompts.yaml",
      "changes": {
        "prompt_id": "step1",
        "field": "prompt",
        "new_value": "Improved prompt text here"
      }
    }
  ]
}

If suggesting changes to conditions, use:
{
  "type": "config_update",
  "description": "Better conditional logic",
  "target_file": "config/prompts.yaml",
  "changes": {
    "prompt_id": "step1",
    "field": "conditions",
    "new_value": [{"if": "response contains 'success'", "then": "step2"}]
  }
}

Be specific and actionable. Focus on improvements that will make the agent more effective."""
    
    def _parse_suggestions(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse improvement suggestions from API response."""
        suggestions = []
        
        # Try to extract JSON from response
        try:
            # Look for JSON block in markdown code fences
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text
            
            data = json.loads(json_str)
            improvements = data.get('improvements', [])
            
            for improvement in improvements:
                if improvement.get('type') == 'config_update':
                    suggestions.append(improvement)
        
        except json.JSONDecodeError:
            # If JSON parsing fails, create a generic suggestion
            suggestions.append({
                'type': 'config_update',
                'description': 'Review and optimize prompt sequence based on analysis',
                'target_file': 'config/prompts.yaml',
                'changes': {
                    'note': 'Manual review required - could not parse structured suggestions',
                    'raw_analysis': response_text[:500]
                }
            })
        
        return suggestions
    
    def create_improvement_record(self, session_id: str, 
                                 suggestions: List[Dict[str, Any]]) -> List[int]:
        """
        Create improvement records in database.
        
        Args:
            session_id: Session ID
            suggestions: List of improvement suggestions
            
        Returns:
            List of improvement database IDs
        """
        improvement_ids = []
        
        for suggestion in suggestions:
            improvement_id = self.database.create_improvement(
                session_id=session_id,
                improvement_type=suggestion.get('type', 'config_update'),
                description=suggestion.get('description', 'Improvement suggestion'),
                suggested_changes=suggestion
            )
            improvement_ids.append(improvement_id)
        
        return improvement_ids
    
    def apply_improvement(self, improvement_id: int, 
                         config_parser: ConfigParser) -> bool:
        """
        Apply an approved improvement to a YAML config file.
        
        Args:
            improvement_id: Improvement database ID
            config_parser: ConfigParser instance for the target config
            
        Returns:
            True if successful, False otherwise
        """
        improvement = self.database.get_improvement(improvement_id)
        
        if not improvement or improvement['status'] != 'approved':
            return False
        
        try:
            changes = json.loads(improvement['suggested_changes'])
            change_data = changes.get('changes', {})
            
            # Reload config to get fresh copy
            config_parser.reload()
            config = config_parser.config
            
            # Find and update the prompt
            prompt_id = change_data.get('prompt_id')
            field = change_data.get('field')
            new_value = change_data.get('new_value')
            
            if prompt_id and field and new_value is not None:
                prompts = config.get('prompts', [])
                for prompt in prompts:
                    if prompt.get('id') == prompt_id:
                        prompt[field] = new_value
                        break
                
                # Write updated config back to file
                import yaml
                with open(config_parser.config_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                
                # Mark improvement as applied
                self.database.approve_improvement(improvement_id)
                return True
        
        except Exception as e:
            print(f"Error applying improvement: {str(e)}")
            return False
        
        return False

