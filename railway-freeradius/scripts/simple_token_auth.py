#!/usr/bin/env python3
"""
Simple Token Authentication Module for FreeRADIUS
A lightweight alternative to PrivacyIDEA for basic token validation
"""

import radiusd
import json
import os
import time
import hashlib
import hmac
import base64
import sqlite3
from pathlib import Path

# Configuration
DB_PATH = "/app/data/tokens.db"
VASCO_DEMO_URL = "https://gs.onespan.cloud/te-demotokens/go6"

def log(level, msg):
    """Log messages to FreeRADIUS log"""
    radiusd.radlog(level, f"simple_token_auth: {msg}")

def init_database():
    """Initialize SQLite database for tokens"""
    try:
        # Ensure directory exists
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                token_type TEXT NOT NULL,
                secret TEXT NOT NULL,
                counter INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create demo tokens if they don't exist
        demo_tokens = [
            ('demo', 'hotp', '3132333435363738393031323334353637383930', 0),
            ('vasco_demo', 'hotp', '76617363615f64656d6f5f746f6b656e5f736563726574', 0),
            ('testuser', 'hotp', '746573745f746f6b656e5f736563726574', 0)
        ]
        
        for username, token_type, secret, counter in demo_tokens:
            cursor.execute('''
                INSERT OR IGNORE INTO tokens (username, token_type, secret, counter)
                VALUES (?, ?, ?, ?)
            ''', (username, token_type, secret, counter))
        
        conn.commit()
        conn.close()
        log(radiusd.L_INFO, "Database initialized successfully")
        return True
        
    except Exception as e:
        log(radiusd.L_ERR, f"Database initialization failed: {str(e)}")
        return False

def hotp(secret, counter, digits=6):
    """Generate HOTP token"""
    try:
        # Convert hex secret to bytes
        key = bytes.fromhex(secret)
        
        # Convert counter to bytes
        counter_bytes = counter.to_bytes(8, byteorder='big')
        
        # Generate HMAC-SHA1
        hmac_result = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        
        # Dynamic truncation
        offset = hmac_result[-1] & 0x0f
        code = ((hmac_result[offset] & 0x7f) << 24) | \
               ((hmac_result[offset + 1] & 0xff) << 16) | \
               ((hmac_result[offset + 2] & 0xff) << 8) | \
               (hmac_result[offset + 3] & 0xff)
        
        # Generate digits
        otp = code % (10 ** digits)
        return str(otp).zfill(digits)
        
    except Exception as e:
        log(radiusd.L_ERR, f"HOTP generation failed: {str(e)}")
        return None

def validate_token(username, password):
    """Validate token against database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user token info
        cursor.execute('SELECT token_type, secret, counter FROM tokens WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if not result:
            log(radiusd.L_AUTH, f"User {username} not found in token database")
            conn.close()
            return False
        
        token_type, secret, counter = result
        
        if token_type == 'hotp':
            # Check current counter and next few values (sync window)
            for i in range(10):  # Check 10 values ahead
                expected_otp = hotp(secret, counter + i)
                if expected_otp and expected_otp == password:
                    # Update counter
                    cursor.execute('UPDATE tokens SET counter = ? WHERE username = ?', 
                                 (counter + i + 1, username))
                    conn.commit()
                    conn.close()
                    log(radiusd.L_INFO, f"HOTP validation successful for {username}")
                    return True
        
        conn.close()
        log(radiusd.L_AUTH, f"Token validation failed for {username}")
        return False
        
    except Exception as e:
        log(radiusd.L_ERR, f"Token validation error: {str(e)}")
        return False

def instantiate(p):
    """Module instantiation"""
    log(radiusd.L_INFO, "Simple token auth module instantiated")
    if init_database():
        log(radiusd.L_INFO, "Token database ready")
        return radiusd.RLM_MODULE_OK
    else:
        log(radiusd.L_ERR, "Failed to initialize token database")
        return radiusd.RLM_MODULE_FAIL

def authenticate(p):
    """Process authentication requests"""
    # Extract username and password from request
    username = None
    password = None
    
    for attr in p:
        if attr[0] == 'User-Name':
            username = attr[1]
        elif attr[0] == 'User-Password':
            password = attr[1]
    
    if not username or not password:
        log(radiusd.L_AUTH, "Missing username or password")
        return radiusd.RLM_MODULE_INVALID
    
    # Validate token
    if validate_token(username, password):
        return radiusd.RLM_MODULE_OK
    else:
        return radiusd.RLM_MODULE_REJECT

def authorize(p):
    """Process authorization requests"""
    return radiusd.RLM_MODULE_OK

def preacct(p):
    """Process preaccounting requests"""
    return radiusd.RLM_MODULE_OK

def accounting(p):
    """Process accounting requests"""
    return radiusd.RLM_MODULE_OK

def detach(p):
    """Module detach"""
    log(radiusd.L_INFO, "Simple token auth module detached")
    return radiusd.RLM_MODULE_OK

# FreeRADIUS module entry points
def pre_proxy(p):
    return radiusd.RLM_MODULE_OK

def post_proxy(p):
    return radiusd.RLM_MODULE_OK

def post_auth(p):
    return radiusd.RLM_MODULE_OK