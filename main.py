#!/usr/bin/env python3
"""
CLI interface for the self-improving AI agent.

SETUP INSTRUCTIONS:
===================

1. Install dependencies:
   pip install -r requirements.txt

2. Browser Setup (optional):
   - Install Brave browser if using browser automation
   - ChromeDriver is automatically managed by Selenium - no installation needed!

3. Set Grok (xAI) API key:
   export GROK_API_KEY="your-api-key-here"
   Or export XAI_API_KEY="your-api-key-here"
   Or add to config/agent_config.yaml

4. Run the agent:
   python main.py start config/prompts.yaml

Commands:
- start [config_file] - Start agent session
- logs [--limit N] - View recent logs
- improvements - Review pending improvements
- approve [improvement_id] - Approve and apply improvement
- reject [improvement_id] - Reject improvement
- pause - Pause current session
- resume - Resume paused session
"""

import argparse
import sys
import os
from typing import Optional
from agent import Agent
from database import Database
from config_parser import ConfigParser
from improvement_engine import ImprovementEngine
from api_client import APIClient


def _find_myaiagent_dir():
    """
    Find MyAIAgent installation directory.
    Works for both installed package and direct script execution.
    """
    # Try to find config directory using sysconfig (for installed packages)
    try:
        import sysconfig
        # Get site-packages or user site-packages where package is installed
        for scheme in ['purelib', 'platlib']:
            try:
                site_packages = sysconfig.get_paths()[scheme]
                # Check for config directory in site-packages
                config_path = os.path.join(site_packages, 'config')
                if os.path.exists(config_path):
                    # Return the parent directory (site-packages root)
                    return site_packages
            except:
                continue
    except Exception:
        pass
    
    # Try to find via importlib (for editable installs)
    try:
        import importlib.util
        spec = importlib.util.find_spec('main')
        if spec and spec.origin:
            main_dir = os.path.dirname(os.path.abspath(spec.origin))
            # Check if config directory exists relative to main module
            config_path = os.path.join(main_dir, 'config')
            if os.path.exists(config_path):
                return main_dir
    except Exception:
        pass
    
    # Fallback: Use __file__ location (direct script execution)
    main_py_path = os.path.abspath(__file__)
    return os.path.dirname(main_py_path)


def load_config() -> dict:
    """Load agent configuration from config file or environment."""
    config = {
        'api_key': os.getenv('GROK_API_KEY') or os.getenv('XAI_API_KEY'),
        'brave_path': os.getenv('BRAVE_BROWSER_PATH'),
        'headless': os.getenv('HEADLESS', 'false').lower() == 'true',
        'default_config': 'config/prompts.yaml',
        'model': os.getenv('GROK_MODEL', 'grok-4-latest')
    }
    
    # Try to load from agent_config.yaml (relative to package directory)
    myaiagent_dir = _find_myaiagent_dir()
    agent_config_path = os.path.join(myaiagent_dir, 'config', 'agent_config.yaml')
    
    # Also check current directory (user override)
    if os.path.exists('config/agent_config.yaml'):
        agent_config_path = 'config/agent_config.yaml'
    elif os.path.exists(agent_config_path):
        pass  # Use package config
    else:
        agent_config_path = None
    
    if agent_config_path and os.path.exists(agent_config_path):
        import yaml
        with open(agent_config_path, 'r') as f:
            file_config = yaml.safe_load(f) or {}
            config.update(file_config)
    
    return config


