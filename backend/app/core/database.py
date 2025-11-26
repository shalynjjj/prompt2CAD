import sqlite3
import json
from typing import Optional, Dict
from contextlib import contextmanager


class Database:
    """Simple SQLite database for tracking files by session_id."""
    
    def __init__(self, db_path: str = "keychain.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Simple files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    session_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    url_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (session_id, file_type)
                )
            """)
            
            # Analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis (
                    session_id TEXT PRIMARY KEY,
                    width REAL,
                    length REAL,
                    thickness REAL,
                    complexity TEXT,
                    ratio_string TEXT
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_file(self, session_id: str, file_type: str, file_path: str, url_path: str):
        """Save or update file path."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO files (session_id, file_type, file_path, url_path)
                   VALUES (?, ?, ?, ?)""",
                (session_id, file_type, file_path, url_path)
            )
            conn.commit()
    
    def get_file(self, session_id: str, file_type: str) -> Optional[Dict]:
        """Get file path by session_id and type."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM files WHERE session_id = ? AND file_type = ?",
                (session_id, file_type)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def save_analysis(self, session_id: str, analysis_data: Dict):
        """Save analysis results."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO analysis 
                   (session_id, width, length, thickness, complexity, ratio_string)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    analysis_data.get('width'),
                    analysis_data.get('length'),
                    analysis_data.get('thickness'),
                    analysis_data.get('complexity'),
                    analysis_data.get('ratio_string')
                )
            )
            conn.commit()
    
    def get_analysis(self, session_id: str) -> Optional[Dict]:
        """Get analysis results."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM analysis WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None