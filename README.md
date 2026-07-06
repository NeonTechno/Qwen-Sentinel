# Qwen-Sentinel

An intelligent environment monitoring agent built for the Qwen Cloud Hackathon. Qwen-Sentinel simulates and analyzes environmental sensor data (camera, temperature, motion) to detect anomalies such as overheating, intruders, high noise, and low-light conditions.

## Features
- Simulates multiple environmental states: normal, overheating, intruder detection, high noise, low light
- Generates realistic sensor payloads (camera, temperature, motion) in JSON format
- Modular design with separate edge, cloud, and common components
- Easy to extend with additional sensors and states

## Files
- `simulator.py` – Main simulation script that generates sensor data
- `src/` – Package directory with placeholder modules for edge, cloud, and common logic
  - `src/edge/__init__.py`
  - `src/cloud/__init__.py`
  - `src/common/__init__.py`

## Usage
Run the simulator to see sample sensor outputs:
```bash
python3 simulator.py
```
The script will generate 5 sample readings with different environmental states and print them as formatted JSON.

## Extending the Project
1. Add new sensor types in `generate_sensor_data()` (e.g., humidity, air quality)
2. Implement edge computing logic in `src/edge/`
3. Implement cloud analytics/alerting in `src/cloud/`
4. Add persistence or alerting mechanisms (e.g., email, SMS, webhook)

## Requirements
- Python 3.6+

## Hackathon Tracks
This project aligns with the following Qwen Cloud Hackathon tracks:
- **MemoryAgent**: Persistent memory of environmental states for trend analysis
- **AI Showrunner**: Could generate video summaries of environmental incidents
- **Agent Society**: Multiple sentinel agents collaborating across locations
- **Visual Understanding**: Camera feed analysis for object detection and facial expressions
- **Productivity**: Automating environment monitoring reduces manual checks

## License
MIT