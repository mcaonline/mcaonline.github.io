from typing import List, Deque, Optional
from collections import deque
from pydantic import BaseModel
from datetime import datetime
import threading
from loguru import logger
import json
from pathlib import Path

class HistoryEntry(BaseModel):
    hotkey_id: str
    timestamp: float
    duration: float
    input_preview: str
    output_preview: str
    model_id: str
    status: str

class HistoryRepository:
    def __init__(self, storage_path: Path = Path("history.json"), max_entries: int = 50):
        self.storage_path = storage_path
        self._entries: Deque[HistoryEntry] = deque(maxlen=max_entries)
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        self._entries.append(HistoryEntry(**item))
            except Exception as e:
                logger.error(f"Failed to load history: {e}")

    def _save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([e.model_dump() for e in self._entries], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def add(self, entry: HistoryEntry):
        with self._lock:
            self._entries.appendleft(entry)
            self._save()

    def get_recent(self, limit: int = 20) -> List[HistoryEntry]:
        with self._lock:
            items = list(self._entries)
            return items[:limit]

    def clear(self):
        with self._lock:
            self._entries.clear()
            if self.storage_path.exists():
                try:
                    self.storage_path.unlink()
                except:
                    pass
