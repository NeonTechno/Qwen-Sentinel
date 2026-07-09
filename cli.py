#!/usr/bin/env python3
"""
Qwen-Sentinel CLI runner.

Ties simulator.generate_sensor_data(), EdgeDetector, MemoryAgent, and
AlertManager together into a single monitoring loop you can run from the
terminal.

Usage:
    python3 cli.py --cycles 10
    python3 cli.py --cycles 5 --state overheating
    python3 cli.py --cycles 20 --memory-file memory.json --cooldown 15
    python3 cli.py --cycles 10 --verbose
    python3 cli.py --cycles 10 --webhook-url https://hooks.slack.com/...
"""
import argparse
import json
import time

from simulator import EnvironmentState, generate_sensor_data
from src.cloud import AlertManager, MemoryAgent
from src.edge import EdgeDetector


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Qwen-Sentinel monitoring loop.")
    parser.add_argument("--cycles", type=int, default=10, help="Number of sensor readings to process.")
    parser.add_argument("--interval", type=float, default=0.0, help="Seconds to sleep between cycles.")
    parser.add_argument(
        "--state",
        choices=[s.value for s in EnvironmentState],
        default=None,
        help="Force a specific environment state instead of random sampling.",
    )
    parser.add_argument("--memory-file", type=str, default=None, help="Path to a JSON file for persistent memory.")
    parser.add_argument("--memory-window", type=int, default=50, help="Number of readings MemoryAgent retains.")
    parser.add_argument("--cooldown", type=float, default=30.0, help="Seconds before repeating the same alert category.")
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
    return parser


def run(args: argparse.Namespace) -> None:
    # Set up components
    detector = EdgeDetector()
    memory = MemoryAgent(storage_path=args.memory_file, window_size=args.memory_window)
    
    # Configure dispatcher based on webhook settings
    if args.webhook_url:
        from src.cloud.alerts import create_webhook_dispatcher
        dispatcher = create_webhook_dispatcher(args.webhook_url, args.webhook_secret)
        alert_manager = AlertManager(cooldown_seconds=args.cooldown, dispatcher=dispatcher)
    else:
        alert_manager = AlertManager(cooldown_seconds=args.cooldown)

    forced_state = EnvironmentState(args.state) if args.state else None

    print("Qwen-Sentinel CLI")
    print("=" * 40)
    if args.webhook_url:
        print(f"Webhook: {args.webhook_url}")
    print()

    for i in range(args.cycles):
        reading = generate_sensor_data(forced_state)
        alerts = detector.analyze(reading)
        memory.record(reading, alerts)
        dispatched = alert_manager.process(alerts)

        state = reading["environment_state"]
        status = f"{len(dispatched)} alert(s)" if dispatched else "nominal"
        print(f"[cycle {i + 1}/{args.cycles}] state={state} -> {status}")
        
        if args.verbose:
            # Show full sensor reading
            print(f"  Sensors: {json.dumps(reading['sensors'], indent=4)}")
        
        for alert in dispatched:
            print(f"    {alert_manager.format_alert(alert)}")

        if args.interval:
            time.sleep(args.interval)

    print("\nSummary")
    print("-" * 40)
    counts = memory.category_counts()
    if not counts:
        print("No anomalies recorded this run.")
    else:
        for category, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
            print(f"  {category}: {count}")


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()