def cmd_start(args):
    """Start an agent session."""
    config = load_config()
    
    if not config.get('api_key'):
        print("Error: GROK_API_KEY or XAI_API_KEY not set. Set it as environment variable or in config/agent_config.yaml")
        sys.exit(1)
    
    config_file = args.config_file or config.get('default_config', 'config/prompts.yaml')
    
    # Resolve config file path - check current directory first, then package directory
    if not os.path.exists(config_file):
        myaiagent_dir = _find_myaiagent_dir()
        potential_config = os.path.join(myaiagent_dir, config_file)
        if os.path.exists(potential_config):
            config_file = potential_config
        elif not os.path.exists(config_file):
            print(f"Error: Config file not found: {config_file}")
            print(f"Tried: {config_file}")
            if os.path.exists(potential_config):
                print(f"Tried: {potential_config}")
            sys.exit(1)
    
    agent = Agent(
        config_path=config_file,
        api_key=config['api_key'],
        model=config.get('model', 'grok-4-latest'),
        brave_path=config.get('brave_path'),
        headless=config.get('headless', False)
    )
    
    try:
        agent.start_session()
        agent.run()
    finally:
        agent.close()


def cmd_logs(args):
    """View recent logs."""
    db = Database()
    
    try:
        logs = db.get_recent_logs(limit=args.limit)
        
        if not logs:
            print("No logs found.")
            return
        
        print(f"\n=== Recent Logs (showing {len(logs)} entries) ===\n")
        
        for log in logs:
            print(f"Session: {log.get('session_id', 'N/A')}")
            print(f"Step: {log.get('step_number', 'N/A')}")
            print(f"Prompt ID: {log.get('config_prompt_id', 'N/A')}")
            print(f"Prompt: {log.get('prompt_text', '')[:100]}...")
            if log.get('response_text'):
                print(f"Response: {log.get('response_text', '')[:150]}...")
            print(f"Tokens: {log.get('tokens_used', 'N/A')}")
            print(f"Time: {log.get('prompt_timestamp', 'N/A')}")
            print("-" * 80)
    
    finally:
        db.close()


def cmd_improvements(args):
    """List pending improvements."""
    db = Database()
    
    try:
        improvements = db.get_pending_improvements()
        
        if not improvements:
            print("No pending improvements.")
            return
        
        print(f"\n=== Pending Improvements ({len(improvements)}) ===\n")
        
        for imp in improvements:
            print(f"ID: {imp['id']}")
            print(f"Type: {imp['improvement_type']}")
            print(f"Description: {imp['description']}")
            print(f"Created: {imp['created_at']}")
            print("-" * 80)
    
    finally:
        db.close()


def cmd_approve(args):
    """Approve and apply an improvement."""
    if not args.improvement_id:
        print("Error: improvement_id required")
        sys.exit(1)
    
    db = Database()
    
    try:
        improvement = db.get_improvement(args.improvement_id)
        
        if not improvement:
            print(f"Error: Improvement {args.improvement_id} not found")
            sys.exit(1)
        
        if improvement['status'] != 'pending':
            print(f"Error: Improvement {args.improvement_id} is not pending (status: {improvement['status']})")
            sys.exit(1)
        
        # Get the config file from improvement
        import json
        changes = json.loads(improvement['suggested_changes'])
        target_file = changes.get('target_file', 'config/prompts.yaml')
        
        if not os.path.exists(target_file):
            print(f"Error: Target config file not found: {target_file}")
            sys.exit(1)
        
        # Apply improvement
        config_parser = ConfigParser(target_file)
        from self_improvement import SelfImprovement
        from api_client import APIClient
        
        config = load_config()
        api_client = APIClient(config.get('api_key', ''))
        self_improvement = SelfImprovement(db, api_client)
        
        if self_improvement.apply_improvement(args.improvement_id, config_parser):
            print(f"Improvement {args.improvement_id} approved and applied to {target_file}")
        else:
            print(f"Error: Failed to apply improvement {args.improvement_id}")
            sys.exit(1)
    
    finally:
        db.close()


def cmd_reject(args):
    """Reject an improvement."""
    if not args.improvement_id:
        print("Error: improvement_id required")
        sys.exit(1)
    
    db = Database()
    
    try:
        improvement = db.get_improvement(args.improvement_id)
        
        if not improvement:
            print(f"Error: Improvement {args.improvement_id} not found")
            sys.exit(1)
        
        db.reject_improvement(args.improvement_id)
        print(f"Improvement {args.improvement_id} rejected")
    
    finally:
        db.close()


