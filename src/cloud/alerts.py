"""
AlertManager with webhook support for Qwen-Sentinel.
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
    def __init__(self, cooldown_seconds: float = config.DEFAULT_ALERT_COOLDOWN_SECONDS, dispatcher: Optional[DispatchFn] = None, clock: Callable[[], float] = time.monotonic) -> None:
        self.cooldown_seconds = cooldown_seconds
        self.dispatcher = dispatcher or self._default_dispatch
        self._clock = clock
        self._last_sent: Dict[str, float] = {}
        self.sent_log: List[Alert] = []

    def process(self, alerts: List[Alert]) -> List[Alert]:
        dispatched: List[Alert] = []
        for alert in alerts:
            key = f"{alert.category.value}:{alert.severity.value}"
            if self._in_cooldown(key):
                continue
            self._last_sent[key] = self._clock()
            self.dispatcher(alert)
            self.sent_log.append(alert)
            dispatched.append(alert)
        return dispatched

    def _in_cooldown(self, key: str) -> bool:
        last = self._last_sent.get(key)
        if last is None:
            return False
        return (self._clock() - last) < self.cooldown_seconds

    @staticmethod
    def format_alert(alert: Alert) -> str:
        return f"[{alert.severity.value.upper()}] {alert.category.value}: {alert.message}"

    def _default_dispatch(self, alert: Alert) -> None:
        print(self.format_alert(alert))