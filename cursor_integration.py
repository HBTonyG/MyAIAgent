"""
Cursor IDE integration module.

This module provides integration with Cursor IDE for file editing,
code generation, and project management.
"""

import subprocess
import os
import json
import re
from typing import Optional, Dict, Any, List
import shutil


class CursorIntegration:
    """Integration with Cursor IDE for file operations and code editing."""
    
    def __init__(self, project_path: Optional[str] = None):
        """
        Initialize Cursor integration.
        
        Args:
            project_path: Path to the project root (defaults to current directory)
        """
        self.project_path = project_path or os.getcwd()
        self.cursor_cli_path = self._find_cursor_cli()
    
    def _find_cursor_cli(self) -> Optional[str]:
        """Find Cursor CLI executable."""
        # Check common locations
        paths = [
            shutil.which('cursor'),
            shutil.which('cursor-agent'),
            '/Applications/Cursor.app/Contents/Resources/app/bin/cursor',
            os.path.expanduser('~/.cursor/bin/cursor')
        ]
        
        for path in paths:
            if path and os.path.exists(path):
                return path
        
        return None
    
    def is_available(self) -> bool:
        """Check if Cursor CLI is available."""
        return self.cursor_cli_path is not None
    
    def write_file(self, file_path: str, content: str) -> bool:
        """
        Write content to a file. Cursor will automatically detect the change.
        
        Args:
            file_path: Relative or absolute path to the file
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert relative path to absolute if needed
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.project_path, file_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {str(e)}")
            return False
    
    def read_file(self, file_path: str) -> Optional[str]:
        """
        Read content from a file.
        
        Args:
            file_path: Relative or absolute path to the file
            
        Returns:
            File content or None if error
        """
        try:
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.project_path, file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return None
    
    def extract_code_from_response(self, response_text: str, language: str = "python") -> Optional[str]:
        """
        Extract code blocks from API response.
        
        Args:
            response_text: Response text that may contain code blocks
            language: Programming language (default: python)
            
        Returns:
            Extracted code or None
        """
        # Try to find code blocks in markdown format
        patterns = [
            rf'```{language}\s*\n(.*?)```',
            rf'```\s*\n(.*?)```',
            rf'<code[^>]*>\s*(.*?)\s*</code>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            if matches:
                return matches[0].strip()
        
        # If no code blocks, check if entire response looks like code
        if response_text.strip().startswith(('def ', 'import ', 'class ', 'from ')):
            return response_text.strip()
        
        return None
    
    def execute_cursor_command(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """
        Execute a Cursor CLI command.
        
        Args:
            command: Cursor command to execute
            args: Additional arguments
            
        Returns:
            Dictionary with 'success', 'output', and 'error'
        """
        if not self.cursor_cli_path:
            return {
                'success': False,
                'output': None,
                'error': 'Cursor CLI not found. Install it from https://cursor.com/install'
            }
        
        try:
            cmd = [self.cursor_cli_path, command]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_path,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': None,
                'error': 'Command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'output': None,
                'error': str(e)
            }
    
    def apply_code_changes(self, response_text: str, target_file: str, 
                          language: str = "python") -> bool:
        """
        Extract code from response and write it to a file.
        
        Args:
            response_text: API response containing code
            target_file: Path to file where code should be written
            language: Programming language
            
        Returns:
            True if successful, False otherwise
        """
        code = self.extract_code_from_response(response_text, language)
        
        if not code:
            print(f"Warning: Could not extract code from response")
            # Try writing the raw response anyway
            code = response_text
        
        return self.write_file(target_file, code)
    
    def get_project_context(self, file_patterns: List[str] = None) -> Dict[str, str]:
        """
        Read multiple files to provide context.
        
        Args:
            file_patterns: List of file patterns/paths to read
            
        Returns:
            Dictionary mapping file paths to their contents
        """
        if file_patterns is None:
            file_patterns = ['*.py', 'requirements.txt', 'README.md']
        
        context = {}
        
        # For now, read specific common files
        common_files = [
            'requirements.txt',
            'README.md',
            'main.py',
            'agent.py'
        ]
        
        for file_name in common_files:
            file_path = os.path.join(self.project_path, file_name)
            if os.path.exists(file_path):
                content = self.read_file(file_path)
                if content:
                    context[file_name] = content
        
        return context

