#!/bin/bash

# RPi5 Multi-Modal AI Assistant Launcher
# This script activates the virtual environment and starts the assistant

echo "Starting RPi5 Multi-Modal AI Assistant..."

# Check if virtual environment exists
if [ ! -d "ai_assistant_env" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run setup.sh first to install the assistant."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source ai_assistant_env/bin/activate

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found!"
    echo "Please ensure you're in the correct directory."
    exit 1
fi

# Start the assistant
echo "Starting AI Assistant..."
echo "Press Ctrl+C to stop the assistant"
echo ""

python main.py 