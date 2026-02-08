from typing import List, Deque, Optional
from collections import deque
from pydantic import BaseModel
from datetime import datetime
import threading

class HistoryEntry(BaseModel):
    hotkey_id: str
    timestamp: float
    duration: float
    input_preview: str
    output_preview: str
    model_id: str
    status: str

class HistoryRepository:
    def __init__(self, max_entries: int = 50):
        self._entries: Deque[HistoryEntry] = deque(maxlen=max_entries)
        self._lock = threading.Lock()

    def add(self, entry: HistoryEntry):
        with self._lock:
            self._entries.appendleft(entry)

    def get_recent(self, limit: int = 10) -> List[HistoryEntry]:
        with self._lock:
            return list(self._entries)[:limit]

    def clear(self):
        with self._lock:
            self._entries.clear()
