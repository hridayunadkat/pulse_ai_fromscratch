#!/bin/bash

echo "🔍 Checking server status..."
echo ""

# Check port 5001 (Flask server)
echo "📡 MediaPipe Server (port 5001):"
if lsof -i :5001 > /dev/null 2>&1; then
    echo "   ✅ Running"
    echo "   Access at: http://localhost:5001"
else
    echo "   ❌ Not running"
fi

echo ""

# Get IP address
IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
if [ -n "$IP" ]; then
    echo "📱 Access from phone:"
    echo "   http://$IP:5001"
fi

echo ""
echo "💡 To view logs, check the terminal where you ran 'npm run dev'"

