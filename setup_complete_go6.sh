#!/bin/bash
# Complete GO6 + PrivacyIDEA + FreeRADIUS Setup

echo "🚀 Setting up complete GO6 authentication system..."
echo "=================================================="

# Kill any existing services
echo "🛑 Stopping existing services..."
sudo pkill -f freeradius || true
pkill -f privacyidea || true
pkill -f "python server.py" || true

# Set up PrivacyIDEA with DPX
echo "🔧 Setting up PrivacyIDEA with DPX support..."
python3 setup_privacyidea_dpx.py &
PRIVACYIDEA_PID=$!

# Wait for PrivacyIDEA to start
echo "⏳ Waiting for PrivacyIDEA to initialize..."
sleep 15

# Copy the PrivacyIDEA module to FreeRADIUS
echo "📁 Installing PrivacyIDEA RADIUS module..."
sudo cp privacyidea_radius_module.py /etc/freeradius/3.0/mods-config/python3/

# Update FreeRADIUS module to use PrivacyIDEA
sudo tee /etc/freeradius/3.0/mods-available/python3-privacyidea > /dev/null << 'EOF'
python3 {
	python_path = "${modconfdir}/${.:name}:/etc/freeradius/3.0/mods-config/python3"
	module = privacyidea_radius_module

	mod_instantiate = ${.module}
	func_instantiate = instantiate

	mod_detach = ${.module}  
	func_detach = detach

	mod_authorize = ${.module}
	func_authorize = authorize

	mod_authenticate = ${.module}
	func_authenticate = authenticate

	mod_preacct = ${.module}
	func_preacct = preacct

	mod_accounting = ${.module}
	func_accounting = accounting

	mod_post_auth = ${.module}
	func_post_auth = post_auth
}
EOF

# Enable the PrivacyIDEA module
echo "🔗 Enabling PrivacyIDEA module in FreeRADIUS..."
sudo rm -f /etc/freeradius/3.0/mods-enabled/python3-vasco
sudo ln -sf /etc/freeradius/3.0/mods-available/python3-privacyidea /etc/freeradius/3.0/mods-enabled/python3-privacyidea

# Update site configuration
sudo tee /etc/freeradius/3.0/sites-available/privacyidea-auth > /dev/null << 'EOF'
server default {

listen {
    type = auth
    ipaddr = *
    port = 1812
}

listen {
    type = acct
    ipaddr = *
    port = 1813
}

authorize {
    python3
    if (ok) {
        update control {
            Auth-Type := Python3
        }
    }
}

authenticate {
    Auth-Type Python3 {
        python3
    }
}

post-auth {
    python3
}

accounting {
    python3
}

}
EOF

# Enable the new site
echo "🌐 Configuring FreeRADIUS site..."
sudo rm -f /etc/freeradius/3.0/sites-enabled/vasco-auth
sudo ln -sf /etc/freeradius/3.0/sites-available/privacyidea-auth /etc/freeradius/3.0/sites-enabled/privacyidea-auth

# Install requests for Python module
echo "📦 Installing required Python packages..."
pip3 install requests --break-system-packages || true

# Test FreeRADIUS configuration
echo "🧪 Testing FreeRADIUS configuration..."
if sudo freeradius -C; then
    echo "✅ FreeRADIUS configuration is valid"
else
    echo "❌ FreeRADIUS configuration error"
    exit 1
fi

# Start FreeRADIUS
echo "🚀 Starting FreeRADIUS with PrivacyIDEA integration..."
sudo freeradius -X &
FREERADIUS_PID=$!

# Wait for FreeRADIUS to start
sleep 5

echo ""
echo "🎉 GO6 Authentication System Setup Complete!"
echo "============================================="
echo ""
echo "📱 Services running:"
echo "   - PrivacyIDEA: http://localhost:5001"
echo "   - FreeRADIUS:  localhost:1812 (RADIUS)"
echo ""
echo "🔐 Login credentials:"
echo "   - PrivacyIDEA Admin: admin / admin123"
echo ""
echo "📁 DPX file should be imported into PrivacyIDEA:"
echo "   - File: /tmp/Demo_GO6.dpx"
echo "   - Contains GO6 token configuration"
echo ""
echo "🧪 Test GO6 authentication:"
echo "   1. Import DPX file in PrivacyIDEA web interface"
echo "   2. Create user 'go6_demo' and assign GO6 token"
echo "   3. Test with: radtest go6_demo [TOKEN] localhost 0 testing123"
echo ""
echo "🌐 Or use web interface on port 5000 when ready"
echo ""

# Keep services running
echo "Press Ctrl+C to stop all services"
wait