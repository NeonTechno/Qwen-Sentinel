"""
AlertManager with webhook support and AI integration for Qwen-Sentinel.
"""
import json
import time
from typing import Callable, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from src.common import config
from src.common.models import Alert

DispatchFn = Callable[[Alert], None]


def create_webhook_dispatcher(url: str, secret: Optional[str] = None) -> DispatchFn:
    """Create a dispatcher that sends alerts to a webhook URL."""
    def webhook_dispatch(alert: Alert) -> None:
        payload = json.dumps(alert.to_dict()).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if secret:
            headers["X-Webhook-Secret"] = secret
        req = Request(url, data=payload, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=5) as response:
                if response.status >= 400:
                    print(f"Webhook error: HTTP {response.status}")
        except HTTPError as e:
            print(f"Webhook HTTP error: {e.code} - {e.reason}")
        except URLError as e:
            print(f"Webhook URL error: {e.reason}")
        except Exception as e:
            print(f"Webhook dispatch failed: {str(e)}")
    return webhook_dispatch


class AlertManager:
    """
    Manages alert deduplication, dispatching, and AI-powered enhancements.
    
    Features:
    - Per-category cooldown to prevent alert spam
    - Pluggable dispatcher (console, webhook, custom)
    - Optional AI integration for natural language summaries
    """
    
    def __init__(self,
                 cooldown_seconds: float = config.DEFAULT_ALERT_COOLDOWN_SECONDS,
                 dispatcher: Optional[DispatchFn] = None,
                 qwen_client: Optional[any] = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        """
        Initialize AlertManager.
        
        Args:
            cooldown_seconds: Seconds before repeating same alert category
            dispatcher: Custom function to dispatch alerts
            qwen_client: Optional QwenClient for AI-powered features
            clock: Time function for testing (defaults to time.monotonic)
        """
        self.cooldown_seconds = cooldown_seconds
        self.dispatcher = dispatcher or self._default_dispatch
        self.qwen_client = qwen_client
        self._clock = clock
        self._last_sent: Dict[str, float] = {}
        self.sent_log: List[Alert] = []
    
    def process(self, alerts: List[Alert], reading: Optional[Dict[str, any]] = None) -> List[Alert]:
        """
        Process alerts through deduplication and optional AI enhancement.
        
        Args:
            alerts: List of Alert objects to process
            reading: Optional sensor reading for AI context
            
        Returns:
            List of dispatched Alert objects
        """
        dispatched: List[Alert] = []
        
        for alert in alerts:
            key = f"{alert.category.value}:{alert.severity.value}"
            
            if self._in_cooldown(key):
                continue
            
            if self.qwen_client and reading:
                self._add_ai_summary(alert, reading)
            
            self._last_sent[key] = self._clock()
            self.dispatcher(alert)
            self.sent_log.append(alert)
            dispatched.append(alert)
        
        if self.qwen_client and reading and dispatched:
            self._print_ai_batch_summary(reading, dispatched)
        
        return dispatched
    
    def _add_ai_summary(self, alert: Alert, reading: Dict[str, any]) -> None:
        """Add AI-generated summary to alert details."""
        try:
            summary = self.qwen_client.generate_summary(reading, [alert])
            alert.details["ai_summary"] = summary
            
            suggestions = self.qwen_client.suggest_actions([alert])
            if suggestions:
                alert.details["ai_suggestions"] = suggestions
        except Exception as e:
            alert.details["ai_error"] = str(e)
    
    def _print_ai_batch_summary(self, reading: Dict[str, any], alerts: List[Alert]) -> None:
        """Print AI-generated summary for a batch of alerts."""
        try:
            summary = self.qwen_client.generate_summary(reading, alerts)
            print(f"\n AI Summary: {summary}\n")
        except Exception as e:
            print(f"\n AI Summary: [Error: {str(e)}]\n")
    
    def _in_cooldown(self, key: str) -> bool:
        """Check if an alert category is in cooldown."""
        last = self._last_sent.get(key)
        if last is None:
            return False
        return (self._clock() - last) < self.cooldown_seconds
    
    @staticmethod
    def format_alert(alert: Alert) -> str:
        """Format alert for console output."""
        base = f"[{alert.severity.value.upper()}] {alert.category.value}: {alert.message}"
        
        if "ai_summary" in alert.details:
            base += f"\n   AI: {alert.details['ai_summary']}"
        
        return base
    
    def _default_dispatch(self, alert: Alert) -> None:
        """Default dispatcher prints formatted alert to console."""
        print(self.format_alert(alert))
    
    @property
    def has_ai(self) -> bool:
        """Check if AI features are enabled."""
        return self.qwen_client is not None