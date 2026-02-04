"""
Progress tracker for scraping operations
"""
import time
from threading import Lock
from collections import defaultdict
from typing import Dict, List, Callable

class ProgressTracker:
    """Thread-safe progress tracker for scraping operations"""
    
    def __init__(self):
        self.sessions: Dict[str, List[dict]] = defaultdict(list)
        self.lock = Lock()
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
    
    def emit(self, session_id: str, event_type: str, data: dict):
        """Emit a progress event"""
        event = {
            'type': event_type,
            'timestamp': time.time(),
            'data': data
        }
        
        with self.lock:
            self.sessions[session_id].append(event)
            
            # Call callbacks
            for callback in self.callbacks.get(session_id, []):
                try:
                    callback(event)
                except:
                    pass
    
    def get_events(self, session_id: str) -> List[dict]:
        """Get all events for a session"""
        with self.lock:
            return self.sessions.get(session_id, []).copy()
    
    def subscribe(self, session_id: str, callback: Callable):
        """Subscribe to events for a session"""
        with self.lock:
            self.callbacks[session_id].append(callback)
    
    def clear_session(self, session_id: str):
        """Clear a session's events"""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
            if session_id in self.callbacks:
                del self.callbacks[session_id]

# Global instance
progress_tracker = ProgressTracker()
