"""
EdgeDetector: rule-based anomaly detection for Qwen-Sentinel.
"""
from typing import Any, Dict, List
from src.common import config
from src.common.models import Alert, AlertCategory, Severity


class EdgeDetector:
    def __init__(self, temperature_warning: float = config.TEMPERATURE_WARNING_C, temperature_critical: float = config.TEMPERATURE_CRITICAL_C, motion_intruder_threshold: float = config.MOTION_INTRUDER_THRESHOLD, motion_noise_threshold: float = config.MOTION_NOISE_THRESHOLD, brightness_low_lux: float = config.BRIGHTNESS_LOW_LUX, humidity_warning: float = config.HUMIDITY_WARNING_PERCENT, humidity_critical: float = config.HUMIDITY_CRITICAL_PERCENT, air_quality_warning: float = config.AIR_QUALITY_WARNING_AQI, air_quality_critical: float = config.AIR_QUALITY_CRITICAL_AQI) -> None:
        self.temperature_warning = temperature_warning
        self.temperature_critical = temperature_critical
        self.motion_intruder_threshold = motion_intruder_threshold
        self.motion_noise_threshold = motion_noise_threshold
        self.brightness_low_lux = brightness_low_lux
        self.humidity_warning = humidity_warning
        self.humidity_critical = humidity_critical
        self.air_quality_warning = air_quality_warning
        self.air_quality_critical = air_quality_critical

    def analyze(self, reading: Dict[str, Any]) -> List[Alert]:
        source_state = reading.get("environment_state")
        alerts: List[Alert] = []
        alerts.extend(self._check_temperature(reading, source_state))
        alerts.extend(self._check_intruder(reading, source_state))
        alerts.extend(self._check_noise(reading, source_state))
        alerts.extend(self._check_low_light(reading, source_state))
        alerts.extend(self._check_humidity(reading, source_state))
        alerts.extend(self._check_air_quality(reading, source_state))
        return alerts

    def _check_temperature(self, reading: Dict[str, Any], source_state) -> List[Alert]:
        temp = reading.get("sensors", {}).get("temperature", {}).get("value")
        if temp is None:
            return []
        alerts = []
        if temp >= self.temperature_critical:
            alerts.append(Alert(category=AlertCategory.OVERHEATING, severity=Severity.CRITICAL, message=f"Critical overheating: {temp:.1f}C exceeds {self.temperature_critical}C", source_state=source_state, details={"temperature_c": temp}))
        elif temp >= self.temperature_warning:
            alerts.append(Alert(category=AlertCategory.OVERHEATING, severity=Severity.WARNING, message=f"Elevated temperature: {temp:.1f}C exceeds {self.temperature_warning}C", source_state=source_state, details={"temperature_c": temp}))
        return alerts

    def _check_intruder(self, reading: Dict[str, Any], source_state) -> List[Alert]:
        sensors = reading.get("sensors", {})
        camera = sensors.get("camera", {}) or {}
        motion = sensors.get("motion", {}).get("value", 0.0)
        objects = camera.get("objects_detected", []) or []
        has_person = any(obj.get("type") == "person" for obj in objects)
        if has_person or motion >= self.motion_intruder_threshold:
            return [Alert(category=AlertCategory.INTRUDER, severity=Severity.CRITICAL, message="Possible intruder detected", source_state=source_state, details={"motion": motion, "objects_detected": objects})]
        return []

    def _check_noise(self, reading: Dict[str, Any], source_state) -> List[Alert]:
        camera = reading.get("sensors", {}).get("camera", {}) or {}
        objects = camera.get("objects_detected", []) or []
        motion_level = camera.get("motion_level", 0.0)
        has_noise_object = any(obj.get("type") == "noise_source" for obj in objects)
        if has_noise_object or motion_level >= self.motion_noise_threshold:
            return [Alert(category=AlertCategory.HIGH_NOISE, severity=Severity.WARNING, message="Elevated ambient noise/activity level detected", source_state=source_state, details={"motion_level": motion_level, "objects_detected": objects})]
        return []

    def _check_low_light(self, reading: Dict[str, Any], source_state) -> List[Alert]:
        camera = reading.get("sensors", {}).get("camera", {}) or {}
        brightness = camera.get("brightness")
        if brightness is not None and brightness < self.brightness_low_lux:
            return [Alert(category=AlertCategory.LOW_LIGHT, severity=Severity.INFO, message=f"Low light conditions: {brightness} lux", source_state=source_state, details={"brightness_lux": brightness})]
        return []

    def _check_humidity(self, reading: Dict[str, Any], source_state) -> List[Alert]:
        humidity = reading.get("sensors", {}).get("humidity", {}).get("value")
        if humidity is None:
            return []
        alerts = []
        if humidity >= self.humidity_critical:
            alerts.append(Alert(category=AlertCategory.HIGH_HUMIDITY, severity=Severity.CRITICAL, message=f"Critical humidity: {humidity:.1f}% exceeds {self.humidity_critical}%", source_state=source_state, details={"humidity_percent": humidity}))
        elif humidity >= self.humidity_warning:
            alerts.append(Alert(category=AlertCategory.HIGH_HUMIDITY, severity=Severity.WARNING, message=f"High humidity: {humidity:.1f}% exceeds {self.humidity_warning}%", source_state=source_state, details={"humidity_percent": humidity}))
        return alerts

    def _check_air_quality(self, reading: Dict[str, Any], source_state) -> List[Alert]:
        aqi = reading.get("sensors", {}).get("air_quality", {}).get("value")
        if aqi is None:
            return []
        alerts = []
        if aqi >= self.air_quality_critical:
            alerts.append(Alert(category=AlertCategory.POOR_AIR_QUALITY, severity=Severity.CRITICAL, message=f"Hazardous air quality: AQI {aqi} exceeds {self.air_quality_critical}", source_state=source_state, details={"aqi": aqi}))
        elif aqi >= self.air_quality_warning:
            alerts.append(Alert(category=AlertCategory.POOR_AIR_QUALITY, severity=Severity.WARNING, message=f"Poor air quality: AQI {aqi} exceeds {self.air_quality_warning}", source_state=source_state, details={"aqi": aqi}))
        return alerts