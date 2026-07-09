"""Unit tests for AlertManager (3 tests)."""
import unittest

from src.cloud.alerts import AlertManager
from src.common.models import Alert, AlertCategory, Severity


def make_alert(category=AlertCategory.INTRUDER, severity=Severity.CRITICAL):
    return Alert(category=category, severity=severity, message="test alert")


class TestAlertManager(unittest.TestCase):
    def test_dispatch_invokes_custom_dispatcher(self):
        received = []
        manager = AlertManager(dispatcher=received.append)
        alert = make_alert()
        dispatched = manager.process([alert])
        self.assertEqual(dispatched, [alert])
        self.assertEqual(received, [alert])

    def test_cooldown_suppresses_duplicate(self):
        clock_time = {"now": 0.0}
        manager = AlertManager(
            cooldown_seconds=10,
            dispatcher=lambda a: None,
            clock=lambda: clock_time["now"],
        )
        alert = make_alert()
        first = manager.process([alert])
        second = manager.process([alert])  # same clock time -> still in cooldown
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)

        clock_time["now"] = 11.0  # advance past cooldown
        third = manager.process([alert])
        self.assertEqual(len(third), 1)

    def test_format_alert_output(self):
        alert = make_alert(category=AlertCategory.LOW_LIGHT, severity=Severity.INFO)
        formatted = AlertManager.format_alert(alert)
        self.assertIn("INFO", formatted)
        self.assertIn("low_light", formatted)


if __name__ == "__main__":
    unittest.main()
