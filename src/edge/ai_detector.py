"""
AIDetector: AI-powered anomaly detection for Qwen-Sentinel with few-shot learning.

Uses Qwen LLM to analyze sensor data and detect anomalies beyond
what rule-based detection can catch. Implements few-shot learning
for consistent, high-quality detections.
"""
import json
from typing import Any, Dict, List, Optional

from src.common.models import Alert, AlertCategory, Severity


class AIDetector:
    """
    AI-powered anomaly detection using Qwen LLM with few-shot learning.
    
    Detects anomalies by analyzing sensor data patterns and providing
    confidence scores for each detection. Uses structured outputs for
    reliable, parseable results.
    """
    
    FEW_SHOT_EXAMPLES = """
    You are an environmental monitoring AI expert. Follow these examples:
    
    Example 1 - Critical Overheating:
    Input: Temperature=42°C, Humidity=60%, AQI=80
    Output:
    [
      {
        "anomaly_type": "overheating",
        "severity": "critical",
        "confidence": 0.98,
        "description": "Temperature 42°C exceeds critical threshold of 38°C",
        "suggested_action": "Activate emergency cooling systems immediately"
      }
    ]
    
    Example 2 - Intruder:
    Input: Motion=0.85, Objects=[person]
    Output:
    [
      {
        "anomaly_type": "intruder_detected",
        "severity": "critical",
        "confidence": 0.95,
        "description": "Person detected with motion level 0.85",
        "suggested_action": "Review security camera footage"
      }
    ]
    
    Example 3 - No Anomalies:
    Input: Temperature=22°C, Humidity=50%
    Output: []
    
    Rule: Only report anomalies with confidence >= 0.7
    """
    
    def __init__(self, qwen_client: Optional[any] = None, threshold: float = 0.8):
        self.qwen_client = qwen_client
        self.threshold = threshold
    
    def analyze(self, reading: Dict[str, Any]) -> List[Alert]:
        if self.qwen_client is None:
            return []
        
        sensors = reading.get("sensors", {})
        sensor_desc = self._build_sensor_description(sensors)
        environment_state = reading.get("environment_state", "unknown")
        
        prompt = f"""{self.FEW_SHOT_EXAMPLES}

Now analyze this sensor reading:

Sensor Data:
{sensor_desc}
Environment State: {environment_state}

Provide anomalies in JSON array format. Only report anomalies with confidence >= {self.threshold}."""
        
        response = self.qwen_client._call_qwen(prompt, temperature=0.1, max_tokens=500)
        anomalies = self._parse_anomaly_response(response)
        
        alerts = []
        for anomaly in anomalies:
            confidence = anomaly.get('confidence', 0.0)
            if confidence >= self.threshold:
                category = self._map_anomaly_type(anomaly.get('anomaly_type', ''))
                severity = self._map_severity(anomaly.get('severity', 'warning'))
                alerts.append(Alert(
                    category=category,
                    severity=severity,
                    message=anomaly.get('description', f"AI detected {anomaly.get('anomaly_type', 'anomaly')}"),
                    source_state=environment_state,
                    details={
                        'ai_detection': True,
                        'ai_confidence': confidence,
                        'ai_anomaly_type': anomaly.get('anomaly_type', 'unknown'),
                        'ai_suggested_action': anomaly.get('suggested_action', '')
                    }
                ))
        return alerts
    
    def _build_sensor_description(self, sensors: Dict[str, Any]) -> str:
        lines = []
        temp = sensors.get("temperature", {}).get("value", "N/A")
        lines.append(f"- Temperature: {temp} degree C (status: {sensors.get('temperature', {}).get('status', 'N/A')})")
        humidity = sensors.get("humidity", {}).get("value", "N/A")
        lines.append(f"- Humidity: {humidity}% (status: {sensors.get('humidity', {}).get('status', 'N/A')})")
        aqi = sensors.get("air_quality", {}).get("value", "N/A")
        lines.append(f"- Air Quality (AQI): {aqi} (status: {sensors.get('air_quality', {}).get('status', 'N/A')})")
        motion = sensors.get("motion", {}).get("value", "N/A")
        lines.append(f"- Motion: {motion} (status: {sensors.get('motion', {}).get('status', 'N/A')})")
        camera = sensors.get("camera", {})
        lines.append(f"- Brightness: {camera.get('brightness', 'N/A')} lux")
        lines.append(f"- Motion Level: {camera.get('motion_level', 'N/A')}")
        objects = camera.get("objects_detected", [])
        if objects:
            obj_str = ", ".join([obj.get('type', 'unknown') for obj in objects])
            lines.append(f"- Objects Detected: {obj_str}")
        facial = camera.get("facial_expression", "N/A")
        lines.append(f"- Facial Expression: {facial}")
        return "\n".join(lines)
    
    def _parse_anomaly_response(self, response: str) -> List[Dict[str, Any]]:
        if not response:
            return []
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return []
    
    def _map_anomaly_type(self, anomaly_type: str) -> AlertCategory:
        type_mapping = {
            'overheating': AlertCategory.OVERHEATING,
            'intruder_detected': AlertCategory.INTRUDER,
            'high_noise': AlertCategory.HIGH_NOISE,
            'low_light': AlertCategory.LOW_LIGHT,
            'high_humidity': AlertCategory.HIGH_HUMIDITY,
            'poor_air_quality': AlertCategory.POOR_AIR_QUALITY,
        }
        return type_mapping.get(anomaly_type.lower(), AlertCategory.OVERHEATING)
    
    def _map_severity(self, severity: str) -> Severity:
        severity_mapping = {
            'info': Severity.INFO,
            'warning': Severity.WARNING,
            'critical': Severity.CRITICAL,
        }
        return severity_mapping.get(severity.lower(), Severity.WARNING)
    
    def explain_detection(self, reading: Dict[str, Any], alert: Alert) -> str:
        if self.qwen_client is None:
            return "AI explanation not available"
        anomaly_type = alert.category.value
        return self.qwen_client.analyze_anomaly(reading, anomaly_type)
