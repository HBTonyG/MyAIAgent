"""
Main agent orchestration logic.

This module handles:
- Loading YAML prompt sequences
- Executing prompt chains with conditional logic
- Coordinating API calls, browser automation, and logging
- Handling session state management
"""

import uuid
import time
from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By
from database import Database
from api_client import APIClient
from browser_automation import BrowserAutomation
from config_parser import ConfigParser
from self_improvement import SelfImprovement
from cursor_integration import CursorIntegration


class Agent:
    """Main agent orchestrator."""
    
    def __init__(self, config_path: str, api_key: str, model: str = "grok-4-latest",
                 brave_path: Optional[str] = None, headless: bool = False):
        """
        Initialize agent.
        
        Args:
            config_path: Path to YAML prompt sequence config
            api_key: Grok (xAI) API key
            model: Model to use (default: grok-4-latest)
            brave_path: Path to Brave browser (optional)
            headless: Run browser in headless mode
        """
        self.config_path = config_path
        self.config_parser = ConfigParser(config_path)
        self.database = Database()
        self.api_client = APIClient(api_key, model=model)
        self.browser = None
        self.brave_path = brave_path
        self.headless = headless
        self.self_improvement = SelfImprovement(self.database, self.api_client)
        self.cursor = CursorIntegration()
        self.session_id = None
        self.is_paused = False
    
    def start_session(self) -> str:
        """
        Start a new agent session.
        
        Returns:
            Session ID
        """
        self.session_id = str(uuid.uuid4())
        self.database.create_session(self.session_id, self.config_path)
        self.is_paused = False
        print(f"Started session: {self.session_id}")
        return self.session_id
    
    def pause_session(self):
        """Pause the current session."""
        if self.session_id:
            self.database.update_session_status(self.session_id, "paused")
            self.is_paused = True
            print(f"Session {self.session_id} paused")
    
    def resume_session(self):
        """Resume a paused session."""
        if self.session_id:
            self.database.update_session_status(self.session_id, "running")
            self.is_paused = False
            print(f"Session {self.session_id} resumed")
    
    def _initialize_browser(self):
        """Initialize browser if not already initialized."""
        if self.browser is None:
            try:
                self.browser = BrowserAutomation(
                    brave_path=self.brave_path,
                    headless=self.headless
                )
                self.database.log_browser_action(
                    self.session_id,
                    "browser_init",
                    {"headless": self.headless},
                    success=True
                )
            except Exception as e:
                self.database.log_error(
                    self.session_id,
                    "browser_init_error",
                    str(e)
                )
                print(f"Browser initialization failed: {str(e)}")
    
    def _execute_browser_actions(self, actions: list):
        """Execute browser actions from prompt configuration."""
        if not self.browser:
            self._initialize_browser()
        
        if not self.browser:
            return
        
        for action in actions:
            action_type = action.get('type')
            action_params = action.get('params', {})
            
            try:
                success = False
                
                if action_type == 'navigate':
                    url = action_params.get('url')
                    if url:
                        success = self.browser.navigate(url)
                
                elif action_type == 'click':
                    selector = action_params.get('selector')
                    by_str = action_params.get('by', 'css').upper()
                    if selector:
                        # Map string to By enum
                        by_map = {
                            'CSS': By.CSS_SELECTOR,
                            'XPATH': By.XPATH,
                            'ID': By.ID,
                            'NAME': By.NAME,
                            'CLASS': By.CLASS_NAME,
                            'TAG': By.TAG_NAME,
                            'LINK_TEXT': By.LINK_TEXT,
                            'PARTIAL_LINK_TEXT': By.PARTIAL_LINK_TEXT
                        }
                        by_value = by_map.get(by_str, By.CSS_SELECTOR)
                        success = self.browser.click_element(selector, by=by_value)
                
                elif action_type == 'type':
                    selector = action_params.get('selector')
                    text = action_params.get('text')
                    if selector and text:
                        success = self.browser.type_text(selector, text)
                
                elif action_type == 'switch_tab':
                    index = action_params.get('index', 0)
                    success = self.browser.switch_tab(index)
                
                elif action_type == 'wait':
                    wait_time = action_params.get('time', 1)
                    time.sleep(wait_time)
                    success = True
                
                elif action_type == 'screenshot':
                    filepath = action_params.get('filepath', f'screenshot_{int(time.time())}.png')
                    success = self.browser.take_screenshot(filepath)
                
                self.database.log_browser_action(
                    self.session_id,
                    action_type,
                    action_params,
                    success
                )
            
            except Exception as e:
                self.database.log_error(
                    self.session_id,
                    "browser_action_error",
                    str(e)
                )
                print(f"Browser action error: {str(e)}")
    
    def _execute_file_operations(self, operations: list, response_text: str):
        """Execute file operations from prompt configuration."""
        for operation in operations:
            op_type = operation.get('type')
            target = operation.get('target')
            extract_code = operation.get('extract_code', False)
            language = operation.get('language', 'python')
            
            try:
                if op_type == 'write':
                    if not target:
                        print("Warning: File operation missing target file")
                        continue
                    
                    if extract_code:
                        # Extract code from response
                        success = self.cursor.apply_code_changes(
                            response_text,
                            target,
                            language
                        )
                    else:
                        # Write full response
                        success = self.cursor.write_file(target, response_text)
                    
                    if success:
                        print(f"✓ Written to file: {target}")
                        self.database.log_browser_action(
                            self.session_id,
                            "file_write",
                            {"file": target, "extracted_code": extract_code},
                            success=True
                        )
                    else:
                        print(f"✗ Failed to write file: {target}")
                        self.database.log_error(
                            self.session_id,
                            "file_write_error",
                            f"Failed to write {target}"
                        )
                
                elif op_type == 'read':
                    # Read file for context (future use)
                    content = self.cursor.read_file(target)
                    if content:
                        self.config_parser.set_variable(f"file_{target}", content)
            
            except Exception as e:
                self.database.log_error(
                    self.session_id,
                    "file_operation_error",
                    str(e)
                )
                print(f"File operation error: {str(e)}")
    
    def run(self) -> bool:
        """
        Run the agent's prompt sequence.
        
        Returns:
            True if completed successfully, False otherwise
        """
        if not self.session_id:
            self.start_session()
        
        try:
            # Get starting prompt
            current_prompt = self.config_parser.get_starting_prompt()
            if not current_prompt:
                print("No prompts found in configuration")
                return False
            
            step_number = 0
            
            while current_prompt and not self.is_paused:
                step_number += 1
                prompt_id = current_prompt.get('id', f'step_{step_number}')
                
                # Execute browser actions before prompt if any
                browser_actions = self.config_parser.get_browser_actions(current_prompt)
                if browser_actions:
                    self._execute_browser_actions(browser_actions)
                
                # Get prompt text with variable substitution
                prompt_text = self.config_parser.get_prompt_text(current_prompt)
                
                # Log prompt
                db_prompt_id = self.database.log_prompt(
                    self.session_id,
                    prompt_text,
                    prompt_id,
                    step_number
                )
                
                print(f"\n[Step {step_number}] Executing prompt: {prompt_id}")
                print(f"Prompt: {prompt_text[:100]}...")
                
                # Send to API
                response = self.api_client.send_prompt(prompt_text)
                
                if response.get('error'):
                    self.database.log_error(
                        self.session_id,
                        "api_error",
                        response['error']
                    )
                    print(f"API Error: {response['error']}")
                    # Continue to next prompt or stop based on error handling strategy
                    break
                
                response_text = response.get('response', '')
                
                # Log response
                self.database.log_response(
                    self.session_id,
                    db_prompt_id,
                    response_text,
                    response.get('model'),
                    response.get('tokens_used')
                )
                
                print(f"Response: {response_text[:200]}...")
                
                # Handle file operations if specified
                file_operations = self.config_parser.get_file_operations(current_prompt)
                if file_operations:
                    self._execute_file_operations(file_operations, response_text)
                
                # Determine next prompt based on conditions
                context = {
                    'step_number': step_number,
                    'response': response_text,
                    'prompt_id': prompt_id
                }
                
                next_prompt_id = self.config_parser.get_next_prompt_id(
                    current_prompt,
                    response_text,
                    context
                )
                
                if next_prompt_id:
                    current_prompt = self.config_parser.get_prompt_by_id(next_prompt_id)
                else:
                    # No next prompt - sequence complete
                    break
            
            # Mark session as completed
            if not self.is_paused:
                self.database.update_session_status(self.session_id, "completed")
                print(f"\nSession {self.session_id} completed")
                
                # Trigger self-improvement analysis
                self._analyze_and_suggest_improvements()
            
            return True
        
        except KeyboardInterrupt:
            print("\nSession interrupted by user")
            self.pause_session()
            return False
        
        except Exception as e:
            self.database.log_error(
                self.session_id,
                "agent_error",
                str(e)
            )
            print(f"Agent error: {str(e)}")
            return False
    
    def _analyze_and_suggest_improvements(self):
        """Analyze completed session and create improvement suggestions."""
        if not self.session_id:
            return
        
        print("\nAnalyzing session for improvements...")
        analysis = self.self_improvement.analyze_session(self.session_id)
        
        if analysis and analysis.get('suggestions'):
            improvement_ids = self.self_improvement.create_improvement_record(
                self.session_id,
                analysis['suggestions']
            )
            print(f"Created {len(improvement_ids)} improvement suggestion(s)")
            print("Review them with: python main.py improvements")
        else:
            print("No improvement suggestions generated")
    
    def close(self):
        """Clean up resources."""
        if self.browser:
            self.browser.close()
        if self.session_id:
            self.database.update_session_status(self.session_id, "completed")
        self.database.close()

