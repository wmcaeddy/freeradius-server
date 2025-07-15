#!/usr/bin/env python3
"""
Web server for RADIUS OTP authentication testing
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import json
import os
import sys
import logging

# Add test-scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'test-scripts'))

# Import VascoTokenAuth without requests dependency
try:
    from vasco_token_auth import VascoTokenAuth
except ImportError:
    # Create a simplified version without requests
    class VascoTokenAuth:
        def __init__(self):
            self.demo_tokens = {
                "demo": {
                    "secret": "12345678901234567890",
                    "counter": 0,
                    "type": "hotp"
                },
                "vasco_demo": {
                    "secret": "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",
                    "counter": 0,
                    "type": "totp"
                },
                "testuser": {
                    "secret": "HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ",
                    "counter": 0,
                    "type": "hotp"
                }
            }
        
        def hotp(self, secret, counter, digits=6):
            import hashlib
            import hmac
            import struct
            
            if len(secret) % 2 == 0:
                try:
                    key = bytes.fromhex(secret)
                except:
                    key = secret.encode('utf-8')
            else:
                key = secret.encode('utf-8')
            
            counter_bytes = struct.pack(">Q", counter)
            hmac_digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()
            
            offset = hmac_digest[19] & 0xf
            code = struct.unpack(">I", hmac_digest[offset:offset+4])[0]
            code &= 0x7fffffff
            code %= 10 ** digits
            
            return f"{code:0{digits}d}"
        
        def totp(self, secret, time_step=30, digits=6):
            import time
            counter = int(time.time()) // time_step
            return self.hotp(secret, counter, digits)
        
        def get_current_tokens(self):
            tokens = {}
            for username, data in self.demo_tokens.items():
                if data["type"] == "hotp":
                    tokens[username] = self.hotp(data["secret"], data["counter"])
                elif data["type"] == "totp":
                    tokens[username] = self.totp(data["secret"])
            return tokens
        
        def validate_token(self, username, token):
            if username not in self.demo_tokens:
                return False
            
            user_data = self.demo_tokens[username]
            secret = user_data["secret"]
            
            if user_data["type"] == "hotp":
                for i in range(user_data["counter"], user_data["counter"] + 10):
                    expected = self.hotp(secret, i)
                    if expected == token:
                        self.demo_tokens[username]["counter"] = i + 1
                        return True
                return False
            
            elif user_data["type"] == "totp":
                import time
                current_time = int(time.time())
                for offset in [-30, 0, 30]:
                    test_time = current_time + offset
                    counter = test_time // 30
                    expected = self.hotp(secret, counter)
                    if expected == token:
                        return True
                return False
            
            return False

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize token authenticator
auth = VascoTokenAuth()

# RADIUS configuration
RADIUS_SERVER = os.environ.get('RADIUS_SERVER', 'localhost')
RADIUS_PORT = os.environ.get('RADIUS_PORT', '1812')
RADIUS_SECRET = os.environ.get('RADIUS_SECRET', 'testing123')

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file('index.html')

@app.route('/api/tokens', methods=['GET'])
def get_tokens():
    """Get current demo tokens"""
    try:
        tokens = auth.get_current_tokens()
        users = auth.demo_tokens
        
        return jsonify({
            'success': True,
            'tokens': tokens,
            'users': {
                username: {
                    'type': data['type'],
                    'counter': data.get('counter', 0)
                }
                for username, data in users.items()
            }
        })
    except Exception as e:
        logger.error(f"Error getting tokens: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    """Authenticate user with RADIUS"""
    try:
        data = request.get_json()
        username = data.get('username')
        otp = data.get('otp')
        
        if not username or not otp:
            return jsonify({
                'success': False,
                'message': 'Username and OTP are required'
            }), 400
        
        # Validate OTP format
        if not otp.isdigit() or len(otp) != 6:
            return jsonify({
                'success': False,
                'message': 'OTP must be 6 digits'
            }), 400
        
        logger.info(f"Authenticating user: {username}")
        
        # Run radtest command
        cmd = ['radtest', username, otp, RADIUS_SERVER, RADIUS_PORT, RADIUS_SECRET]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check if authentication was successful
            success = 'Access-Accept' in result.stdout
            
            if success:
                logger.info(f"Authentication successful for {username}")
                return jsonify({
                    'success': True,
                    'message': 'Authentication successful',
                    'details': {
                        'username': username,
                        'server': RADIUS_SERVER,
                        'port': RADIUS_PORT
                    }
                })
            else:
                logger.warning(f"Authentication failed for {username}")
                # Extract error message
                error_msg = 'Invalid OTP or username'
                if 'Access-Reject' in result.stdout:
                    error_msg = 'Access denied - Invalid credentials'
                elif result.stderr:
                    error_msg = f"RADIUS error: {result.stderr.strip()}"
                
                return jsonify({
                    'success': False,
                    'message': error_msg
                })
                
        except subprocess.TimeoutExpired:
            logger.error("RADIUS timeout")
            return jsonify({
                'success': False,
                'message': 'RADIUS server timeout'
            }), 504
            
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/validate', methods=['POST'])
def validate_token():
    """Validate token locally (without RADIUS)"""
    try:
        data = request.get_json()
        username = data.get('username')
        otp = data.get('otp')
        
        if not username or not otp:
            return jsonify({
                'success': False,
                'message': 'Username and OTP are required'
            }), 400
        
        # Local validation
        valid = auth.validate_token(username, otp)
        
        return jsonify({
            'success': valid,
            'message': 'Token valid' if valid else 'Invalid token',
            'local_validation': True
        })
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Check if RADIUS is accessible
    try:
        cmd = ['radtest', 'test', 'test', RADIUS_SERVER, RADIUS_PORT, RADIUS_SECRET]
        subprocess.run(cmd, capture_output=True, timeout=2)
        radius_status = 'connected'
    except:
        radius_status = 'unreachable'
    
    return jsonify({
        'status': 'healthy',
        'radius': {
            'server': RADIUS_SERVER,
            'port': RADIUS_PORT,
            'status': radius_status
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"Starting OTP test server on {host}:{port}")
    logger.info(f"RADIUS server: {RADIUS_SERVER}:{RADIUS_PORT}")
    logger.info(f"Web interface accessible at:")
    logger.info(f"  - http://localhost:{port}")
    logger.info(f"  - http://0.0.0.0:{port}")
    
    # Get local IP address
    import socket
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        logger.info(f"  - http://{local_ip}:{port}")
    except:
        pass
    
    app.run(
        host=host,
        port=port,
        debug=True
    )