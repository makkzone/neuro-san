#!/bin/bash

# Neuro-SAN Server Startup Script for macOS/Linux
# This script handles all necessary steps to launch the neuro-san server

set -e

echo "==============================================="
echo "  Neuro-SAN Server Startup"
echo "==============================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Project directory: $PROJECT_DIR"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    VENV_DIR=".venv"
else
    VENV_DIR="venv"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "✅ Virtual environment activated"
echo ""

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_DIR"
echo "PYTHONPATH set to: $PYTHONPATH"
echo ""

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python -c "import neuro_san" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi
echo ""

# Check for API keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY environment variable is not set!"
    echo "   Some features may not work without API keys."
    echo "   Set it with: export OPENAI_API_KEY='your-key-here'"
    echo ""
fi

# Enable CORS headers for web applications
export AGENT_ALLOW_CORS_HEADERS=1
echo "✅ CORS headers enabled"
echo ""

# Start the server
echo "==============================================="
echo "  Starting Neuro-SAN Server on port 8080"
echo "==============================================="
echo ""
echo "Server will be available at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

python -m neuro_san.service.main_loop.server_main_loop
