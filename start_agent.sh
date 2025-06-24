#!/bin/bash

# Strava Data Agent Startup Script

echo "Starting Strava Data Agent..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH"
    exit 1
fi

# Check if required files exist
if [ ! -f "run_agent.py" ]; then
    echo "Error: run_agent.py not found"
    exit 1
fi

if [ ! -f "data_collector.py" ]; then
    echo "Error: data_collector.py not found"
    exit 1
fi

if [ ! -f "app.py" ]; then
    echo "Error: app.py not found"
    exit 1
fi

# Check if strava_token.json exists
if [ ! -f "strava_token.json" ]; then
    echo "Warning: strava_token.json not found. You may need to authenticate first."
    echo "Run the notebook to set up authentication."
fi

# Create data directory if it doesn't exist
mkdir -p data

# Start the agent
echo "Starting agent with default settings..."
echo "Web app will be available at: http://localhost:5000"
echo "Data will be collected every 24 hours"
echo "Press Ctrl+C to stop"
echo ""

python3 run_agent.py