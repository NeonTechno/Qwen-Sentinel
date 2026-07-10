"""
AIDetector: AI-powered anomaly detection for Qwen-Sentinel.

Uses Qwen LLM to analyze sensor data and detect anomalies beyond
what rule-based detection can catch. Works alongside EdgeDetector
for hybrid detection.
"""
import json
from typing import Any, Dict, List, Optional

from src.common.models import Alert, AlertCategory, Severity


class AIDetector:
    """
    AI-powered anomaly detection using Qwen LLM.
    
    Detects anomalies by analyzing sensor data patterns and providing
    confidence scores for each detection.
    """
    
    def __init__(self, qwen_client: Optional[any] = None, 
                 threshold: float = 0.8):
        """
        Initialize AI detector.
        
        Args:
            qwen_client: QwenClient instance for API calls
            threshold: Minimum confidence score (0.0-1.0) to trigger an alert
        """
        self.qwen_client = qwen_client
        self.threshold = threshold
    
    def analyze(self, reading: Dict[str, Any]) -> List[Alert]:
        """
        Analyze sensor reading using AI for anomaly detection.
        
        Args:
            reading: Sensor reading dictionary
            
        Returns:
            List of Alert objects for detected anomalies
        """
        if self.qwen_client is None:
            return []
        
        sensors = reading.get("sensors", {})
        environment_state = reading.get("environment_state", "unknown")
        
        sensor_desc = self._build_sensor_description(sensors)
        
        prompt = f"""You are an environmental monitoring AI expert.
Analyze this sensor data and identify any anomalies or concerning patterns.

Sensor Data:
{sensor_desc}

Environment State: {environment_state}

For each anomaly you detect, provide:
1. anomaly_type: One of these exact values: overheating, intruder_detected, high_noise, low_light, high_humidity, poor_air_quality
2. severity: One of: info, warning, critical
3. confidence: Number between 0.0 and 1.0
4. description: Brief explanation of the anomaly

Format your response as a JSON array:
[{{"anomaly_type": "...", "severity": "...", "confidence": X.X, "description": "..."}}]

Only report anomalies with confidence >= {self.threshold}.
If no anomalies, return empty array [].
Return ONLY the JSON array, no other text or explanation."""
        
        response = self.qwen_client._call_qwen(
            prompt, 
            temperature=0.1,  
            max_tokens=500
        )
        
        alerts = self._parse_ai_response(response, reading)
        return alerts
    
    def _build_sensor_description(self, sensors: Dict[str, Any]) -> str:
        """Build a human-readable description of sensor data."""
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
            obj_str = ", ".join([obj.get("type", "unknown") for obj in objects])
            lines.append(f"- Objects Detected: {obj_str}")
        
        facial = camera.get("facial_expression", "N/A")
        lines.append(f"- Facial Expression: {facial}")
        
        return "\n".join(lines)
    
    def _parse_ai_response(self, response: str, reading: Dict[str, Any]) -> List[Alert]:
        """Parse AI response into Alert objects."""
        alerts = []
        
        if not response or response.startswith("[API Error") or response.startswith("[Response"):
            return alerts
        
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start >= 0 and end > start:
                anomalies = json.loads(response[start:end])
                
                for anomaly in anomalies:
                    category = self._map_anomaly_type(anomaly.get('anomaly_type', ''))
                    severity = self._map_severity(anomaly.get('severity', 'warning'))
                    confidence = anomaly.get('confidence', 0.0)
                    
                    if confidence >= self.threshold:
                        alert = Alert(
                            category=category,
                            severity=severity,
                            message=anomaly.get('description', f"AI detected {anomaly.get('anomaly_type', 'anomaly')}"),
                            source_state=reading.get('environment_state'),
                            details={
                                'ai_detection': True,
                                'ai_confidence': confidence,
                                'ai_anomaly_type': anomaly.get('anomaly_type', 'unknown')
                            }
                        )
                        alerts.append(alert)
                        
        except (json.JSONDecodeError, ValueError) as e:
            print(f"AI response parse error: {e}")
        
        return alerts
    
    def _map_anomaly_type(self, anomaly_type: str) -> AlertCategory:
        """Map string anomaly type to AlertCategory enum."""
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
        """Map string severity to Severity enum."""
        severity_mapping = {
            'info': Severity.INFO,
            'warning': Severity.WARNING,
            'critical': Severity.CRITICAL,
        }
        return severity_mapping.get(severity.lower(), Severity.WARNING)
    
    def explain_detection(self, reading: Dict[str, Any], alert: Alert) -> str:
        """
        Get AI explanation for a specific detection.
        
        Args:
            reading: The sensor reading
            alert: The alert to explain
            
        Returns:
            AI-generated explanation
        """
        if self.qwen_client is None:
            return f"AI explanation not available (no Qwen client)"
        
        anomaly_type = alert.category.value
        return self.qwen_client.analyze_anomaly(reading, anomaly_type)