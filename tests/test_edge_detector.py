"""Unit tests for EdgeDetector."""
import unittest
from src.common.models import AlertCategory, Severity
from src.edge.detector import EdgeDetector


def make_reading(environment_state, temperature=22.0, motion=0.1, objects_detected=None, motion_level=0.1, brightness=100, humidity=50.0, aqi=50):
    return {
        "timestamp": "2026-07-09T00:00:00Z",
        "environment_state": environment_state,
        "sensors": {
            "camera": {"objects_detected": objects_detected or [], "facial_expression": "neutral", "motion_level": motion_level, "brightness": brightness},
            "temperature": {"value": temperature, "unit": "C", "status": "ok"},
            "motion": {"value": motion, "unit": "normalized", "status": "ok"},
            "humidity": {"value": humidity, "unit": "%", "status": "ok"},
            "air_quality": {"value": aqi, "unit": "AQI", "status": "good"},
        },
    }


class TestEdgeDetector(unittest.TestCase):
    def setUp(self):
        self.detector = EdgeDetector()

    def test_normal_state_no_alerts(self):
        reading = make_reading("normal", temperature=22.0, motion=0.1, motion_level=0.1, brightness=100)
        alerts = self.detector.analyze(reading)
        self.assertEqual(alerts, [])

    def test_overheating_triggers_alert(self):
        reading = make_reading("overheating", temperature=40.0)
        alerts = self.detector.analyze(reading)
        categories = [a.category for a in alerts]
        self.assertIn(AlertCategory.OVERHEATING, categories)
        overheat = next(a for a in alerts if a.category == AlertCategory.OVERHEATING)
        self.assertEqual(overheat.severity, Severity.CRITICAL)

    def test_intruder_triggers_alert(self):
        reading = make_reading("intruder_detected", motion=0.9, objects_detected=[{"type": "person", "confidence": 0.85}])
        alerts = self.detector.analyze(reading)
        categories = [a.category for a in alerts]
        self.assertIn(AlertCategory.INTRUDER, categories)

    def test_high_noise_triggers_alert(self):
        reading = make_reading("high_noise", motion_level=0.65, objects_detected=[{"type": "noise_source", "confidence": 0.7}])
        alerts = self.detector.analyze(reading)
        categories = [a.category for a in alerts]
        self.assertIn(AlertCategory.HIGH_NOISE, categories)

    def test_low_light_triggers_alert(self):
        reading = make_reading("low_light", brightness=15)
        alerts = self.detector.analyze(reading)
        categories = [a.category for a in alerts]
        self.assertIn(AlertCategory.LOW_LIGHT, categories)

    def test_high_humidity_triggers_alert(self):
        reading = make_reading("high_humidity", humidity=80.0)
        alerts = self.detector.analyze(reading)
        categories = [a.category for a in alerts]
        self.assertIn(AlertCategory.HIGH_HUMIDITY, categories)
        humidity_alert = next(a for a in alerts if a.category == AlertCategory.HIGH_HUMIDITY)
        self.assertEqual(humidity_alert.severity, Severity.WARNING)

    def test_poor_air_quality_triggers_alert(self):
        reading = make_reading("poor_air_quality", aqi=160)
        alerts = self.detector.analyze(reading)
        categories = [a.category for a in alerts]
        self.assertIn(AlertCategory.POOR_AIR_QUALITY, categories)
        aq_alert = next(a for a in alerts if a.category == AlertCategory.POOR_AIR_QUALITY)
        self.assertEqual(aq_alert.severity, Severity.CRITICAL)

    def test_temperature_warning_not_critical(self):
        reading = make_reading("overheating", temperature=35.0)
        alerts = self.detector.analyze(reading)
        overheat_alerts = [a for a in alerts if a.category == AlertCategory.OVERHEATING]
        self.assertEqual(len(overheat_alerts), 1)
        self.assertEqual(overheat_alerts[0].severity, Severity.WARNING)


if __name__ == "__main__":
    unittest.main()