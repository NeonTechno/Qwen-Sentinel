"""Unit tests for AIDetector."""
import unittest
from unittest.mock import MagicMock, patch

from src.common.models import Alert, AlertCategory, Severity
from src.edge.ai_detector import AIDetector


class TestAIDetector(unittest.TestCase):
    def test_init_without_qwen_client(self):
        """Test AIDetector initialization without Qwen client."""
        detector = AIDetector(qwen_client=None)
        self.assertIsNone(detector.qwen_client)
        self.assertEqual(detector.threshold, 0.8)

    def test_init_with_qwen_client(self):
        """Test AIDetector initialization with Qwen client."""
        mock_client = MagicMock()
        detector = AIDetector(qwen_client=mock_client, threshold=0.7)
        self.assertEqual(detector.qwen_client, mock_client)
        self.assertEqual(detector.threshold, 0.7)

    def test_analyze_without_client_returns_empty(self):
        """Test that analyze returns empty list without Qwen client."""
        detector = AIDetector(qwen_client=None)
        reading = {"sensors": {}, "environment_state": "normal"}
        result = detector.analyze(reading)
        self.assertEqual(result, [])

    @patch.object(AIDetector, '_parse_ai_response')
    def test_analyze_with_client(self, mock_parse):
        """Test analyze method with Qwen client."""
        mock_client = MagicMock()
        mock_client._call_qwen.return_value = '[{"anomaly_type": "overheating", "severity": "critical", "confidence": 0.9, "description": "Test"}]'
        
        mock_parse.return_value = [
            Alert(
                category=AlertCategory.OVERHEATING,
                severity=Severity.CRITICAL,
                message="Test",
                details={'ai_detection': True}
            )
        ]
        
        detector = AIDetector(qwen_client=mock_client)
        reading = {"sensors": {"temperature": {"value": 40}}, "environment_state": "overheating"}
        
        result = detector.analyze(reading)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].category, AlertCategory.OVERHEATING)

    def test_build_sensor_description(self):
        """Test sensor description building."""
        detector = AIDetector()
        sensors = {
            "temperature": {"value": 25, "status": "ok"},
            "humidity": {"value": 50, "status": "ok"},
            "air_quality": {"value": 50, "status": "good"},
            "motion": {"value": 0.1, "status": "ok"},
            "camera": {
                "brightness": 100,
                "motion_level": 0.1,
                "objects_detected": [{"type": "person"}],
                "facial_expression": "neutral"
            }
        }
        
        result = detector._build_sensor_description(sensors)
        self.assertIn("Temperature: 25", result)
        self.assertIn("Humidity: 50", result)
        self.assertIn("Air Quality (AQI): 50", result)

    def test_map_anomaly_type(self):
        """Test anomaly type mapping."""
        detector = AIDetector()
        
        self.assertEqual(detector._map_anomaly_type("overheating"), AlertCategory.OVERHEATING)
        self.assertEqual(detector._map_anomaly_type("intruder_detected"), AlertCategory.INTRUDER)
        self.assertEqual(detector._map_anomaly_type("high_noise"), AlertCategory.HIGH_NOISE)
        self.assertEqual(detector._map_anomaly_type("low_light"), AlertCategory.LOW_LIGHT)
        self.assertEqual(detector._map_anomaly_type("high_humidity"), AlertCategory.HIGH_HUMIDITY)
        self.assertEqual(detector._map_anomaly_type("poor_air_quality"), AlertCategory.POOR_AIR_QUALITY)
        self.assertEqual(detector._map_anomaly_type("unknown_type"), AlertCategory.OVERHEATING)

    def test_map_severity(self):
        """Test severity mapping."""
        detector = AIDetector()
        
        self.assertEqual(detector._map_severity("info"), Severity.INFO)
        self.assertEqual(detector._map_severity("warning"), Severity.WARNING)
        self.assertEqual(detector._map_severity("critical"), Severity.CRITICAL)
        self.assertEqual(detector._map_severity("unknown"), Severity.WARNING)

    @patch.object(AIDetector, '_parse_ai_response')
    def test_analyze_threshold_filtering(self, mock_parse):
        """Test that alerts below threshold are filtered out."""
        mock_client = MagicMock()
        
        def parse_side_effect(response, reading):
            return [
                Alert(
                    category=AlertCategory.OVERHEATING,
                    severity=Severity.WARNING,
                    message="Low confidence alert",
                    details={'ai_confidence': 0.7}
                )
            ]
        
        mock_parse.side_effect = parse_side_effect
        
        detector = AIDetector(qwen_client=mock_client, threshold=0.8)
        reading = {"sensors": {}, "environment_state": "normal"}
        
        result = detector.analyze(reading)
        self.assertEqual(result, [])

    @patch('src.cloud.qwen_client.QwenClient')
    def test_explain_detection(self, mock_qwen_client):
        """Test explain_detection method."""
        mock_client = MagicMock()
        mock_client.analyze_anomaly.return_value = "Detailed explanation"
        mock_qwen_client.return_value = mock_client
        
        detector = AIDetector(qwen_client=mock_client)
        reading = {"sensors": {}}
        alert = Alert(
            category=AlertCategory.OVERHEATING,
            severity=Severity.CRITICAL,
            message="Test alert"
        )
        
        result = detector.explain_detection(reading, alert)
        self.assertEqual(result, "Detailed explanation")


if __name__ == "__main__":
    unittest.main()