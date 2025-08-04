#!/bin/bash

# Installation script for Project Management Dashboard API
# This script sets up the Python environment and installs dependencies

echo "🚀 Setting up Project Management Dashboard API..."

# Check if Python 3.11+ is available
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
if [ "$1" = "--dev" ]; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt
else
    echo "Installing production dependencies..."
    pip install -r requirements.txt
fi

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please update .env file with your configuration"
fi

echo "✅ Installation complete!"
echo ""
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
echo "To format code:"
echo "  black ."
echo "  isort ." 