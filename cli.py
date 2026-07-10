#!/usr/bin/env python3
"""
Qwen-Sentinel CLI runner with AI support.

Ties simulator.generate_sensor_data(), EdgeDetector/HybridDetector, MemoryAgent, and
AlertManager together into a single monitoring loop you can run from the terminal.

Usage:
    python3 cli.py --cycles 10
    python3 cli.py --cycles 5 --state overheating
    python3 cli.py --cycles 20 --memory-file memory.json --cooldown 15
    python3 cli.py --cycles 10 --verbose
    python3 cli.py --cycles 10 --webhook-url https://hooks.slack.com/...
    python3 cli.py --cycles 10 --use-ai --qwen-api-key $Qwen_Cloud_API
"""
import argparse
import json
import os
import time

from simulator import EnvironmentState, generate_sensor_data
from src.cloud import AlertManager, MemoryAgent
from src.cloud.qwen_client import QwenClient
from src.edge.detector import EdgeDetector
from src.edge.hybrid_detector import HybridDetector


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Qwen-Sentinel monitoring loop with optional AI features."
    )
    parser.add_argument("--cycles", type=int, default=10, 
                       help="Number of sensor readings to process.")
    parser.add_argument("--interval", type=float, default=0.0, 
                       help="Seconds to sleep between cycles.")
    parser.add_argument(
        "--state",
        choices=[s.value for s in EnvironmentState],
        default=None,
        help="Force a specific environment state instead of random sampling.",
    )
    parser.add_argument("--memory-file", type=str, default=None, 
                       help="Path to a JSON file for persistent memory.")
    parser.add_argument("--memory-window", type=int, default=50, 
                       help="Number of readings MemoryAgent retains.")
    parser.add_argument("--cooldown", type=float, default=30.0, 
                       help="Seconds before repeating the same alert category.")
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Show detailed output including all sensor readings.",
    )
    parser.add_argument(
        "--webhook-url",
        type=str,
        default=None,
        help="URL to send alerts to via webhook POST requests.",
    )
    parser.add_argument(
        "--webhook-secret",
        type=str,
        default=None,
        help="Secret token for webhook authentication (X-Webhook-Secret header).",
    )
    
    parser.add_argument(
        "--use-ai",
        action="store_true",
        default=False,
        help="Enable AI-powered anomaly detection (requires --qwen-api-key).",
    )
    parser.add_argument(
        "--qwen-api-key",
        type=str,
        default=None,
        help="Qwen Cloud API key for AI features. Can also be set via Qwen_Cloud_API environment variable.",
    )
    parser.add_argument(
        "--ai-threshold",
        type=float,
        default=0.8,
        help="Minimum confidence score (0.0-1.0) for AI detections. Default: 0.8",
    )
    
    return parser


def run(args: argparse.Namespace) -> None:
    qwen_api_key = args.qwen_api_key or os.getenv("Qwen_Cloud_API")
    
    qwen_client = None
    if qwen_api_key:
        try:
            qwen_client = QwenClient(api_key=qwen_api_key)
            if qwen_client.check_connection():
                print(f"Connected to Qwen API")
            else:
                print(f"Qwen API: Connection failed (key may be invalid)")
                qwen_client = None
        except Exception as e:
            print(f"Qwen API: {str(e)}")
            qwen_client = None
    else:
        print(f"Qwen API: Not connected (use --qwen-api-key or set Qwen_Cloud_API env var)")
    
    if args.use_ai and qwen_client:
        detector = HybridDetector(
            qwen_client=qwen_client,
            use_ai=True,
            ai_threshold=args.ai_threshold
        )
        print(f"AI Detection: Enabled (threshold: {args.ai_threshold})")
    else:
        detector = EdgeDetector()
        if args.use_ai:
            print(f"AI Detection: Disabled (Qwen API not connected)")
    
    memory = MemoryAgent(storage_path=args.memory_file, window_size=args.memory_window)
    
    if args.webhook_url:
        from src.cloud.alerts import create_webhook_dispatcher
        dispatcher = create_webhook_dispatcher(args.webhook_url, args.webhook_secret)
        alert_manager = AlertManager(
            cooldown_seconds=args.cooldown,
            dispatcher=dispatcher,
            qwen_client=qwen_client
        )
    else:
        alert_manager = AlertManager(
            cooldown_seconds=args.cooldown,
            qwen_client=qwen_client
        )

    forced_state = EnvironmentState(args.state) if args.state else None

    print("\n" + "=" * 60)
    print("Qwen-Sentinel CLI" + (" with AI" if args.use_ai and qwen_client else ""))
    print("=" * 60)
    if args.webhook_url:
        print(f"Webhook: {args.webhook_url}")
    print()

    for i in range(args.cycles):
        reading = generate_sensor_data(forced_state)
        alerts = detector.analyze(reading)
        memory.record(reading, alerts)
        
        dispatched = alert_manager.process(alerts, reading)

        state = reading["environment_state"]
        status = f"{len(dispatched)} alert(s)" if dispatched else "nominal"
        print(f"[cycle {i + 1}/{args.cycles}] state={state} -> {status}")
        
        if args.verbose:
            print(f"  Sensors: {json.dumps(reading['sensors'], indent=4)}")
        
        if args.use_ai and hasattr(detector, 'is_ai_enabled') and detector.is_ai_enabled:
            summary = detector.get_detection_summary(reading)
            if summary.get('ai_alerts', 0) > 0:
                print(f"  AI detected {summary['ai_alerts']} additional anomaly(ies)")
        
        for alert in dispatched:
            print(f"    {alert_manager.format_alert(alert)}")

        if args.interval:
            time.sleep(args.interval)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    counts = memory.category_counts()
    if not counts:
        print("No anomalies recorded this run.")
    else:
        for category, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
            print(f"  {category}: {count}")
    
    if qwen_client and args.cycles > 0:
        print("\nAI Analysis: Enabled throughout the session")


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()