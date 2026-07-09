"""Central threshold configuration for Qwen-Sentinel edge detection."""

# Temperature thresholds (Celsius)
TEMPERATURE_WARNING_C = 30.0
TEMPERATURE_CRITICAL_C = 38.0

# Motion thresholds (normalized 0.0-1.0)
MOTION_INTRUDER_THRESHOLD = 0.7

# Camera-reported motion_level threshold
MOTION_NOISE_THRESHOLD = 0.5

# Brightness threshold (lux)
BRIGHTNESS_LOW_LUX = 35

# Humidity thresholds (percentage)
HUMIDITY_WARNING_PERCENT = 70.0
HUMIDITY_CRITICAL_PERCENT = 85.0

# Air quality thresholds (AQI)
AIR_QUALITY_WARNING_AQI = 100
AIR_QUALITY_CRITICAL_AQI = 150

# MemoryAgent defaults
DEFAULT_MEMORY_WINDOW = 50

# AlertManager defaults
DEFAULT_ALERT_COOLDOWN_SECONDS = 30.0