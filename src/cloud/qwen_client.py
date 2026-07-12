"""
QwenClient: Advanced client for Qwen Cloud API integration.

Provides natural language processing capabilities for Qwen-Sentinel,
including alert summarization, action suggestions, anomaly analysis,
and structured outputs for reliable AI interactions.
"""
import json
import os
from typing import Any, Dict, List, Optional
import requests


class QwenClient:
    """
    Client for interacting with Qwen Cloud API.
    
    Handles authentication, API calls, and response parsing for
    integrating Qwen LLM capabilities into Qwen-Sentinel.
    """
    
    FEW_SHOT_EXAMPLES = {
        'anomaly_detection': """
        You are an environmental monitoring AI expert. Follow these examples:
        
        Example 1 - Critical Overheating:
        Input: Temperature=42°C, Humidity=60%
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
        Input: Temperature=22°C
        Output: []
        
        Rule: Only report anomalies with confidence >= 0.7
        """
    }
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.qwen.ai/v1"):
        if api_key is None:
            api_key = os.getenv("Qwen_Cloud_API")
        self.api_key = api_key
        self.base_url = base_url
        self._validate_api_key()
    
    def _validate_api_key(self) -> None:
        if not self.api_key:
            raise ValueError("Qwen API key required. Set Qwen_Cloud_API env var or pass api_key")
    
    def generate_summary(self, sensor_data: Dict[str, Any], alerts: List[Any]) -> str:
        alert_str = "No active alerts" if not alerts else "\n".join([f"- [{a.get('severity', 'unknown').upper()}] {a.get('category', 'unknown')}: {a.get('message', '')}" for a in alerts])
        prompt = f"""You are an environmental monitoring AI. Analyze this data:

Sensor Data:
{json.dumps(sensor_data, indent=2)}

Active Alerts:
{alert_str}

Provide a 2-3 sentence professional summary."""
        return self._call_qwen(prompt, temperature=0.3, max_tokens=300)
    
    def detect_anomalies(self, reading: Dict[str, Any]) -> List[Dict[str, Any]]:
        sensor_desc = self._build_sensor_description(reading.get("sensors", {}))
        prompt = f"""{self.FEW_SHOT_EXAMPLES['anomaly_detection']}

Now analyze:
{sensor_desc}

Return ONLY valid JSON array of anomalies or empty array []."""
        response = self._call_qwen(prompt, temperature=0.1, max_tokens=500)
        return self._parse_json_array(response)
    
    def suggest_actions(self, alerts: List[Any]) -> List[Dict[str, Any]]:
        if not alerts:
            return []
        alert_str = "\n".join([f"- {a.get('message', str(a))}" for a in alerts])
        prompt = f"""You are a facility management AI. For these alerts:
{alert_str}

Suggest 1-3 specific remediation actions as JSON array:
[{{"action": "...", "priority": "high/medium/low", "description": "..."}}]
Return ONLY valid JSON array."""
        response = self._call_qwen(prompt, temperature=0.2, max_tokens=400)
        return self._parse_json_array(response)
    
    def analyze_anomaly(self, reading: Dict[str, Any], anomaly_type: str) -> str:
        prompt = f"""Explain why this sensor reading indicates {anomaly_type}:

{json.dumps(reading, indent=2)}

Provide 3-4 sentence technical explanation."""
        return self._call_qwen(prompt, temperature=0.3, max_tokens=400)
    
    def _build_sensor_description(self, sensors: Dict[str, Any]) -> str:
        lines = []
        temp = sensors.get("temperature", {}).get("value", "N/A")
        lines.append(f"- Temperature: {temp} degree C")
        humidity = sensors.get("humidity", {}).get("value", "N/A")
        lines.append(f"- Humidity: {humidity}%")
        aqi = sensors.get("air_quality", {}).get("value", "N/A")
        lines.append(f"- Air Quality (AQI): {aqi}")
        motion = sensors.get("motion", {}).get("value", "N/A")
        lines.append(f"- Motion: {motion}")
        return "\n".join(lines)
    
    def _call_qwen(self, prompt: str, temperature: float, max_tokens: int) -> str:
        if not self.api_key:
            raise ValueError("Qwen API key not set")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": "qwen-plus", "messages": [{"role": "user", "content": prompt}], "temperature": temperature, "max_tokens": max_tokens}
        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            if "choices" in result and result["choices"]:
                return result["choices"][0].get("message", {}).get("content", "")
            return str(result)
        except Exception as e:
            print(f"Qwen API error: {e}")
            return f"[API Error: {str(e)}]"
    
    def _parse_json_array(self, response: str) -> List[Dict[str, Any]]:
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
    
    def check_connection(self) -> bool:
        try:
            response = self._call_qwen("Say connection test successful", temperature=0.0, max_tokens=10)
            return "successful" in response.lower()
        except:
            return False