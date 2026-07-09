"""Unit tests for Simulator."""
import json
import unittest
from simulator import EnvironmentState, generate_sensor_data


class TestSimulator(unittest.TestCase):
    def test_generate_sensor_data_returns_dict(self):
        data = generate_sensor_data(EnvironmentState.NORMAL)
        self.assertIsInstance(data, dict)

    def test_generate_sensor_data_has_required_keys(self):
        data = generate_sensor_data(EnvironmentState.NORMAL)
        self.assertIn("timestamp", data)
        self.assertIn("environment_state", data)
        self.assertIn("sensors", data)
        sensors = data["sensors"]
        self.assertIn("camera", sensors)
        self.assertIn("temperature", sensors)
        self.assertIn("motion", sensors)
        self.assertIn("humidity", sensors)
        self.assertIn("air_quality", sensors)

    def test_generate_sensor_data_is_valid_json(self):
        data = generate_sensor_data(EnvironmentState.OVERHEATING)
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        self.assertEqual(data, parsed)

    def test_all_environment_states_generate_data(self):
        for state in EnvironmentState:
            data = generate_sensor_data(state)
            self.assertIsInstance(data, dict)
            self.assertEqual(data["environment_state"], state.value)

    def test_overheating_state_has_high_temperature(self):
        data = generate_sensor_data(EnvironmentState.OVERHEATING)
        temp = data["sensors"]["temperature"]["value"]
        self.assertGreater(temp, 30.0)

    def test_low_light_state_has_low_brightness(self):
        data = generate_sensor_data(EnvironmentState.LOW_LIGHT)
        brightness = data["sensors"]["camera"]["brightness"]
        self.assertLess(brightness, 35)

    def test_high_humidity_state_has_high_humidity(self):
        data = generate_sensor_data(EnvironmentState.HIGH_HUMIDITY)
        humidity = data["sensors"]["humidity"]["value"]
        self.assertGreater(humidity, 70.0)

    def test_poor_air_quality_state_has_high_aqi(self):
        data = generate_sensor_data(EnvironmentState.POOR_AIR_QUALITY)
        aqi = data["sensors"]["air_quality"]["value"]
        self.assertGreater(aqi, 100)


if __name__ == "__main__":
    unittest.main()