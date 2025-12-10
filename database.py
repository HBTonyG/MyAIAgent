"""
SQLite database module for logging all agent interactions.

This module handles:
- Schema creation for prompts, responses, errors, and improvements
- Logging methods for all interactions
- Query methods for log analysis
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os


class Database:
    """SQLite database handler for agent logging."""
    
    def __init__(self, db_path: str = "agent.db"):
        """
        Initialize database connection and create schema.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()
    
    def _create_schema(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                config_file TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paused_at TIMESTAMP,
                resumed_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Prompts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                prompt_id TEXT,
                prompt_text TEXT NOT NULL,
                step_number INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Responses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                prompt_id INTEGER,
                response_text TEXT NOT NULL,
                model_used TEXT,
                tokens_used INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Errors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                error_type TEXT,
                error_message TEXT,
                stack_trace TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Browser actions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS browser_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_details TEXT,
                success BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Improvements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS improvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                improvement_type TEXT NOT NULL,
                description TEXT NOT NULL,
                suggested_changes TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Quality scores table (for iterative improvement)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                iteration_number INTEGER NOT NULL,
                overall_score REAL,
                scores_json TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Improvement iterations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS improvement_iterations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                iteration_number INTEGER NOT NULL,
                quality_score_before REAL,
                quality_score_after REAL,
                improvements_applied TEXT,
                files_modified TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        self.conn.commit()
    
    def create_session(self, session_id: str, config_file: Optional[str] = None) -> int:
        """
        Create a new session record.
        
        Args:
            session_id: Unique session identifier
            config_file: Path to config file used
            
        Returns:
            Session database ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (session_id, status, config_file)
            VALUES (?, ?, ?)
        """, (session_id, "running", config_file))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_session_status(self, session_id: str, status: str):
        """Update session status (running, paused, completed)."""
        cursor = self.conn.cursor()
        timestamp_field = None
        if status == "paused":
            timestamp_field = "paused_at"
        elif status == "running" and timestamp_field is None:
            timestamp_field = "resumed_at"
        elif status == "completed":
            timestamp_field = "completed_at"
        
        if timestamp_field:
            cursor.execute(f"""
                UPDATE sessions 
                SET status = ?, {timestamp_field} = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (status, session_id))
        else:
            cursor.execute("""
                UPDATE sessions 
                SET status = ?
                WHERE session_id = ?
            """, (status, session_id))
        self.conn.commit()
    
    def log_prompt(self, session_id: str, prompt_text: str, 
                   prompt_id: Optional[str] = None, step_number: Optional[int] = None) -> int:
        """
        Log a prompt to the database.
        
        Args:
            session_id: Session identifier
            prompt_text: The prompt text
            prompt_id: Optional prompt ID from config
            step_number: Optional step number in sequence
            
        Returns:
            Prompt database ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO prompts (session_id, prompt_id, prompt_text, step_number)
            VALUES (?, ?, ?, ?)
        """, (session_id, prompt_id, prompt_text, step_number))
        self.conn.commit()
        return cursor.lastrowid
    
    def log_response(self, session_id: str, prompt_id: int, response_text: str,
                     model_used: Optional[str] = None, tokens_used: Optional[int] = None) -> int:
        """
        Log an API response.
        
        Args:
            session_id: Session identifier
            prompt_id: Database ID of the prompt
            response_text: The response text
            model_used: Model name used
            tokens_used: Number of tokens used
            
        Returns:
            Response database ID
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO responses (session_id, prompt_id, response_text, model_used, tokens_used)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, prompt_id, response_text, model_used, tokens_used))
        self.conn.commit()
        return cursor.lastrowid
    
    def log_error(self, session_id: str, error_type: str, error_message: str,
                  stack_trace: Optional[str] = None):
        """Log an error."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO errors (session_id, error_type, error_message, stack_trace)
            VALUES (?, ?, ?, ?)
        """, (session_id, error_type, error_message, stack_trace))
        self.conn.commit()
    
    def log_browser_action(self, session_id: str, action_type: str,
                          action_details: Optional[Dict[str, Any]] = None, success: bool = True):
        """Log a browser automation action."""
        cursor = self.conn.cursor()
        details_json = json.dumps(action_details) if action_details else None
        cursor.execute("""
            INSERT INTO browser_actions (session_id, action_type, action_details, success)
            VALUES (?, ?, ?, ?)
        """, (session_id, action_type, details_json, success))
        self.conn.commit()
    
    def create_improvement(self, session_id: str, improvement_type: str,
                          description: str, suggested_changes: Dict[str, Any]) -> int:
        """
        Create a new improvement suggestion.
        
        Args:
            session_id: Session identifier
            improvement_type: Type of improvement (e.g., 'config_update')
            description: Description of the improvement
            suggested_changes: Dictionary of suggested changes
            
        Returns:
            Improvement database ID
        """
        cursor = self.conn.cursor()
        changes_json = json.dumps(suggested_changes)
        cursor.execute("""
            INSERT INTO improvements (session_id, improvement_type, description, suggested_changes)
            VALUES (?, ?, ?, ?)
        """, (session_id, improvement_type, description, changes_json))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_pending_improvements(self) -> List[Dict[str, Any]]:
        """Get all pending improvements."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM improvements 
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def approve_improvement(self, improvement_id: int):
        """Mark an improvement as approved."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE improvements 
            SET status = 'approved', approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (improvement_id,))
        self.conn.commit()
    
    def reject_improvement(self, improvement_id: int):
        """Mark an improvement as rejected."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE improvements 
            SET status = 'rejected'
            WHERE id = ?
        """, (improvement_id,))
        self.conn.commit()
    
    def get_improvement(self, improvement_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific improvement by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM improvements WHERE id = ?", (improvement_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent logs combining prompts and responses.
        
        Args:
            limit: Maximum number of log entries to return
            
        Returns:
            List of log entries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                p.id as prompt_id,
                p.session_id,
                p.prompt_id as config_prompt_id,
                p.prompt_text,
                p.step_number,
                p.timestamp as prompt_timestamp,
                r.response_text,
                r.model_used,
                r.tokens_used,
                r.timestamp as response_timestamp
            FROM prompts p
            LEFT JOIN responses r ON p.id = r.prompt_id
            ORDER BY p.timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific session."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                p.id as prompt_id,
                p.prompt_id as config_prompt_id,
                p.prompt_text,
                p.step_number,
                p.timestamp as prompt_timestamp,
                r.response_text,
                r.model_used,
                r.tokens_used,
                r.timestamp as response_timestamp
            FROM prompts p
            LEFT JOIN responses r ON p.id = r.prompt_id
            WHERE p.session_id = ?
            ORDER BY p.timestamp ASC
        """, (session_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_active_session(self) -> Optional[str]:
        """Get the currently active session ID."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT session_id FROM sessions 
            WHERE status IN ('running', 'paused')
            ORDER BY started_at DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return row['session_id'] if row else None
    
    def save_quality_score(self, session_id: str, iteration_number: int,
                          overall_score: float, scores_json: str):
        """Save quality score for an iteration."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO quality_scores (session_id, iteration_number, overall_score, scores_json)
            VALUES (?, ?, ?, ?)
        """, (session_id, iteration_number, overall_score, scores_json))
        self.conn.commit()
    
    def save_iteration(self, session_id: str, iteration_number: int,
                      quality_before: float, quality_after: float,
                      improvements_applied: str, files_modified: str):
        """Save improvement iteration record."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO improvement_iterations 
            (session_id, iteration_number, quality_score_before, quality_score_after, 
             improvements_applied, files_modified)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, iteration_number, quality_before, quality_after,
              improvements_applied, files_modified))
        self.conn.commit()
    
    def get_iteration_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get iteration history for a session."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM improvement_iterations
            WHERE session_id = ?
            ORDER BY iteration_number ASC
        """, (session_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def close(self):
        """Close database connection."""
        self.conn.close()

