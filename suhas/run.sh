#!/bin/bash

# Raspberry Pi AI Assistant Launcher Script

echo "🤖 Starting Raspberry Pi AI Assistant..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.py first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found. Please check your installation."
    exit 1
fi

# Run the assistant
python main.py

echo "👋 AI Assistant stopped."
