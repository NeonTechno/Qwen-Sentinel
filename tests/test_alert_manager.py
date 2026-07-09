"""Unit tests for AlertManager."""
import unittest
from src.cloud.alerts import AlertManager, create_webhook_dispatcher
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
        manager = AlertManager(cooldown_seconds=10, dispatcher=lambda a: None, clock=lambda: clock_time["now"])
        alert = make_alert()
        first = manager.process([alert])
        second = manager.process([alert])
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)
        clock_time["now"] = 11.0
        third = manager.process([alert])
        self.assertEqual(len(third), 1)

    def test_format_alert_output(self):
        alert = make_alert(category=AlertCategory.LOW_LIGHT, severity=Severity.INFO)
        formatted = AlertManager.format_alert(alert)
        self.assertIn("INFO", formatted)
        self.assertIn("low_light", formatted)

    def test_webhook_dispatcher_creation(self):
        dispatcher = create_webhook_dispatcher("http://example.com/webhook")
        self.assertIsNotNone(dispatcher)
        self.assertCallable(dispatcher)


if __name__ == "__main__":
    unittest.main()