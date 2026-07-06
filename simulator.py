#!/usr/bin/env python3
"""
Simulator for generating varied environment states for Qwen-Sentinel.
Produces JSON payloads from mock sensors: camera, temperature, motion.
"""

import json
import random
import time
from datetime import datetime
from enum import Enum
from typing import Dict, Any


class EnvironmentState(Enum):
    NORMAL = "normal"
    OVERHEATING = "overheating"
    INTRUDER_DETECTED = "intruder_detected"
    HIGH_NOISE = "high_noise"
    LOW_LIGHT = "low_light"


def generate_sensor_data(state: EnvironmentState = None) -> Dict[str, Any]:
    """
    Generate mock sensor data based on the given environment state.
    If no state is provided, randomly select one.
    """
    if state is None:
        state = random.choice(list(EnvironmentState))

    # Base sensor readings
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Simulate camera data (mock: object detection, facial expression, etc.)
    camera_data = {
        "objects_detected": [],
        "facial_expression": "neutral",
        "motion_level": 0.0,
        "brightness": 100  # lux
    }

    # Simulate temperature sensor (in Celsius)
    temperature = 22.0  # default

    # Simulate motion sensor (0.0 to 1.0)
    motion = 0.1  # default

    # Adjust based on environment state
    if state == EnvironmentState.OVERHEATING:
        temperature = random.uniform(35.0, 45.0)
        camera_data["objects_detected"].append({"type": "heat_source", "confidence": 0.9})
        camera_data["facial_expression"] = "distressed"

    elif state == EnvironmentState.INTRUDER_DETECTED:
        motion = random.uniform(0.7, 1.0)
        camera_data["objects_detected"].append({"type": "person", "confidence": 0.85})
        camera_data["facial_expression"] = "alert"
        camera_data["motion_level"] = motion

    elif state == EnvironmentState.HIGH_NOISE:
        # For simplicity, we'll affect camera motion and maybe add a "noise_source" object
        camera_data["motion_level"] = random.uniform(0.5, 0.8)
        camera_data["objects_detected"].append({"type": "noise_source", "confidence": 0.7})

    elif state == EnvironmentState.LOW_LIGHT:
        camera_data["brightness"] = random.uniform(10, 30)  # low lux
        camera_data["facial_expression"] = "sleepy"

    else:  # NORMAL
        temperature = random.uniform(20.0, 25.0)
        motion = random.uniform(0.0, 0.2)
        camera_data["motion_level"] = motion

    # Construct the sensor payload
    sensor_payload = {
        "timestamp": timestamp,
        "environment_state": state.value,
        "sensors": {
            "camera": camera_data,
            "temperature": {
                "value": temperature,
                "unit": "C",
                "status": "ok" if temperature < 30 else "warning"
            },
            "motion": {
                "value": motion,
                "unit": "normalized",
                "status": "ok"
            }
        }
    }

    return sensor_payload


def simulate_environment_sequence(duration_seconds: int = 30, interval_seconds: int = 5):
    """
    Simulate a sequence of environment states over time.
    Yields sensor data at each interval.
    """
    start_time = time.time()
    states = list(EnvironmentState)

    while time.time() - start_time < duration_seconds:
        # Cycle through states or pick randomly
        state_index = int((time.time() - start_time) // interval_seconds) % len(states)
        state = states[state_index]

        data = generate_sensor_data(state)
        yield data

        time.sleep(interval_seconds)


if __name__ == "__main__":
    # Demo: generate and print a few sensor readings
    print("Qwen-Sentinel Sensor Simulator")
    print("=" * 40)

    for i in range(5):
        # Generate random state for demo
        state = random.choice(list(EnvironmentState))
        data = generate_sensor_data(state)
        print(f"\n--- Reading {i+1} ({state.value.upper()}) ---")
        print(json.dumps(data, indent=2))
        time.sleep(0.5)  # small delay for demo