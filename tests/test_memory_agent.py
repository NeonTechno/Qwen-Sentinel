"""Unit tests for MemoryAgent (4 tests)."""
import tempfile
import unittest
from pathlib import Path

from src.cloud.memory import MemoryAgent
from src.common.models import Alert, AlertCategory, Severity


def make_alert(category=AlertCategory.OVERHEATING, severity=Severity.WARNING):
    return Alert(category=category, severity=severity, message="test alert")


class TestMemoryAgent(unittest.TestCase):
    def test_record_appends_history(self):
        memory = MemoryAgent()
        reading = {"timestamp": "t1", "environment_state": "normal"}
        memory.record(reading, [])
        self.assertEqual(len(memory.get_recent(10)), 1)

    def test_window_size_enforced(self):
        memory = MemoryAgent(window_size=3)
        for i in range(5):
            memory.record({"timestamp": f"t{i}", "environment_state": "normal"}, [])
        self.assertEqual(len(memory.get_recent(10)), 3)

    def test_persist_and_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memory.json"
            memory = MemoryAgent(storage_path=str(path))
            memory.record(
                {"timestamp": "t1", "environment_state": "overheating"},
                [make_alert()],
            )
            self.assertTrue(path.exists())

            reloaded = MemoryAgent(storage_path=str(path))
            self.assertEqual(len(reloaded.get_recent(10)), 1)
            self.assertEqual(reloaded.get_recent(1)[0]["environment_state"], "overheating")

    def test_count_by_category(self):
        memory = MemoryAgent()
        memory.record({"timestamp": "t1", "environment_state": "overheating"}, [make_alert(AlertCategory.OVERHEATING)])
        memory.record({"timestamp": "t2", "environment_state": "normal"}, [])
        memory.record({"timestamp": "t3", "environment_state": "overheating"}, [make_alert(AlertCategory.OVERHEATING)])
        self.assertEqual(memory.count_by_category("overheating"), 2)


if __name__ == "__main__":
    unittest.main()