def cmd_pause(args):
    """Pause current session."""
    db = Database()
    
    try:
        session_id = db.get_active_session()
        
        if not session_id:
            print("No active session found")
            return
        
        db.update_session_status(session_id, "paused")
        print(f"Session {session_id} paused")
    
    finally:
        db.close()


def cmd_resume(args):
    """Resume paused session."""
    db = Database()
    
    try:
        session_id = db.get_active_session()
        
        if not session_id:
            print("No active session found")
            return
        
        db.update_session_status(session_id, "running")
        print(f"Session {session_id} resumed")
    
    finally:
        db.close()


def cmd_improve(args):
    """Run iterative improvement on a project."""
    config = load_config()
    
    if not config.get('api_key'):
        print("Error: GROK_API_KEY or XAI_API_KEY not set.")
        sys.exit(1)
    
    # Resolve config file path
    config_file = args.config_file or 'config/project_improvement.yaml'
    
    # If config file not found, try relative to MyAIAgent directory
    if not os.path.exists(config_file):
        myaiagent_dir = _find_myaiagent_dir()
        potential_config = os.path.join(myaiagent_dir, config_file)
        if os.path.exists(potential_config):
            config_file = potential_config
        elif not os.path.exists(config_file):
            # Try default path relative to MyAIAgent
            default_config = os.path.join(myaiagent_dir, 'config', 'project_improvement.yaml')
            if os.path.exists(default_config):
                config_file = default_config
            else:
                print(f"Error: Config file not found: {config_file}")
                print(f"Tried: {config_file}")
                print(f"Tried: {potential_config}")
                print(f"Tried: {default_config}")
                print("Create a config file or use the example: config/project_improvement.yaml")
                sys.exit(1)
    
    # Load improvement config
    import yaml
    with open(config_file, 'r') as f:
        improve_config = yaml.safe_load(f) or {}
    
    # Determine project path: command-line argument takes precedence, then config, then current directory
    if hasattr(args, 'project_path') and args.project_path:
        project_path = os.path.abspath(args.project_path)
    else:
        project_path = improve_config.get('project', {}).get('path', '.')
        project_path = os.path.abspath(project_path)
    
    # Extract token budget settings
    token_budget_config = improve_config.get('token_budget', {})
    max_tokens = token_budget_config.get('max_tokens_per_session')
    warning_threshold = token_budget_config.get('warning_threshold', 0.80)
    hard_stop = token_budget_config.get('hard_stop', True)
    
    # Initialize components
    db = Database()
    api_client = APIClient(
        config['api_key'],
        model=config.get('model', 'grok-4-latest'),
        max_tokens=max_tokens,
        warning_threshold=warning_threshold,
        hard_stop=hard_stop
    )
    
    # Create session
    import uuid
    session_id = str(uuid.uuid4())
    db.create_session(session_id, config_file)
    
    try:
        print(f"Starting improvement session: {session_id}")
        print(f"Project path: {project_path}")
        print(f"Quality threshold: {improve_config.get('quality', {}).get('threshold', 85)}")
        
        # Display token budget info
        if max_tokens:
            print(f"Token Budget: {max_tokens:,} tokens")
            print(f"Warning at: {warning_threshold*100:.0f}% ({int(max_tokens * warning_threshold):,} tokens)")
            print(f"Hard stop: {'Enabled' if hard_stop else 'Disabled'}")
        
        # Git safety check
        if improve_config.get('safety', {}).get('git_integration', True):
            _git_safety_check(project_path)
        
        # Run improvement loop
        engine = ImprovementEngine(api_client, db, project_path)
        results = engine.run_improvement_loop(session_id, improve_config)
        
        # Print results
        print(f"\n{'='*60}")
        print("Improvement Complete")
        print(f"{'='*60}")
        print(f"Final Score: {results['final_score']}/100")
        print(f"Threshold Met: {results['threshold_met']}")
        print(f"Iterations: {len(results['iterations'])}")
        
        if results.get('budget_exceeded'):
            print(f"\n⚠️  Session stopped due to token budget limit")
        
        if results['iterations']:
            print("\nIteration Summary:")
            for iter_result in results['iterations']:
                print(f"  Iteration {iter_result['iteration']}: "
                      f"{iter_result['score_before']} -> {iter_result['score_after']} "
                      f"({iter_result['improvements']} improvements, "
                      f"{len(iter_result['files_modified'])} files modified)")
        
        # Display final token usage summary
        if max_tokens:
            print(f"\nToken Usage Summary:")
            print(f"  Total used: {api_client.tokens_used_session:,}/{max_tokens:,} tokens")
            if api_client.tokens_used_session > 0:
                usage_pct = (api_client.tokens_used_session / max_tokens) * 100
                print(f"  Percentage: {usage_pct:.1f}%")
                remaining = api_client.get_remaining_tokens()
                print(f"  Remaining: {remaining:,} tokens")
        
        status = "budget_exceeded" if results.get('budget_exceeded') else "completed"
        db.update_session_status(session_id, status)
        
    finally:
        db.close()


