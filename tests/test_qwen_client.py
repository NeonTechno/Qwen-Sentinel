"""Unit tests for QwenClient."""
import os
import unittest
from unittest.mock import MagicMock, patch

from src.cloud.qwen_client import QwenClient


class TestQwenClient(unittest.TestCase):
    def test_init_with_api_key(self):
        """Test QwenClient initialization with API key."""
        client = QwenClient(api_key="test-key-123")
        self.assertEqual(client.api_key, "test-key-123")
        self.assertEqual(client.base_url, "https://api.qwen.ai/v1")

    def test_init_without_api_key_raises(self):
        """Test that QwenClient raises error without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError) as context:
                QwenClient()
            self.assertIn("Qwen API key is required", str(context.exception))

    def test_init_from_env_variable(self):
        """Test QwenClient gets API key from environment."""
        with patch.dict('os.environ', {'Qwen_Cloud_API': 'env-key-456'}, clear=True):
            client = QwenClient()
            self.assertEqual(client.api_key, "env-key-456")

    @patch('requests.post')
    def test_generate_summary(self, mock_post):
        """Test generate_summary method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Test summary response"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        client = QwenClient(api_key="test-key")
        sensor_data = {"temperature": 25, "humidity": 50}
        alerts = []
        
        result = client.generate_summary(sensor_data, alerts)
        self.assertIn("Test summary", result)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("Authorization", call_args[1]['headers'])

    @patch('requests.post')
    def test_suggest_actions(self, mock_post):
        """Test suggest_actions method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '[{"action": "test", "priority": "high", "description": "test desc"}]'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        client = QwenClient(api_key="test-key")
        alerts = [{"message": "test alert"}]
        
        result = client.suggest_actions(alerts)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch('requests.post')
    def test_suggest_actions_empty_list(self, mock_post):
        """Test suggest_actions with empty alerts."""
        client = QwenClient(api_key="test-key")
        result = client.suggest_actions([])
        self.assertEqual(result, [])

    @patch('requests.post')
    def test_check_connection_success(self, mock_post):
        """Test check_connection method with successful connection."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Qwen-Sentinel connection test successful"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        client = QwenClient(api_key="test-key")
        result = client.check_connection()
        self.assertTrue(result)

    @patch('requests.post')
    def test_check_connection_failure(self, mock_post):
        """Test check_connection method with failed connection."""
        mock_post.side_effect = Exception("Connection failed")
        
        client = QwenClient(api_key="test-key")
        result = client.check_connection()
        self.assertFalse(result)

    @patch('requests.post')
    def test_api_error_handling(self, mock_post):
        """Test that API errors are handled gracefully."""
        mock_post.side_effect = Exception("API Error")
        
        client = QwenClient(api_key="test-key")
        result = client._call_qwen("test prompt")
        self.assertIn("API Error", result)