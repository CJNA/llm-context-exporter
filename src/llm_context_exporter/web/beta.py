"""
Beta user management for the web interface.

This module handles beta user registration, tracking, and feedback collection.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from ..models.payment import BetaUser, UsageStats, Feedback


class BetaManager:
    """
    Manages beta users and their feedback.
    
    Handles beta user whitelist, usage tracking, and feedback collection
    for the beta testing program.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the beta manager.
        
        Args:
            db_path: Path to SQLite database (defaults to ~/.llm_context_exporter_beta.db)
        """
        self.db_path = db_path or os.path.expanduser("~/.llm_context_exporter_beta.db")
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS beta_users (
                    email TEXT PRIMARY KEY,
                    added_date TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    total_exports INTEGER DEFAULT 0,
                    last_export_date TEXT,
                    feedback_count INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    feedback_text TEXT NOT NULL,
                    export_id TEXT NOT NULL,
                    target_platform TEXT NOT NULL,
                    FOREIGN KEY (email) REFERENCES beta_users (email)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    email TEXT NOT NULL,
                    export_date TEXT NOT NULL,
                    target_platform TEXT NOT NULL,
                    conversations_processed INTEGER DEFAULT 0,
                    export_size_mb REAL DEFAULT 0.0,
                    FOREIGN KEY (email) REFERENCES beta_users (email)
                )
            """)
            
            conn.commit()
    
    def add_beta_user(self, email: str, notes: str = "") -> None:
        """
        Add a user to the beta whitelist.
        
        Args:
            email: User email address
            notes: Optional notes about the user
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO beta_users 
                (email, added_date, notes, total_exports, feedback_count)
                VALUES (?, ?, ?, 0, 0)
            """, (email, datetime.now().isoformat(), notes))
            conn.commit()
    
    def remove_beta_user(self, email: str) -> None:
        """
        Remove a user from the beta whitelist.
        
        Args:
            email: User email address
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM beta_users WHERE email = ?", (email,))
            conn.commit()
    
    def is_beta_user(self, email: str) -> bool:
        """
        Check if a user is in the beta program.
        
        Args:
            email: User email address
            
        Returns:
            True if user is in beta program
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM beta_users WHERE email = ?", (email,))
            return cursor.fetchone() is not None
    
    def get_beta_users(self) -> List[BetaUser]:
        """
        Get all beta users with their statistics.
        
        Returns:
            List of BetaUser objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT email, added_date, notes, total_exports, 
                       last_export_date, feedback_count
                FROM beta_users
                ORDER BY added_date DESC
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append(BetaUser(
                    email=row[0],
                    added_date=datetime.fromisoformat(row[1]),
                    notes=row[2] or "",
                    total_exports=row[3],
                    last_export_date=datetime.fromisoformat(row[4]) if row[4] else None,
                    feedback_count=row[5]
                ))
            
            return users
    
    def record_export(self, email: str, target_platform: str, conversations_processed: int = 0, export_size_mb: float = 0.0) -> None:
        """
        Record an export by a beta user.
        
        Args:
            email: User email address
            target_platform: Target platform (gemini/ollama)
            conversations_processed: Number of conversations processed
            export_size_mb: Size of export in MB
        """
        export_date = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Update beta user stats
            conn.execute("""
                UPDATE beta_users 
                SET total_exports = total_exports + 1,
                    last_export_date = ?
                WHERE email = ?
            """, (export_date, email))
            
            # Record usage stats
            conn.execute("""
                INSERT INTO usage_stats 
                (email, export_date, target_platform, conversations_processed, export_size_mb)
                VALUES (?, ?, ?, ?, ?)
            """, (email, export_date, target_platform, conversations_processed, export_size_mb))
            
            conn.commit()
    
    def record_feedback(self, email: str, feedback: str, rating: int, export_id: str, target_platform: str) -> None:
        """
        Store beta user feedback.
        
        Args:
            email: User email address
            feedback: Feedback text
            rating: Rating (1-5 stars)
            export_id: ID of the export this feedback relates to
            target_platform: Target platform for the export
        """
        timestamp = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Insert feedback
            conn.execute("""
                INSERT INTO feedback 
                (email, timestamp, rating, feedback_text, export_id, target_platform)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (email, timestamp, rating, feedback, export_id, target_platform))
            
            # Update feedback count
            conn.execute("""
                UPDATE beta_users 
                SET feedback_count = feedback_count + 1
                WHERE email = ?
            """, (email,))
            
            conn.commit()
    
    def get_usage_stats(self, email: str) -> UsageStats:
        """
        Get usage statistics for a beta user.
        
        Args:
            email: User email address
            
        Returns:
            UsageStats object
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get basic stats
            cursor = conn.execute("""
                SELECT total_exports, last_export_date
                FROM beta_users
                WHERE email = ?
            """, (email,))
            
            row = cursor.fetchone()
            if not row:
                return UsageStats(
                    total_exports=0,
                    exports_by_target={},
                    total_conversations_processed=0,
                    average_export_size_mb=0.0,
                    last_export_date=None
                )
            
            total_exports, last_export_date = row
            
            # Get exports by target platform
            cursor = conn.execute("""
                SELECT target_platform, COUNT(*)
                FROM usage_stats
                WHERE email = ?
                GROUP BY target_platform
            """, (email,))
            
            exports_by_target = dict(cursor.fetchall())
            
            # Get conversation and size stats
            cursor = conn.execute("""
                SELECT SUM(conversations_processed), AVG(export_size_mb)
                FROM usage_stats
                WHERE email = ?
            """, (email,))
            
            conv_sum, avg_size = cursor.fetchone()
            
            return UsageStats(
                total_exports=total_exports,
                exports_by_target=exports_by_target,
                total_conversations_processed=conv_sum or 0,
                average_export_size_mb=avg_size or 0.0,
                last_export_date=datetime.fromisoformat(last_export_date) if last_export_date else None
            )
    
    def get_all_feedback(self) -> List[Feedback]:
        """
        Get all feedback from beta users.
        
        Returns:
            List of Feedback objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT email, timestamp, rating, feedback_text, export_id, target_platform
                FROM feedback
                ORDER BY timestamp DESC
            """)
            
            feedback_list = []
            for row in cursor.fetchall():
                feedback_list.append(Feedback(
                    email=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    rating=row[2],
                    feedback_text=row[3],
                    export_id=row[4],
                    target_platform=row[5]
                ))
            
            return feedback_list