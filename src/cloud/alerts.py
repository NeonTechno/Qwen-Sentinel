"""
AlertManager: dedupes and dispatches Alert objects raised by EdgeDetector,
applying a per-category cooldown so a persistent anomaly doesn't spam the
same channel every cycle.
"""
import time
from typing import Callable, Dict, List, Optional

from src.common import config
from src.common.models import Alert

DispatchFn = Callable[[Alert], None]


class AlertManager:
    def __init__(
        self,
        cooldown_seconds: float = config.DEFAULT_ALERT_COOLDOWN_SECONDS,
        dispatcher: Optional[DispatchFn] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
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