def _git_safety_check(project_path: str):
    """Check git status and create backup commit."""
    import subprocess
    
    # Check if git repo
    git_dir = os.path.join(project_path, '.git')
    if not os.path.exists(git_dir):
        print("Warning: Not a git repository. Changes cannot be rolled back.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
        return
    
    # Check for uncommitted changes
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            print("Warning: Uncommitted changes detected.")
            response = input("Create backup commit before improvements? (y/n): ")
            if response.lower() == 'y':
                subprocess.run(
                    ['git', 'add', '.'],
                    cwd=project_path
                )
                subprocess.run(
                    ['git', 'commit', '-m', 'Backup before AI agent improvements'],
                    cwd=project_path
                )
                print("✓ Backup commit created")
    except Exception as e:
        print(f"Git check warning: {str(e)}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Self-improving AI agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start agent session')
    start_parser.add_argument('config_file', nargs='?', help='Path to YAML config file')
    start_parser.set_defaults(func=cmd_start)
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='View recent logs')
    logs_parser.add_argument('--limit', type=int, default=50, help='Number of logs to show')
    logs_parser.set_defaults(func=cmd_logs)
    
    # Improvements command
    improvements_parser = subparsers.add_parser('improvements', help='List pending improvements')
    improvements_parser.set_defaults(func=cmd_improvements)
    
    # Approve command
    approve_parser = subparsers.add_parser('approve', help='Approve and apply improvement')
    approve_parser.add_argument('improvement_id', type=int, help='Improvement ID to approve')
    approve_parser.set_defaults(func=cmd_approve)
    
    # Reject command
    reject_parser = subparsers.add_parser('reject', help='Reject improvement')
    reject_parser.add_argument('improvement_id', type=int, help='Improvement ID to reject')
    reject_parser.set_defaults(func=cmd_reject)
    
    # Pause command
    pause_parser = subparsers.add_parser('pause', help='Pause current session')
    pause_parser.set_defaults(func=cmd_pause)
    
    # Resume command
    resume_parser = subparsers.add_parser('resume', help='Resume paused session')
    resume_parser.set_defaults(func=cmd_resume)
    
    # Improve command (new iterative improvement feature)
    improve_parser = subparsers.add_parser('improve', help='Run iterative code improvement on project')
    improve_parser.add_argument('config_file', nargs='?',
                                help='Path to improvement config file (default: config/project_improvement.yaml)')
    improve_parser.add_argument('--project-path', type=str, default=None,
                                help='Path to project directory (default: current directory or value from config)')
    improve_parser.set_defaults(func=cmd_improve)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()

