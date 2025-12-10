"""
Project analysis module for scanning and understanding project structure.

This module handles:
- Scanning project directory for code files
- Reading and parsing project structure
- Identifying project type
- Building project context
"""

import os
import glob
from typing import Dict, List, Optional, Any
from pathlib import Path


class ProjectAnalyzer:
    """Analyzes project structure and extracts code context."""
    
    # File patterns for different project types
    FILE_PATTERNS = {
        'website': ['*.html', '*.css', '*.js', '*.jsx', '*.ts', '*.tsx'],
        'python': ['*.py', 'requirements.txt', 'setup.py'],
        'node': ['*.js', '*.ts', 'package.json', '*.json'],
        'general': ['*.py', '*.js', '*.html', '*.css', '*.json']
    }
    
    def __init__(self, project_path: str = "."):
        """
        Initialize project analyzer.
        
        Args:
            project_path: Path to project root directory
        """
        self.project_path = os.path.abspath(project_path)
        self.ignore_patterns = [
            '**/node_modules/**',
            '**/venv/**',
            '**/.git/**',
            '**/__pycache__/**',
            '**/dist/**',
            '**/build/**',
            '**/.env/**',
            '**/*.pyc'
        ]
    
    def scan_project(self, file_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Scan project directory and extract file information.
        
        Args:
            file_patterns: List of file patterns to search for (e.g., ['*.html', '*.css'])
                          If None, auto-detect based on project type
        
        Returns:
            Dictionary with project information
        """
        if file_patterns is None:
            file_patterns = self._detect_file_patterns()
        
        files = {}
        total_files = 0
        
        for pattern in file_patterns:
            # Search recursively
            search_pattern = os.path.join(self.project_path, '**', pattern)
            found_files = glob.glob(search_pattern, recursive=True)
            
            for file_path in found_files:
                # Check if file should be ignored
                if self._should_ignore(file_path):
                    continue
                
                rel_path = os.path.relpath(file_path, self.project_path)
                files[rel_path] = {
                    'full_path': file_path,
                    'relative_path': rel_path,
                    'size': os.path.getsize(file_path),
                    'extension': os.path.splitext(file_path)[1]
                }
                total_files += 1
        
        project_type = self._detect_project_type(files)
        
        return {
            'project_path': self.project_path,
            'project_type': project_type,
            'files': files,
            'file_count': total_files,
            'file_patterns_used': file_patterns
        }
    
    def read_project_files(self, file_paths: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Read contents of project files.
        
        Args:
            file_paths: List of relative file paths to read. If None, reads all scanned files
        
        Returns:
            Dictionary mapping file paths to their contents
        """
        if file_paths is None:
            scan_result = self.scan_project()
            file_paths = list(scan_result['files'].keys())
        
        contents = {}
        
        for rel_path in file_paths:
            full_path = os.path.join(self.project_path, rel_path)
            
            if not os.path.exists(full_path):
                continue
            
            try:
                # Skip binary files
                if self._is_binary_file(full_path):
                    continue
                
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    contents[rel_path] = f.read()
            except Exception as e:
                print(f"Warning: Could not read {rel_path}: {str(e)}")
        
        return contents
    
    def get_project_context(self, max_file_size: int = 100000) -> Dict[str, Any]:
        """
        Get comprehensive project context for AI analysis.
        
        Args:
            max_file_size: Maximum file size to read in bytes (skip larger files)
        
        Returns:
            Dictionary with project context
        """
        scan_result = self.scan_project()
        files = scan_result['files']
        
        # Filter out large files
        readable_files = {
            path: info for path, info in files.items()
            if info['size'] <= max_file_size
        }
        
        # Read file contents
        contents = self.read_project_files(list(readable_files.keys()))
        
        # Get project metadata
        metadata = self._get_project_metadata()
        
        return {
            'project_type': scan_result['project_type'],
            'file_count': scan_result['file_count'],
            'files': {
                path: {
                    'content': contents.get(path, ''),
                    'size': info['size'],
                    'extension': info['extension']
                }
                for path, info in readable_files.items()
            },
            'metadata': metadata
        }
    
    def _detect_project_type(self, files: Dict[str, Any]) -> str:
        """Detect project type based on files present."""
        file_extensions = set()
        file_names = set()
        
        for file_info in files.values():
            ext = file_info.get('extension', '')
            if ext:
                file_extensions.add(ext)
            file_names.add(os.path.basename(file_info['relative_path']))
        
        # Check for key files
        if 'package.json' in file_names:
            return 'node'
        if 'requirements.txt' in file_names or any('.py' in ext for ext in file_extensions):
            if any(ext in ['.html', '.css', '.js'] for ext in file_extensions):
                return 'website'  # Python web project
            return 'python'
        if any(ext in ['.html', '.css', '.js', '.jsx', '.tsx'] for ext in file_extensions):
            return 'website'
        
        return 'general'
    
    def _detect_file_patterns(self) -> List[str]:
        """Auto-detect which file patterns to use."""
        # Quick scan to detect project type
        all_files = []
        for pattern in ['*.html', '*.py', '*.js', 'package.json', 'requirements.txt']:
            search_pattern = os.path.join(self.project_path, '**', pattern)
            all_files.extend(glob.glob(search_pattern, recursive=True))
        
        if not all_files:
            return self.FILE_PATTERNS['general']
        
        # Simple detection
        has_html = any(f.endswith('.html') for f in all_files)
        has_py = any(f.endswith('.py') for f in all_files)
        has_js = any(f.endswith('.js') or f.endswith('.jsx') for f in all_files)
        
        if has_html or (has_js and not has_py):
            return self.FILE_PATTERNS['website']
        elif has_py:
            return self.FILE_PATTERNS['python']
        
        return self.FILE_PATTERNS['general']
    
    def _should_ignore(self, file_path: str) -> bool:
        """Check if file should be ignored."""
        rel_path = os.path.relpath(file_path, self.project_path)
        
        for pattern in self.ignore_patterns:
            if self._match_pattern(rel_path, pattern):
                return True
        
        return False
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Simple pattern matching for ignore patterns."""
        # Convert pattern to regex-like matching
        pattern_parts = pattern.replace('**', '||').split('/')
        path_parts = path.replace('\\', '/').split('/')
        
        # Simple implementation - check if any part matches
        for part in pattern_parts:
            if '||' in part:  # ** wildcard
                return True
            if part and part in path:
                return True
        
        return False
    
    def _is_binary_file(self, file_path: str) -> bool:
        """Check if file is likely binary."""
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
                            '.pdf', '.zip', '.exe', '.dll', '.so', '.bin'}
        ext = os.path.splitext(file_path)[1].lower()
        return ext in binary_extensions
    
    def _get_project_metadata(self) -> Dict[str, Any]:
        """Extract project metadata (package.json, requirements.txt, etc.)."""
        metadata = {}
        
        # Check for package.json
        package_json = os.path.join(self.project_path, 'package.json')
        if os.path.exists(package_json):
            try:
                import json
                with open(package_json, 'r') as f:
                    metadata['package.json'] = json.load(f)
            except:
                pass
        
        # Check for requirements.txt
        requirements = os.path.join(self.project_path, 'requirements.txt')
        if os.path.exists(requirements):
            try:
                with open(requirements, 'r') as f:
                    metadata['requirements'] = f.read().splitlines()
            except:
                pass
        
        # Check for README
        readme_files = ['README.md', 'README.txt', 'README']
        for readme in readme_files:
            readme_path = os.path.join(self.project_path, readme)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        metadata['readme'] = f.read()[:1000]  # First 1000 chars
                    break
                except:
                    pass
        
        return metadata

