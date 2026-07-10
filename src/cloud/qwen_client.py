"""
QwenClient: Client for Qwen Cloud API integration.

Provides natural language processing capabilities for Qwen-Sentinel,
including alert summarization, action suggestions, and anomaly analysis.
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
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.qwen.ai/v1"):
        """
        Initialize Qwen client.
        
        Args:
            api_key: Qwen Cloud API key. If None, will try to get from environment variable Qwen_Cloud_API
            base_url: Base URL for Qwen API
        """
        if api_key is None:
            api_key = os.getenv("Qwen_Cloud_API")
        
        self.api_key = api_key
        self.base_url = base_url
        self._validate_api_key()
    
    def _validate_api_key(self) -> None:
        """Validate that API key is available."""
        if not self.api_key:
            raise ValueError(
                "Qwen API key is required. Either pass it to QwenClient or set "
                "the Qwen_Cloud_API environment variable."
            )
    
    def generate_summary(self, sensor_data: Dict[str, Any], alerts: List[Any]) -> str:
        """
        Generate a natural language summary of sensor data and alerts.
        
        Args:
            sensor_data: The sensor reading data
            alerts: List of alert objects
            
        Returns:
            A human-readable summary string
        """
        alert_str = "\n".join([
            f"- [{a.get('severity', 'unknown').upper()}] {a.get('category', 'unknown')}: {a.get('message', '')}"
            for a in alerts
        ]) if alerts else "No active alerts"
        
        prompt = f"""You are an environmental monitoring AI assistant.
Analyze this sensor data and alerts, then provide a concise 2-3 sentence summary.

Sensor Data:
{json.dumps(sensor_data, indent=2)}

Active Alerts:
{alert_str}

Provide a brief, professional summary of the current environmental state."""
        
        return self._call_qwen(prompt, temperature=0.3, max_tokens=300)
    
    def suggest_actions(self, alerts: List[Any]) -> List[Dict[str, Any]]:
        """
        Suggest remediation actions for alerts.
        
        Args:
            alerts: List of alert objects
            
        Returns:
            List of action suggestions with priority and description
        """
        if not alerts:
            return []
            
        alert_str = "\n".join([
            f"- {a.get('message', str(a))}"
            for a in alerts
        ])
        
        prompt = f"""You are a facility management AI.
For these environmental alerts, suggest specific remediation actions.

Alerts:
{alert_str}

Format your response as a JSON array of action objects with these fields:
- action: string (what to do)
- priority: string (low, medium, high, critical)
- description: string (detailed explanation)

Return ONLY the JSON array, no other text."""
        
        response = self._call_qwen(prompt, temperature=0.2, max_tokens=500)
        
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
        
        return [
            {
                "action": "Review sensor data",
                "priority": "medium",
                "description": "Manually review the sensor readings and alerts"
            }
        ]
    
    def analyze_anomaly(self, reading: Dict[str, Any], anomaly_type: str) -> str:
        """
        Get detailed explanation for a specific anomaly.
        
        Args:
            reading: The sensor reading with the anomaly
            anomaly_type: Type of anomaly detected
            
        Returns:
            Detailed explanation string
        """
        prompt = f"""You are an environmental monitoring expert AI.
Explain why this sensor reading might indicate {anomaly_type}.

Sensor Data:
{json.dumps(reading, indent=2)}

Provide a 3-4 sentence technical explanation focusing on:
- What specific sensor values triggered the anomaly
- Why these values are concerning
- Potential causes
- Immediate implications"""
        
        return self._call_qwen(prompt, temperature=0.3, max_tokens=400)
    
    def _call_qwen(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """
        Call Qwen API with a prompt.
        
        Args:
            prompt: The text prompt to send to Qwen
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            The generated text response
        """
        if not self.api_key:
            raise ValueError("Qwen API key is not set")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen-plus",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0].get("message", {}).get("content", "")
            elif "output" in result:
                return result["output"]
            elif "text" in result:
                return result["text"]
            else:
                return str(result)
                
        except requests.exceptions.RequestException as e:
            print(f"Qwen API error: {e}")
            return f"[API Error: {str(e)}]"
        except json.JSONDecodeError as e:
            print(f"Qwen API response parse error: {e}")
            return f"[Response Parse Error: {str(e)}]"
    
    def check_connection(self) -> bool:
        """
        Test the API connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            test_prompt = "Say 'Qwen-Sentinel connection test successful'"
            response = self._call_qwen(test_prompt, temperature=0.0, max_tokens=10)
            return "successful" in response.lower()
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False