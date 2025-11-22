
# TODO: redis or other database 
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict

DB_PATH = Path("chat_history.db")

class HistoryService:

    def __init__(self):
        self.__init__db()

    def _get_connection(self):
        return sqlite3.connect(DB_PATH,check_same_thread=False)
    
    def __init__db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT NOT NULL,
            ref_image_path TEXT,
            message TEXT,
            scad_code TEXT,
            file_paths TEXT,
            prompt_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON chat_history(session_id)')
        conn.commit()
        conn.close()
    
    def add_user_message(self, session_id: str, message: str, image_path: str = None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO chat_history (session_id, role, message, ref_image_path)
        VALUES (?, 'user', ?, ?)
        """, (session_id, message, image_path))
        conn.commit()
        conn.close()
    
    def add_ai_message(self, session_id, message: str, scad_code: str, file_paths: dict, prompt_version: str = "v1"):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO chat_history (session_id, role, message, scad_code, file_paths, prompt_version)
        VALUES (?, 'ai', ?, ?, ?, ?)
        """, (session_id, message, scad_code, json.dumps(file_paths), prompt_version))
        conn.commit()
        conn.close()
    
    def get_latest_code(self, session_id: str) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT scad_code FROM chat_history
        WHERE session_id = ? AND role = 'ai' AND scad_code IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 1
        """, (session_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM chat_history
        WHERE session_id = ?
        ORDER BY id ASC
        """, (session_id,))
        rows = cursor.fetchall()
        conn.close()

        history=[]
        for row in rows:
            history.append({
                "role": row["role"],
                "message": row["message"],
                "ref_image_path": row["ref_image_path"],
                "scad_code": row["scad_code"],
                "file_paths": json.loads(row["file_paths"]) if row["file_paths"] else None,
                "prompt_version": row["prompt_version"],
                "timestamp": row["created_at"]
            })
        return history



history_service = HistoryService()
