#!/bin/bash
# Start OTP Testing Web Interface

echo "🚀 Starting OTP Testing Web Interface..."
echo "=========================================="

# Check if FreeRADIUS is running
if ! pgrep -x "freeradius" > /dev/null; then
    echo "⚠️  FreeRADIUS is not running. Starting it..."
    sudo freeradius &
    sleep 2
else
    echo "✅ FreeRADIUS is already running"
fi

# Navigate to web directory
cd web-otp-test

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo ""
echo "🌐 Starting web server..."
echo "========================="
echo ""
echo "📱 Access the OTP Test Interface at:"
echo "   - http://localhost:5000"
echo "   - http://0.0.0.0:5000"

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ ! -z "$LOCAL_IP" ]; then
    echo "   - http://$LOCAL_IP:5000"
fi

echo ""
echo "🔐 Demo Users:"
echo "   - vasco_demo (TOTP)"
echo "   - demo (HOTP)"
echo "   - testuser (HOTP)"
echo ""
echo "🌍 Server is listening on all interfaces (0.0.0.0)"
echo "   You can access it from any device on your network!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python server.py