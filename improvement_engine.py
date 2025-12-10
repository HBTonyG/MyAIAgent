"""
Iterative improvement engine.

This module handles:
- Automatic iteration loops
- Quality threshold management
- Applying improvements to files
- Progress tracking
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from project_analyzer import ProjectAnalyzer
from quality_analyzer import QualityAnalyzer
from cursor_integration import CursorIntegration
from database import Database
from api_client import APIClient, TokenBudgetExceeded


class ImprovementEngine:
    """Manages iterative code improvement process."""
    
    def __init__(self, api_client: APIClient, database: Database,
                 project_path: str = "."):
        """
        Initialize improvement engine.
        
        Args:
            api_client: API client for code generation
            database: Database instance for tracking
            project_path: Path to project root
        """
        self.api_client = api_client
        self.database = database
        self.project_path = project_path
        self.project_analyzer = ProjectAnalyzer(project_path)
        self.quality_analyzer = QualityAnalyzer(api_client)
        self.cursor = CursorIntegration(project_path)
    
    def run_improvement_loop(self, session_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run iterative improvement loop.
        
        Args:
            session_id: Session identifier
            config: Configuration dictionary with quality/iteration settings
        
        Returns:
            Dictionary with final results
        """
        quality_config = config.get('quality', {})
        iteration_config = config.get('iteration', {})
        
        threshold = quality_config.get('threshold', 85)
        max_iterations = iteration_config.get('max_iterations', 5)
        criteria = quality_config.get('criteria', ['code_style', 'user_experience'])
        
        results = {
            'session_id': session_id,
            'iterations': [],
            'final_score': 0,
            'threshold_met': False,
            'converged': False,
            'budget_exceeded': False
        }
        
        previous_score = 0
        convergence_count = 0
        convergence_threshold = iteration_config.get('convergence_threshold', 2)
        
        # Display token budget info if set
        if self.api_client.max_tokens:
            print(f"Token Budget: {self.api_client.max_tokens:,} tokens")
            print(f"Warning threshold: {self.api_client.warning_threshold*100:.0f}%")
        
        for iteration in range(1, max_iterations + 1):
            print(f"\n{'='*60}")
            print(f"Iteration {iteration}/{max_iterations}")
            print(f"{'='*60}")
            
            # Analyze current project
            print("Analyzing project...")
            project_context = self.project_analyzer.get_project_context()
            
            # Assess quality
            print("Assessing quality...")
            quality_analysis = self.quality_analyzer.analyze_project_quality(
                project_context,
                criteria
            )
            
            current_score = quality_analysis.get('overall_score', 0)
            
            # Save quality score
            self.database.save_quality_score(
                session_id,
                iteration,
                current_score,
                json.dumps(quality_analysis.get('scores', {}))
            )
            
            print(f"Current Quality Score: {current_score}/100 (Target: {threshold})")
            
            # Check if threshold met
            if current_score >= threshold:
                results['final_score'] = current_score
                results['threshold_met'] = True
                print(f"\n✓ Quality threshold met! ({current_score} >= {threshold})")
                break
            
            # Check convergence
            score_change = abs(current_score - previous_score)
            if score_change < 2:  # Less than 2 point change
                convergence_count += 1
                if convergence_count >= convergence_threshold:
                    results['final_score'] = current_score
                    results['converged'] = True
                    print(f"\n✓ Improvement converged (no significant change for {convergence_count} iterations)")
                    break
            else:
                convergence_count = 0
            
            # Generate improvements
            print("Generating improvements...")
            try:
                best_practices = None
                if iteration == 1:  # Research best practices on first iteration
                    print("Researching best practices...")
                    project_type = project_context.get('project_type', 'general')
                    best_practices = self.quality_analyzer.research_best_practices(
                        project_type,
                        criteria[0] if criteria else 'user_experience'
                    )
                
                suggestions = self.quality_analyzer.generate_improvement_suggestions(
                    project_context,
                    quality_analysis,
                    best_practices
                )
            except TokenBudgetExceeded as e:
                print(f"\n✗ Token budget exceeded: {str(e)}")
                results['budget_exceeded'] = True
                results['final_score'] = current_score
                print(f"Session stopped. Final score: {current_score}/100")
                print(f"Total tokens used: {self.api_client.tokens_used_session:,}/{self.api_client.max_tokens:,}")
                break
            
            if not suggestions:
                print("No improvement suggestions generated.")
                break
            
            # Apply improvements
            print("Applying improvements...")
            files_modified = []
            
            for suggestion in suggestions[:3]:  # Limit to top 3 per iteration
                improvement_text = suggestion.get('suggestion', '')
                
                # Extract code and file info from suggestion
                modified_files = self._apply_improvement(
                    improvement_text,
                    project_context
                )
                
                files_modified.extend(modified_files)
            
            # Save iteration record
            self.database.save_iteration(
                session_id,
                iteration,
                previous_score,
                current_score,
                json.dumps([s.get('criterion') for s in suggestions]),
                json.dumps(list(set(files_modified)))
            )
            
            iteration_result = {
                'iteration': iteration,
                'score_before': previous_score,
                'score_after': current_score,
                'improvements': len(suggestions),
                'files_modified': files_modified
            }
            results['iterations'].append(iteration_result)
            
            previous_score = current_score
            
            # Display token usage for this iteration
            if self.api_client.max_tokens:
                remaining = self.api_client.get_remaining_tokens()
                usage_pct = (self.api_client.tokens_used_session / self.api_client.max_tokens) * 100
                print(f"Iteration {iteration} complete. Score: {previous_score} -> {current_score}")
                print(f"Token usage: {self.api_client.tokens_used_session:,}/{self.api_client.max_tokens:,} "
                      f"({usage_pct:.1f}%) - {remaining:,} remaining")
            else:
                print(f"Iteration {iteration} complete. Score: {previous_score} -> {current_score}")
        
        # Display final token usage
        if self.api_client.max_tokens:
            print(f"\n{'='*60}")
            print(f"Final Token Usage: {self.api_client.tokens_used_session:,}/{self.api_client.max_tokens:,} tokens")
            usage_pct = (self.api_client.tokens_used_session / self.api_client.max_tokens) * 100
            print(f"Usage: {usage_pct:.1f}%")
        
        results['final_score'] = previous_score
        return results
    
    def _apply_improvement(self, improvement_text: str,
                          project_context: Dict[str, Any]) -> List[str]:
        """
        Apply an improvement suggestion to project files.
        
        Args:
            improvement_text: Improvement suggestion from AI
            project_context: Current project context
        
        Returns:
            List of modified file paths
        """
        modified_files = []
        
        # Try to extract file paths and code from improvement text
        files = project_context.get('files', {})
        
        # Ask AI to generate the actual code changes
        prompt = f"""Based on this improvement suggestion, provide the actual code changes needed.

Improvement Suggestion:
{improvement_text[:1000]}

Current Project Files:
{self._format_files_for_prompt(files)}

Provide the updated code for files that need changes. Format as:
FILE: path/to/file.ext
```language
// updated code here
```

Only include files that actually need changes."""

        response = self.api_client.send_prompt(prompt, temperature=0.3)
        
        if response.get('error'):
            print(f"Error generating code changes: {response['error']}")
            return modified_files
        
        # Parse and apply code changes
        code_blocks = self._extract_file_code_blocks(response.get('response', ''))
        
        for file_path, code in code_blocks.items():
            # Resolve file path - handle both absolute and relative
            if os.path.isabs(file_path):
                # If absolute, check if it's within project
                if not file_path.startswith(self.project_path):
                    # Make relative to project
                    full_path = os.path.join(self.project_path, os.path.basename(file_path))
                else:
                    full_path = file_path
            else:
                full_path = os.path.join(self.project_path, file_path)
            
            # Create directory if needed
            dir_path = os.path.dirname(full_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            if self.cursor.write_file(full_path, code):
                rel_path = os.path.relpath(full_path, self.project_path)
                modified_files.append(rel_path)
                print(f"  ✓ Updated: {rel_path}")
        
        return modified_files
    
    def _format_files_for_prompt(self, files: Dict[str, Any], max_files: int = 5) -> str:
        """Format file contents for prompt."""
        formatted = []
        count = 0
        
        for path, info in files.items():
            if count >= max_files:
                break
            content = info.get('content', '')[:800]  # Limit content
            formatted.append(f"\n--- {path} ---\n{content}")
            count += 1
        
        return '\n'.join(formatted)
    
    def _extract_file_code_blocks(self, response_text: str) -> Dict[str, str]:
        """Extract file paths and code blocks from AI response."""
        import os
        
        file_code_map = {}
        
        # Pattern: FILE: path/to/file
        file_pattern = r'FILE:\s*(.+?)(?:\n|$)'
        code_block_pattern = r'```(?:\w+)?\s*\n(.*?)```'
        
        # Find all FILE: declarations
        file_matches = list(re.finditer(file_pattern, response_text, re.MULTILINE))
        
        for i, file_match in enumerate(file_matches):
            file_path = file_match.group(1).strip()
            
            # Find code block after this FILE declaration
            start_pos = file_match.end()
            next_file_pos = file_matches[i + 1].start() if i + 1 < len(file_matches) else len(response_text)
            
            code_section = response_text[start_pos:next_file_pos]
            code_match = re.search(code_block_pattern, code_section, re.DOTALL)
            
            if code_match:
                code = code_match.group(1).strip()
                file_code_map[file_path] = code
        
        return file_code_map


# Add missing import
import os

