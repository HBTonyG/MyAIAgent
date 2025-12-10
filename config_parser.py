"""
YAML configuration parser for prompt sequences with conditional logic.

This module handles:
- Parsing prompt sequences from YAML files
- Evaluating conditional logic (if/then/else)
- Supporting variables and response-based branching
"""

import yaml
from typing import Dict, List, Any, Optional
import re


class ConfigParser:
    """Parser for YAML prompt sequence configurations."""
    
    def __init__(self, config_path: str):
        """
        Initialize config parser.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.variables = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and parse YAML configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config or {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {str(e)}")
    
    def get_prompts(self) -> List[Dict[str, Any]]:
        """Get list of prompts from configuration."""
        return self.config.get('prompts', [])
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific prompt by its ID."""
        prompts = self.get_prompts()
        for prompt in prompts:
            if prompt.get('id') == prompt_id:
                return prompt
        return None
    
    def get_starting_prompt(self) -> Optional[Dict[str, Any]]:
        """Get the starting prompt (first prompt or one marked as 'start')."""
        prompts = self.get_prompts()
        if not prompts:
            return None
        
        # Look for prompt marked as start
        for prompt in prompts:
            if prompt.get('start', False):
                return prompt
        
        # Return first prompt
        return prompts[0]
    
    def evaluate_condition(self, condition: str, response: str, 
                          context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Evaluate a conditional expression.
        
        Supported conditions:
        - "response contains 'text'" - Check if response contains text
        - "response not contains 'text'" - Check if response doesn't contain text
        - "response length > 100" - Compare response length
        - "variable_name == 'value'" - Compare variable value
        
        Args:
            condition: Condition string to evaluate
            response: Current response text
            context: Optional context dictionary
            
        Returns:
            True if condition is met, False otherwise
        """
        condition = condition.strip()
        
        # Response contains check
        if "response contains" in condition.lower():
            match = re.search(r"response contains ['\"](.+?)['\"]", condition, re.IGNORECASE)
            if match:
                text = match.group(1)
                return text.lower() in response.lower()
        
        # Response not contains check
        if "response not contains" in condition.lower():
            match = re.search(r"response not contains ['\"](.+?)['\"]", condition, re.IGNORECASE)
            if match:
                text = match.group(1)
                return text.lower() not in response.lower()
        
        # Response length comparison
        if "response length" in condition.lower():
            if ">" in condition:
                match = re.search(r"response length > (\d+)", condition, re.IGNORECASE)
                if match:
                    length = int(match.group(1))
                    return len(response) > length
            elif "<" in condition:
                match = re.search(r"response length < (\d+)", condition, re.IGNORECASE)
                if match:
                    length = int(match.group(1))
                    return len(response) < length
        
        # Variable comparison
        if "==" in condition:
            parts = condition.split("==")
            if len(parts) == 2:
                var_name = parts[0].strip()
                var_value = parts[1].strip().strip("'\"")
                if var_name in self.variables:
                    return str(self.variables[var_name]) == var_value
        
        # Default: return False for unknown conditions
        return False
    
    def get_next_prompt_id(self, current_prompt: Dict[str, Any], 
                           response: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Determine the next prompt ID based on conditions.
        
        Args:
            current_prompt: Current prompt dictionary
            response: Response from current prompt
            context: Optional context dictionary
            
        Returns:
            Next prompt ID or None if no conditions match
        """
        conditions = current_prompt.get('conditions', [])
        
        for condition in conditions:
            if_condition = condition.get('if')
            then_action = condition.get('then')
            else_action = condition.get('else')
            
            if if_condition:
                if self.evaluate_condition(if_condition, response, context):
                    return then_action
                elif else_action:
                    return else_action
        
        # If no conditions match, check for default next
        next_id = current_prompt.get('next')
        if next_id:
            return next_id
        
        # Check for sequential next (next prompt in list)
        prompts = self.get_prompts()
        current_index = None
        for i, prompt in enumerate(prompts):
            if prompt.get('id') == current_prompt.get('id'):
                current_index = i
                break
        
        if current_index is not None and current_index + 1 < len(prompts):
            return prompts[current_index + 1].get('id')
        
        return None
    
    def set_variable(self, name: str, value: Any):
        """Set a variable for use in conditions."""
        self.variables[name] = value
    
    def get_variable(self, name: str) -> Any:
        """Get a variable value."""
        return self.variables.get(name)
    
    def substitute_variables(self, text: str) -> str:
        """
        Substitute variables in text using {{variable_name}} syntax.
        
        Args:
            text: Text with variable placeholders
            
        Returns:
            Text with variables substituted
        """
        def replace_var(match):
            var_name = match.group(1)
            return str(self.variables.get(var_name, match.group(0)))
        
        return re.sub(r'\{\{(\w+)\}\}', replace_var, text)
    
    def get_prompt_text(self, prompt: Dict[str, Any]) -> str:
        """
        Get prompt text with variable substitution.
        
        Args:
            prompt: Prompt dictionary
            
        Returns:
            Prompt text with variables substituted
        """
        prompt_text = prompt.get('prompt', '')
        return self.substitute_variables(prompt_text)
    
    def get_browser_actions(self, prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get browser actions for a prompt if any."""
        return prompt.get('browser_actions', [])
    
    def get_file_operations(self, prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get file operations for a prompt if any.
        
        Expected format:
        file_operations:
          - type: "write"
            target: "output/scraper.py"
            extract_code: true
            language: "python"
        """
        return prompt.get('file_operations', [])
    
    def reload(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        self.variables = {}

