"""Unit tests for HybridDetector."""
import unittest
from unittest.mock import MagicMock, patch

from src.common.models import Alert, AlertCategory, Severity
from src.edge.hybrid_detector import HybridDetector


class TestHybridDetector(unittest.TestCase):
    def test_init_without_ai(self):
        """Test HybridDetector initialization without AI."""
        detector = HybridDetector(use_ai=False)
        self.assertIsNotNone(detector.rule_detector)
        self.assertIsNone(detector.ai_detector)
        self.assertFalse(detector.use_ai)

    def test_init_with_ai(self):
        """Test HybridDetector initialization with AI."""
        mock_client = MagicMock()
        detector = HybridDetector(qwen_client=mock_client, use_ai=True)
        self.assertIsNotNone(detector.rule_detector)
        self.assertIsNotNone(detector.ai_detector)
        self.assertTrue(detector.use_ai)

    def test_analyze_without_ai(self):
        """Test analyze method without AI enabled."""
        detector = HybridDetector(use_ai=False)
        reading = {
            "sensors": {
                "temperature": {"value": 40, "unit": "C", "status": "warning"},
                "camera": {"brightness": 100, "motion_level": 0.1, "objects_detected": [], "facial_expression": "neutral"},
                "motion": {"value": 0.1, "unit": "normalized", "status": "ok"},
                "humidity": {"value": 50, "unit": "%", "status": "ok"},
                "air_quality": {"value": 50, "unit": "AQI", "status": "good"}
            },
            "environment_state": "overheating"
        }
        
        result = detector.analyze(reading)
        self.assertGreater(len(result), 0)
        categories = [a.category for a in result]
        self.assertIn(AlertCategory.OVERHEATING, categories)

    @patch.object(HybridDetector, 'ai_detector', new_callable=lambda: MagicMock())
    def test_analyze_with_ai(self, mock_ai):
        """Test analyze method with AI enabled."""
        mock_client = MagicMock()
        mock_ai.return_value.analyze.return_value = []
        
        detector = HybridDetector(qwen_client=mock_client, use_ai=True)
        reading = {
            "sensors": {
                "temperature": {"value": 40, "unit": "C", "status": "warning"},
                "camera": {"brightness": 100, "motion_level": 0.1, "objects_detected": [], "facial_expression": "neutral"},
                "motion": {"value": 0.1, "unit": "normalized", "status": "ok"},
                "humidity": {"value": 50, "unit": "%", "status": "ok"},
                "air_quality": {"value": 50, "unit": "AQI", "status": "good"}
            },
            "environment_state": "overheating"
        }
        
        result = detector.analyze(reading)
        self.assertGreater(len(result), 0)

    def test_get_detection_summary(self):
        """Test get_detection_summary method."""
        detector = HybridDetector(use_ai=False)
        reading = {
            "sensors": {
                "temperature": {"value": 40, "unit": "C", "status": "warning"},
                "camera": {"brightness": 100, "motion_level": 0.1, "objects_detected": [], "facial_expression": "neutral"},
                "motion": {"value": 0.1, "unit": "normalized", "status": "ok"},
                "humidity": {"value": 50, "unit": "%", "status": "ok"},
                "air_quality": {"value": 50, "unit": "AQI", "status": "good"}
            },
            "environment_state": "overheating"
        }
        
        summary = detector.get_detection_summary(reading)
        self.assertIn('rule_alerts', summary)
        self.assertIn('rule_categories', summary)
        self.assertIn('ai_enabled', summary)
        self.assertFalse(summary['ai_enabled'])

    def test_explain_alert_rule_based(self):
        """Test explain_alert for rule-based alerts."""
        detector = HybridDetector(use_ai=False)
        reading = {"sensors": {}}
        alert = Alert(
            category=AlertCategory.OVERHEATING,
            severity=Severity.CRITICAL,
            message="Critical overheating"
        )
        
        result = detector.explain_alert(reading, alert)
        self.assertIn("Temperature", result)

    def test_is_ai_enabled_property(self):
        """Test is_ai_enabled property."""
        detector_no_ai = HybridDetector(use_ai=False)
        self.assertFalse(detector_no_ai.is_ai_enabled)
        
        mock_client = MagicMock()
        detector_with_ai = HybridDetector(qwen_client=mock_client, use_ai=True)
        self.assertTrue(detector_with_ai.is_ai_enabled)


if __name__ == "__main__":
    unittest.main()