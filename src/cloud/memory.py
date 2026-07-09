"""
MemoryAgent: persistent, file-backed memory of recent sensor readings and
raised alerts, used for trend analysis (e.g. "how many overheating events
in the last N readings") rather than reacting to a single sample in
isolation.
"""
import json
from collections import Counter, deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from src.common import config
from src.common.models import Alert


class MemoryAgent:
    def __init__(
        self,
        storage_path: Optional[str] = None,
        window_size: int = config.DEFAULT_MEMORY_WINDOW,
    ) -> None:
        self.storage_path = Path(storage_path) if storage_path else None
        self.window_size = window_size
        self.history: Deque[Dict[str, Any]] = deque(maxlen=window_size)
        if self.storage_path and self.storage_path.exists():
            self._load()

    def record(self, reading: Dict[str, Any], alerts: List[Alert]) -> None:
        entry = {
            "timestamp": reading.get("timestamp"),
            "environment_state": reading.get("environment_state"),
            "alert_categories": [a.category.value for a in alerts],
            "alert_severities": [a.severity.value for a in alerts],
        }
        self.history.append(entry)
        if self.storage_path:
            self._persist()

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        return list(self.history)[-n:]

    def count_by_category(self, category: str) -> int:
        return sum(1 for entry in self.history if category in entry.get("alert_categories", []))

    def category_counts(self) -> Dict[str, int]:
        counter: Counter = Counter()
        for entry in self.history:
            counter.update(entry.get("alert_categories", []))
        return dict(counter)

    def clear(self) -> None:
        self.history.clear()
        if self.storage_path and self.storage_path.exists():
            self.storage_path.unlink()

    def _persist(self) -> None:
        assert self.storage_path is not None
        self.storage_path.write_text(json.dumps(list(self.history), indent=2))

    def _load(self) -> None:
        assert self.storage_path is not None
        try:
            data = json.loads(self.storage_path.read_text())
            for entry in data[-self.window_size:]:
                self.history.append(entry)
        except (json.JSONDecodeError, OSError):
            # Corrupted or unreadable memory file: start fresh rather than crash.
            self.history.clear()
