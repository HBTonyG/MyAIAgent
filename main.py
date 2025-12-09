#!/usr/bin/env python3
"""
CLI interface for the self-improving AI agent.

SETUP INSTRUCTIONS:
===================

1. Install dependencies:
   pip install -r requirements.txt

2. Install ChromeDriver (required for Brave browser automation):
   brew install chromedriver
   Or download from: https://chromedriver.chromium.org/

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


def load_config() -> dict:
    """Load agent configuration from config file or environment."""
    config = {
        'api_key': os.getenv('GROK_API_KEY') or os.getenv('XAI_API_KEY'),
        'brave_path': os.getenv('BRAVE_BROWSER_PATH'),
        'headless': os.getenv('HEADLESS', 'false').lower() == 'true',
        'default_config': 'config/prompts.yaml',
        'model': os.getenv('GROK_MODEL', 'grok-4-latest')
    }
    
    # Try to load from agent_config.yaml if it exists
    if os.path.exists('config/agent_config.yaml'):
        import yaml
        with open('config/agent_config.yaml', 'r') as f:
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
    
    if not os.path.exists(config_file):
        print(f"Error: Config file not found: {config_file}")
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
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()

