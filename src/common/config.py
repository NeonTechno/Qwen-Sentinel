"""Central threshold configuration for Qwen-Sentinel edge detection."""

# Temperature thresholds (Celsius)
TEMPERATURE_WARNING_C = 30.0
TEMPERATURE_CRITICAL_C = 38.0

# Motion thresholds (normalized 0.0-1.0, from the top-level `motion` sensor)
MOTION_INTRUDER_THRESHOLD = 0.7

# Camera-reported motion_level threshold used as a proxy for ambient noise/activity
MOTION_NOISE_THRESHOLD = 0.5

# Brightness threshold (lux) below which conditions are considered low light
BRIGHTNESS_LOW_LUX = 35

# MemoryAgent defaults
DEFAULT_MEMORY_WINDOW = 50

# AlertManager defaults
DEFAULT_ALERT_COOLDOWN_SECONDS = 30.0
