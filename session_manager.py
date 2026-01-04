"""
Session Manager for Meeting Coach Agent
Tracks and manages analysis sessions for easy resumption.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class SessionManager:
    """Manages meeting analysis sessions."""
    
    def __init__(self, storage_path: str = "results/sessions.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_storage()
    
    def _ensure_storage(self):
        """Create storage file if it doesn't exist."""
        if not self.storage_path.exists():
            self._save_sessions([])
    
    def _load_sessions(self) -> List[Dict]:
        """Load all sessions from storage."""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_sessions(self, sessions: List[Dict]):
        """Save sessions to storage."""
        with open(self.storage_path, 'w') as f:
            json.dump(sessions, f, indent=2)
    
    def save_session(
        self,
        session_id: str,
        audio_filename: str,
        user_role: str,
        analysis_type: str,
        output_file: str
    ):
        """Save a new session with metadata."""
        sessions = self._load_sessions()
        
        session_data = {
            "session_id": session_id,
            "audio_filename": audio_filename,
            "user_role": user_role,
            "analysis_type": analysis_type,
            "output_file": output_file,
            "timestamp": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        
        sessions.append(session_data)
        self._save_sessions(sessions)
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all sessions, sorted by most recent first."""
        sessions = self._load_sessions()
        return sorted(sessions, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a specific session by ID."""
        sessions = self._load_sessions()
        for session in sessions:
            if session['session_id'] == session_id:
                return session
        return None
    
    def update_last_accessed(self, session_id: str):
        """Update the last accessed time for a session."""
        sessions = self._load_sessions()
        for session in sessions:
            if session['session_id'] == session_id:
                session['last_accessed'] = datetime.now().isoformat()
                break
        self._save_sessions(sessions)
    
    def delete_session(self, session_id: str):
        """Delete a session."""
        sessions = self._load_sessions()
        sessions = [s for s in sessions if s['session_id'] != session_id]
        self._save_sessions(sessions)
    
    def format_session_display(self, session: Dict) -> str:
        """Format session info for display."""
        timestamp = datetime.fromisoformat(session['timestamp'])
        date_str = timestamp.strftime("%Y-%m-%d %H:%M")
        
        return f"{session['audio_filename']} ({session['analysis_type']}) - {date_str}"

