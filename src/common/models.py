"""
Shared data models for Qwen-Sentinel.

Alert is the common currency between EdgeDetector (which raises them),
MemoryAgent (which records them), and AlertManager (which dedupes and
dispatches them).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertCategory(Enum):
    OVERHEATING = "overheating"
    INTRUDER = "intruder_detected"
    HIGH_NOISE = "high_noise"
    LOW_LIGHT = "low_light"
    HIGH_HUMIDITY = "high_humidity"
    POOR_AIR_QUALITY = "poor_air_quality"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class Alert:
    category: AlertCategory
    severity: Severity
    message: str
    timestamp: str = field(default_factory=_utc_now_iso)
    source_state: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "source_state": self.source_state,
            "details": self.details,
        }