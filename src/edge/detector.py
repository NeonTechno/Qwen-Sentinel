"""
EdgeDetector: rule-based anomaly detection over Qwen-Sentinel sensor payloads.

Runs close to the data source (no cloud round-trip required) and emits a
list of Alert objects for any thresholds crossed in a single sensor reading
from simulator.generate_sensor_data().
"""
from typing import Any, Dict, List

from src.common import config
from src.common.models import Alert, AlertCategory, Severity


class EdgeDetector:
    def __init__(
        self,
        temperature_warning: float = config.TEMPERATURE_WARNING_C,
        temperature_critical: float = config.TEMPERATURE_CRITICAL_C,
        motion_intruder_threshold: float = config.MOTION_INTRUDER_THRESHOLD,
        motion_noise_threshold: float = config.MOTION_NOISE_THRESHOLD,
        brightness_low_lux: float = config.BRIGHTNESS_LOW_LUX,
    ) -> None:
        self.temperature_warning = temperature_warning
        self.temperature_critical = temperature_critical
        self.motion_intruder_threshold = motion_intruder_threshold
        self.motion_noise_threshold = motion_noise_threshold
        self.brightness_low_lux = brightness_low_lux

    def analyze(self, reading: Dict[str, Any]) -> List[Alert]:
        """Run every rule against a single sensor payload and return raised alerts."""
        source_state = reading.get("environment_state")
        alerts: List[Alert] = []
        alerts.extend(self._check_temperature(reading, source_state))
        alerts.extend(self._check_intruder(reading, source_state))
        alerts.extend(self._check_noise(reading, source_state))
        alerts.extend(self._check_low_light(reading, source_state))
        return alerts

    def _check_temperature(self, reading: Dict[str, Any], source_state) -> List[Alert]:
        temp = reading.get("sensors", {}).get("temperature", {}).get("value")
        if temp is None:
            return []
        if temp >= self.temperature_critical:
            return [Alert(
                category=AlertCategory.OVERHEATING,
                severity=Severity.CRITICAL,
                message=f"Critical overheating: {temp:.1f}C exceeds {self.temperature_critical}C",
                source_state=source_state,
                details={"temperature_c": temp},
            )]
        if temp >= self.temperature_warning:
            return [Alert(
                category=AlertCategory.OVERHEATING,
                severity=Severity.WARNING,
                message=f"Elevated temperature: {temp:.1f}C exceeds {self.temperature_warning}C",
                source_state=source_state,
                details={"temperature_c": temp},
            )]
        return []

    def _check_intruder(self, reading: Dict[str, Any], source_state) -> List[Alert]:
        sensors = reading.get("sensors", {})
        camera = sensors.get("camera", {}) or {}
        motion = sensors.get("motion", {}).get("value", 0.0)
        objects = camera.get("objects_detected", []) or []
        has_person = any(obj.get("type") == "person" for obj in objects)

        if has_person or motion >= self.motion_intruder_threshold:
            return [Alert(
                category=AlertCategory.INTRUDER,
                severity=Severity.CRITICAL,
                message="Possible intruder detected (person object and/or high motion)",
                source_state=source_state,
                details={"motion": motion, "objects_detected": objects},
            )]
        return []

    def _check_noise(self, reading: Dict[str, Any], source_state) -> List[Alert]:
        camera = reading.get("sensors", {}).get("camera", {}) or {}
        objects = camera.get("objects_detected", []) or []
        motion_level = camera.get("motion_level", 0.0)
        has_noise_object = any(obj.get("type") == "noise_source" for obj in objects)

        if has_noise_object or motion_level >= self.motion_noise_threshold:
            return [Alert(
                category=AlertCategory.HIGH_NOISE,
                severity=Severity.WARNING,
                message="Elevated ambient noise/activity level detected",
                source_state=source_state,
                details={"motion_level": motion_level, "objects_detected": objects},
            )]
        return []

    def _check_low_light(self, reading: Dict[str, Any], source_state) -> List[Alert]:
        camera = reading.get("sensors", {}).get("camera", {}) or {}
        brightness = camera.get("brightness")
        if brightness is not None and brightness < self.brightness_low_lux:
            return [Alert(
                category=AlertCategory.LOW_LIGHT,
                severity=Severity.INFO,
                message=f"Low light conditions: {brightness} lux",
                source_state=source_state,
                details={"brightness_lux": brightness},
            )]
        return []
