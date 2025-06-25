#!/usr/bin/env python3
"""
Strava Data Agent - Main Runner
Runs data collection and web app in the background
"""

import os
import sys
import time
import argparse
import subprocess
import threading
import signal
import logging
from pathlib import Path

# pylint: disable=W1203
# pylint: disable=W0718

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strava_agent.log'),
        logging.StreamHandler()
    ]
)

class StravaAgent:
    def __init__(self, port=5000, data_interval_hours=24):
        self.port = port
        self.data_interval_hours = data_interval_hours
        self.processes = []
        self.running = False

    def start_data_collector(self):
        """Start the data collection process"""
        try:
            cmd = [sys.executable, "data_collector.py", "--interval", str(self.data_interval_hours)]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(("data_collector", process))
            logging.info(f"Data collector started with PID: {process.pid} (interval: {self.data_interval_hours}h)")
            return process
        except Exception as e:
            logging.error(f"Failed to start data collector: {e}")
            return None

    def start_web_app(self):
        """Start the Flask web app"""
        try:
            cmd = [sys.executable, "app.py"]
            env = os.environ.copy()
            env['FLASK_ENV'] = 'production'
            env['FLASK_HOST'] = '127.0.0.1'
            env['FLASK_PORT'] = str(self.port)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            self.processes.append(("web_app", process))
            logging.info(f"Web app started with PID: {process.pid}")
            return process
        except Exception as e:
            logging.error(f"Failed to start web app: {e}")
            return None

    def stop_all(self):
        """Stop all running processes"""
        self.running = False
        for name, process in self.processes:
            try:
                logging.info(f"Stopping {name} (PID: {process.pid})")
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logging.warning(f"Force killing {name} (PID: {process.pid})")
                process.kill()
            except Exception as e:
                logging.error(f"Error stopping {name}: {e}")
        self.processes.clear()

    def monitor_processes(self):
        """Monitor running processes and restart if needed"""
        while self.running:
            for name, process in self.processes[:]:
                if process.poll() is not None:
                    logging.warning(f"{name} process died, restarting...")
                    self.processes.remove((name, process))

                    new_process = None
                    if name == "data_collector":
                        new_process = self.start_data_collector()
                    elif name == "web_app":
                        new_process = self.start_web_app()

                    if new_process is None:
                        logging.error(f"Failed to restart {name}")

            time.sleep(30)  # Check every 30 seconds

    def run(self):
        """Main run method"""
        logging.info("Starting Strava Agent...")

        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)

        # Start data collector
        if not self.start_data_collector():
            logging.error("Failed to start data collector")
            return

        # Wait a bit for initial data collection
        time.sleep(5)

        # Start web app
        if not self.start_web_app():
            logging.error("Failed to start web app")
            self.stop_all()
            return

        self.running = True

        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()

        logging.info("Strava Agent is running!")
        logging.info(f"Web app available at: http://127.0.0.1:{self.port}")
        logging.info(f"Data collection interval: {self.data_interval_hours} hours")
        logging.info("Press Ctrl+C to stop")

        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Received interrupt signal, shutting down...")
        finally:
            self.stop_all()
            logging.info("Strava Agent stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logging.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Strava Data Agent")
    parser.add_argument("--port", type=int, default=5000, help="Web app port (default: 5000)")
    parser.add_argument("--interval", type=int, default=24, help="Data collection interval in hours (default: 24)")

    args = parser.parse_args()

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run agent
    agent = StravaAgent(port=args.port, data_interval_hours=args.interval)
    agent.run()
