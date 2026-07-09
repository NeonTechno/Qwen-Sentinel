"""Integration tests for CLI."""
import io
import unittest
from unittest.mock import patch
from cli import build_arg_parser, run


class TestCLIIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = build_arg_parser()

    def test_cli_parser_defaults(self):
        args = self.parser.parse_args([])
        self.assertEqual(args.cycles, 10)
        self.assertEqual(args.interval, 0.0)
        self.assertIsNone(args.state)
        self.assertIsNone(args.memory_file)
        self.assertEqual(args.memory_window, 50)
        self.assertEqual(args.cooldown, 30.0)
        self.assertFalse(args.verbose)
        self.assertIsNone(args.webhook_url)
        self.assertIsNone(args.webhook_secret)

    def test_cli_parser_with_all_args(self):
        args = self.parser.parse_args(["--cycles", "20", "--interval", "1.5", "--state", "overheating", "--memory-file", "test.json", "--memory-window", "100", "--cooldown", "60.0", "--verbose", "--webhook-url", "https://hooks.example.com/test", "--webhook-secret", "my-secret"])
        self.assertEqual(args.cycles, 20)
        self.assertEqual(args.interval, 1.5)
        self.assertEqual(args.state, "overheating")
        self.assertEqual(args.memory_file, "test.json")
        self.assertEqual(args.memory_window, 100)
        self.assertEqual(args.cooldown, 60.0)
        self.assertTrue(args.verbose)
        self.assertEqual(args.webhook_url, "https://hooks.example.com/test")
        self.assertEqual(args.webhook_secret, "my-secret")

    def test_cli_runs_without_errors(self):
        args = self.parser.parse_args(["--cycles", "1", "--interval", "0"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            run(args)
        output = mock_stdout.getvalue()
        self.assertIn("Qwen-Sentinel CLI", output)
        self.assertIn("cycle 1/1", output)
        self.assertIn("Summary", output)

    def test_cli_verbose_mode_shows_sensor_data(self):
        args = self.parser.parse_args(["--cycles", "1", "--verbose"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            run(args)
        output = mock_stdout.getvalue()
        self.assertIn("Sensors:", output)
        self.assertIn("temperature", output)

    def test_cli_with_forced_state(self):
        args = self.parser.parse_args(["--cycles", "2", "--state", "overheating"])
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            run(args)
        output = mock_stdout.getvalue()
        self.assertIn("state=overheating", output)
        self.assertIn("overheating", output.lower())


class TestCLIWithWebhook(unittest.TestCase):
    def setUp(self):
        self.parser = build_arg_parser()

    @patch("src.cloud.alerts.create_webhook_dispatcher")
    def test_cli_with_webhook_url(self, mock_create_dispatcher):
        mock_dispatcher = lambda alert: None
        mock_create_dispatcher.return_value = mock_dispatcher
        args = self.parser.parse_args(["--cycles", "1", "--webhook-url", "https://hooks.example.com/test"])
        with patch("sys.stdout", new_callable=io.StringIO):
            run(args)
        mock_create_dispatcher.assert_called_once_with("https://hooks.example.com/test", None)

    @patch("src.cloud.alerts.create_webhook_dispatcher")
    def test_cli_with_webhook_url_and_secret(self, mock_create_dispatcher):
        mock_dispatcher = lambda alert: None
        mock_create_dispatcher.return_value = mock_dispatcher
        args = self.parser.parse_args(["--cycles", "1", "--webhook-url", "https://hooks.example.com/test", "--webhook-secret", "my-secret"])
        with patch("sys.stdout", new_callable=io.StringIO):
            run(args)
        mock_create_dispatcher.assert_called_once_with("https://hooks.example.com/test", "my-secret")


if __name__ == "__main__":
    unittest.main()