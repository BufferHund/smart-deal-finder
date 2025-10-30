#!/bin/bash

# SmartDeal Web Application Launcher
# This script launches the Streamlit web application

echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║        SmartDeal - Brochure Analyzer                     ║"
echo "║        Starting Web Application...                       ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   Run: source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install streamlit
fi

echo "🚀 Launching application..."
echo "📍 The app will open at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Launch the enhanced app
cd "$(dirname "$0")"
streamlit run src/app/enhanced_app.py
