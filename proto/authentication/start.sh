#!/bin/bash
# Quick start script for Garmin Auth Tester

echo "🚀 Starting Garmin Authentication Tester..."
echo ""
echo "📋 Available options:"
echo "  1. Web UI (browser)"
echo "  2. Command Line"
echo ""
read -p "Choose option (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "🌐 Starting web server..."
        echo "📱 Open http://localhost:8000 in your browser"
        echo "⏹️  Press CTRL+C to stop"
        echo ""
        uv run server.py
        ;;
    2)
        echo ""
        if [ -f "creds.json" ]; then
            echo "📄 Found creds.json, using it..."
            uv run cli_test.py --credentials creds.json
        else
            echo "❌ No creds.json found"
            echo "💡 Create one from creds.example.json or use:"
            echo "   uv run cli_test.py --email your@email.com --password yourpass"
        fi
        ;;
    *)
        echo "❌ Invalid option. Please choose 1 or 2."
        exit 1
        ;;
esac
