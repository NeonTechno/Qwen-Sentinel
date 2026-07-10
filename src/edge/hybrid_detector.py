"""
HybridDetector: Combines rule-based and AI-powered anomaly detection.

Uses both EdgeDetector (fast, deterministic) and AIDetector (smart, adaptive)
for comprehensive anomaly detection in Qwen-Sentinel.
"""
from typing import Any, Dict, List, Optional

from src.edge.detector import EdgeDetector
from src.edge.ai_detector import AIDetector
from src.common.models import Alert, AlertCategory, Severity


class HybridDetector:
    """
    Hybrid anomaly detection combining rule-based and AI approaches.
    
    The detector first runs rule-based detection for fast, deterministic
    results, then optionally runs AI detection for more nuanced analysis.
    Results are merged, with AI detections added for new anomaly types.
    """
    
    def __init__(self, 
                 qwen_client: Optional[any] = None,
                 use_ai: bool = False,
                 ai_threshold: float = 0.8,
                 temperature_warning: float = 30.0,
                 temperature_critical: float = 38.0,
                 motion_intruder_threshold: float = 0.7,
                 motion_noise_threshold: float = 0.5,
                 brightness_low_lux: float = 35,
                 humidity_warning: float = 70.0,
                 humidity_critical: float = 85.0,
                 air_quality_warning: float = 100,
                 air_quality_critical: float = 150):
        """
        Initialize hybrid detector.
        
        Args:
            qwen_client: QwenClient instance for AI detection
            use_ai: Whether to enable AI detection
            ai_threshold: Minimum confidence for AI detections (0.0-1.0)
            temperature_warning: Temperature warning threshold in Celsius
            temperature_critical: Temperature critical threshold in Celsius
            motion_intruder_threshold: Motion threshold for intruder detection
            motion_noise_threshold: Motion level threshold for noise detection
            brightness_low_lux: Brightness threshold for low light detection
            humidity_warning: Humidity warning threshold in percentage
            humidity_critical: Humidity critical threshold in percentage
            air_quality_warning: AQI warning threshold
            air_quality_critical: AQI critical threshold
        """
        self.rule_detector = EdgeDetector(
            temperature_warning=temperature_warning,
            temperature_critical=temperature_critical,
            motion_intruder_threshold=motion_intruder_threshold,
            motion_noise_threshold=motion_noise_threshold,
            brightness_low_lux=brightness_low_lux,
            humidity_warning=humidity_warning,
            humidity_critical=humidity_critical,
            air_quality_warning=air_quality_warning,
            air_quality_critical=air_quality_critical
        )
        
        self.ai_detector = AIDetector(
            qwen_client=qwen_client,
            threshold=ai_threshold
        ) if use_ai and qwen_client else None
        
        self.use_ai = use_ai and qwen_client is not None
    
    def analyze(self, reading: Dict[str, Any]) -> List[Alert]:
        """
        Analyze sensor reading using both rule-based and AI detection.
        
        Args:
            reading: Sensor reading dictionary
            
        Returns:
            List of Alert objects for all detected anomalies
        """
        alerts = self.rule_detector.analyze(reading)
        
        if self.use_ai and self.ai_detector:
            ai_alerts = self.ai_detector.analyze(reading)
            
            existing_categories = {a.category for a in alerts}
            for ai_alert in ai_alerts:
                if ai_alert.category not in existing_categories:
                    alerts.append(ai_alert)
                else:
                    for i, existing_alert in enumerate(alerts):
                        if existing_alert.category == ai_alert.category:
                            severity_order = {
                                Severity.CRITICAL: 3,
                                Severity.WARNING: 2,
                                Severity.INFO: 1
                            }
                            if severity_order.get(ai_alert.severity, 0) > severity_order.get(existing_alert.severity, 0):
                                alerts[i] = ai_alert
                            break
        
        return alerts
    
    def get_detection_summary(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of detection results including both rule-based and AI analysis.
        
        Args:
            reading: Sensor reading dictionary
            
        Returns:
            Dictionary with detection summary
        """
        rule_alerts = self.rule_detector.analyze(reading)
        
        summary = {
            'rule_alerts': len(rule_alerts),
            'rule_categories': [a.category.value for a in rule_alerts],
            'ai_enabled': self.use_ai,
            'ai_alerts': 0,
            'ai_categories': []
        }
        
        if self.use_ai and self.ai_detector:
            ai_alerts = self.ai_detector.analyze(reading)
            summary['ai_alerts'] = len(ai_alerts)
            summary['ai_categories'] = [a.category.value for a in ai_alerts]
        
        return summary
    
    def explain_alert(self, reading: Dict[str, Any], alert: Alert) -> str:
        """
        Get explanation for a specific alert.
        
        Args:
            reading: The sensor reading
            alert: The alert to explain
            
        Returns:
            Explanation string
        """
        if alert.details.get('ai_detection'):
            if self.ai_detector:
                return self.ai_detector.explain_detection(reading, alert)
            return "AI detection (explanation not available)"
        
        return self._get_rule_explanation(alert)
    
    def _get_rule_explanation(self, alert: Alert) -> str:
        """Get explanation for rule-based alerts."""
        explanations = {
            AlertCategory.OVERHEATING: (
                "Temperature exceeded safe thresholds. "
                "This could indicate equipment malfunction, poor ventilation, "
                "or environmental heat sources."
            ),
            AlertCategory.INTRUDER: (
                "Motion or person detected in a restricted area. "
                "This could be an unauthorized person or unexpected movement."
            ),
            AlertCategory.HIGH_NOISE: (
                "Elevated noise levels detected. "
                "This could indicate equipment issues, loud events, or ambient noise."
            ),
            AlertCategory.LOW_LIGHT: (
                "Light levels are below acceptable thresholds. "
                "This could affect visibility and safety."
            ),
            AlertCategory.HIGH_HUMIDITY: (
                "Humidity levels are elevated. "
                "This could cause condensation, equipment damage, or discomfort."
            ),
            AlertCategory.POOR_AIR_QUALITY: (
                "Air quality index is high. "
                "This could indicate pollution, poor ventilation, or hazardous conditions."
            ),
        }
        return explanations.get(alert.category, "Alert triggered by rule-based detection")
    
    @property
    def is_ai_enabled(self) -> bool:
        """Check if AI detection is enabled."""
        return self.use_ai