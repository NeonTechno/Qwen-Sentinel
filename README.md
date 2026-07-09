# Qwen-Sentinel

An intelligent environment monitoring agent built for the Qwen Cloud Hackathon. Qwen-Sentinel simulates and analyzes environmental sensor data (camera, temperature, motion) to detect anomalies such as overheating, intruders, high noise, and low-light conditions — then persists trends and dispatches deduplicated alerts.

## Architecture

```
simulator.py          Generates mock sensor payloads (camera, temperature, motion)
cli.py                 CLI runner that wires everything together
src/edge/detector.py    EdgeDetector — rule-based anomaly detection, runs on a single reading
src/cloud/memory.py     MemoryAgent — persistent, file-backed history + trend queries
src/cloud/alerts.py     AlertManager — dedupes/cooldowns and dispatches alerts
src/common/models.py    Shared Alert, AlertCategory, Severity types
src/common/config.py    Central threshold configuration
tests/                  12-test unittest suite covering all three components
```

## Features
- Simulates multiple environmental states: normal, overheating, intruder detection, high noise, low light
- Rule-based **EdgeDetector** that turns a single sensor reading into zero or more `Alert` objects (temperature, motion/person, noise, brightness thresholds)
- Persistent **MemoryAgent** that keeps a rolling window of readings/alerts, optionally backed by a JSON file, with category-count trend queries
- **AlertManager** that deduplicates alerts per category with a configurable cooldown so a sustained anomaly doesn't spam the same channel every cycle, and dispatches via a pluggable callback (defaults to console output)
- End-to-end **CLI runner** (`cli.py`) tying simulator → detector → memory → alerts into a monitoring loop
- Modular design with separate edge, cloud, and common components
- 12-test `unittest` suite across all three components

## Usage

Run the sensor simulator standalone:
```bash
python3 simulator.py
```

Run the full monitoring loop:
```bash
python3 cli.py --cycles 10
python3 cli.py --cycles 5 --state overheating
python3 cli.py --cycles 20 --memory-file memory.json --cooldown 15
```

Run the test suite:
```bash
python3 -m unittest discover -s tests -v
```

## Extending the Project
1. Add new sensor types in `simulator.generate_sensor_data()` (e.g., humidity, air quality)
2. Add new detection rules to `EdgeDetector` in `src/edge/detector.py`
3. Extend `MemoryAgent` trend queries or swap the JSON backing store for a real database
4. Add real dispatch mechanisms to `AlertManager` (email, SMS, webhook) by passing a custom `dispatcher` callable

## Requirements
- Python 3.8+ (standard library only, no external dependencies)

## Hackathon Tracks
This project aligns with the following Qwen Cloud Hackathon tracks:
- **MemoryAgent**: Persistent memory of environmental states for trend analysis
- **AI Showrunner**: Could generate video summaries of environmental incidents
- **Agent Society**: Multiple sentinel agents collaborating across locations
- **Visual Understanding**: Camera feed analysis for object detection and facial expressions
- **Productivity**: Automating environment monitoring reduces manual checks

## License
MIT
