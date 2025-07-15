#!/usr/bin/env python3
"""
Setup PrivacyIDEA with DPX file for proper GO6 token handling
"""

import requests
import json
import os
import subprocess
import time

class PrivacyIDEASetup:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.admin_token = None
        
    def install_privacyidea(self):
        """Install PrivacyIDEA locally"""
        print("Installing PrivacyIDEA...")
        
        try:
            # Install required packages
            subprocess.run([
                "sudo", "apt-get", "update"
            ], check=True)
            
            subprocess.run([
                "sudo", "apt-get", "install", "-y",
                "python3-pip", "python3-venv", "python3-dev",
                "libssl-dev", "libffi-dev", "libxml2-dev", "libxslt1-dev",
                "libldap2-dev", "libsasl2-dev", "libjpeg-dev", "zlib1g-dev"
            ], check=True)
            
            # Create virtual environment
            if not os.path.exists("privacyidea-env"):
                subprocess.run([
                    "python3", "-m", "venv", "privacyidea-env"
                ], check=True)
            
            # Install PrivacyIDEA in virtual environment
            subprocess.run([
                "./privacyidea-env/bin/pip", "install", "--upgrade", "pip"
            ], check=True)
            
            subprocess.run([
                "./privacyidea-env/bin/pip", "install", 
                "privacyidea", "gunicorn", "passlib"
            ], check=True)
            
            print("PrivacyIDEA installation completed!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False
    
    def create_config(self):
        """Create PrivacyIDEA configuration"""
        config_content = """
# PrivacyIDEA Configuration
import os

# Secret key for session encryption
SECRET_KEY = 'your-super-secret-key-change-this-in-production'

# Database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///privacyidea.db'

# Logging
PI_LOGFILE = 'privacyidea.log'
PI_LOGLEVEL = 'INFO'

# Token settings
DEFAULT_TOKENTYPE = 'hotp'

# Authentication settings
PI_PEPPER = 'your-pepper-here'

# Web UI settings
PI_UI_DEACTIVATED = False

# RADIUS settings
PI_RADIUS_CLIENTS = [
    {
        'identifier': 'localhost',
        'secret': 'testing123'
    }
]
"""
        
        with open("pi.cfg", "w") as f:
            f.write(config_content)
        
        print("PrivacyIDEA configuration created!")
    
    def start_privacyidea(self):
        """Start PrivacyIDEA server"""
        print("Starting PrivacyIDEA server...")
        
        # Set configuration
        os.environ['PRIVACYIDEA_CONFIGFILE'] = os.path.abspath('pi.cfg')
        
        try:
            # Initialize database
            subprocess.run([
                "./privacyidea-env/bin/pi-manage", "createdb"
            ], check=True)
            
            # Create admin user
            subprocess.run([
                "./privacyidea-env/bin/pi-manage", "admin", "add", "admin"
            ], input="admin123\nadmin123\n", text=True, check=True)
            
            # Start server in background
            with open("privacyidea.log", "w") as log_file:
                process = subprocess.Popen([
                    "./privacyidea-env/bin/gunicorn", 
                    "--bind", "0.0.0.0:5001",
                    "--workers", "2",
                    "--timeout", "120",
                    "privacyidea.app:create_app()"
                ], stdout=log_file, stderr=subprocess.STDOUT)
            
            print("PrivacyIDEA server starting on port 5001...")
            time.sleep(5)
            
            return process
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to start PrivacyIDEA: {e}")
            return None
    
    def get_admin_token(self):
        """Get admin authentication token"""
        try:
            response = requests.post(
                f"{self.base_url}:5001/auth",
                data={
                    'username': 'admin',
                    'password': 'admin123'
                },
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                self.admin_token = result['result']['value']['token']
                print(f"Got admin token: {self.admin_token[:20]}...")
                return True
            else:
                print(f"Failed to get admin token: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Error getting admin token: {e}")
            return False
    
    def import_dpx_file(self, dpx_file_path="/tmp/Demo_GO6.dpx"):
        """Import DPX file into PrivacyIDEA"""
        if not self.admin_token:
            print("No admin token available")
            return False
        
        try:
            headers = {
                'Authorization': self.admin_token,
                'Content-Type': 'multipart/form-data'
            }
            
            with open(dpx_file_path, 'rb') as dpx_file:
                files = {
                    'file': ('Demo_GO6.dpx', dpx_file, 'application/octet-stream')
                }
                
                response = requests.post(
                    f"{self.base_url}:5001/token/load/Demo_GO6.dpx",
                    headers={'Authorization': self.admin_token},
                    files=files,
                    verify=False
                )
            
            if response.status_code == 200:
                result = response.json()
                print("DPX file imported successfully!")
                print(f"Result: {result}")
                return True
            else:
                print(f"Failed to import DPX: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error importing DPX: {e}")
            return False
    
    def create_test_user(self):
        """Create test user for GO6 token"""
        if not self.admin_token:
            return False
        
        try:
            # Create user
            response = requests.post(
                f"{self.base_url}:5001/user",
                headers={'Authorization': self.admin_token},
                data={
                    'username': 'go6_demo',
                    'realm': 'default'
                },
                verify=False
            )
            
            if response.status_code == 200:
                print("Test user 'go6_demo' created successfully!")
                return True
            else:
                print(f"Failed to create user: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

def main():
    setup = PrivacyIDEASetup()
    
    print("=== PrivacyIDEA + DPX Setup ===")
    
    # Install PrivacyIDEA
    if not setup.install_privacyidea():
        print("Failed to install PrivacyIDEA")
        return 1
    
    # Create configuration
    setup.create_config()
    
    # Start PrivacyIDEA
    process = setup.start_privacyidea()
    if not process:
        print("Failed to start PrivacyIDEA")
        return 1
    
    # Wait for startup
    print("Waiting for PrivacyIDEA to start...")
    time.sleep(10)
    
    # Get admin token
    if not setup.get_admin_token():
        print("Failed to get admin token")
        return 1
    
    # Import DPX file
    if setup.import_dpx_file():
        print("✅ DPX file imported successfully!")
    else:
        print("❌ Failed to import DPX file")
    
    # Create test user
    if setup.create_test_user():
        print("✅ Test user created successfully!")
    
    print("\n🎉 PrivacyIDEA setup complete!")
    print("📱 Access PrivacyIDEA at: http://localhost:5001")
    print("🔐 Admin credentials: admin / admin123")
    print("👤 Test user: go6_demo")
    
    return 0

if __name__ == "__main__":
    exit(main())