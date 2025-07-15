#!/usr/bin/env python3
"""
FreeRADIUS Python3 module for PrivacyIDEA authentication
Connects to PrivacyIDEA server for proper DPX token validation
"""

import radiusd
import requests
import json
import time

# PrivacyIDEA server configuration
PRIVACYIDEA_URL = "http://localhost:5001"
PRIVACYIDEA_REALM = "default"
PRIVACYIDEA_TIMEOUT = 10

def privacyidea_validate(username, password):
    """
    Validate user credentials against PrivacyIDEA
    """
    try:
        # Prepare validation request
        validate_url = f"{PRIVACYIDEA_URL}/validate/check"
        
        data = {
            'user': username,
            'pass': password,
            'realm': PRIVACYIDEA_REALM
        }
        
        # Make request to PrivacyIDEA
        response = requests.post(
            validate_url,
            data=data,
            timeout=PRIVACYIDEA_TIMEOUT,
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if authentication was successful
            if result.get('result', {}).get('status'):
                auth_result = result.get('result', {}).get('value', False)
                if auth_result:
                    radiusd.radlog(radiusd.L_INFO, f"PrivacyIDEA: Authentication successful for {username}")
                    return True
                else:
                    radiusd.radlog(radiusd.L_AUTH, f"PrivacyIDEA: Authentication failed for {username}")
                    return False
            else:
                error_msg = result.get('result', {}).get('error', {}).get('message', 'Unknown error')
                radiusd.radlog(radiusd.L_ERR, f"PrivacyIDEA: Error - {error_msg}")
                return False
        else:
            radiusd.radlog(radiusd.L_ERR, f"PrivacyIDEA: HTTP error {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        radiusd.radlog(radiusd.L_ERR, "PrivacyIDEA: Request timeout")
        return False
    except requests.exceptions.RequestException as e:
        radiusd.radlog(radiusd.L_ERR, f"PrivacyIDEA: Request error - {e}")
        return False
    except Exception as e:
        radiusd.radlog(radiusd.L_ERR, f"PrivacyIDEA: Unexpected error - {e}")
        return False

def instantiate(p):
    """Module instantiation"""
    radiusd.radlog(radiusd.L_INFO, "PrivacyIDEA RADIUS module instantiated")
    radiusd.radlog(radiusd.L_INFO, f"PrivacyIDEA server: {PRIVACYIDEA_URL}")
    return radiusd.RLM_MODULE_OK

def authenticate(p):
    """Authenticate user with PrivacyIDEA"""
    try:
        # Get username and password from request
        username = None
        password = None
        
        for attr in p:
            if attr[0] == 'User-Name':
                username = attr[1]
            elif attr[0] == 'User-Password':
                password = attr[1]
        
        if not username or not password:
            radiusd.radlog(radiusd.L_AUTH, "PrivacyIDEA: Missing username or password")
            return radiusd.RLM_MODULE_REJECT
        
        radiusd.radlog(radiusd.L_AUTH, f"PrivacyIDEA: Authenticating user: {username}")
        
        # Validate with PrivacyIDEA
        if privacyidea_validate(username, password):
            radiusd.radlog(radiusd.L_AUTH, f"PrivacyIDEA: Authentication successful for {username}")
            return radiusd.RLM_MODULE_OK
        else:
            radiusd.radlog(radiusd.L_AUTH, f"PrivacyIDEA: Authentication failed for {username}")
            return radiusd.RLM_MODULE_REJECT
            
    except Exception as e:
        radiusd.radlog(radiusd.L_ERR, f"PrivacyIDEA: Authentication error - {e}")
        return radiusd.RLM_MODULE_FAIL

def authorize(p):
    """Authorization - set Auth-Type"""
    radiusd.radlog(radiusd.L_INFO, "PrivacyIDEA: Authorization")
    return radiusd.RLM_MODULE_OK

def preacct(p):
    """Pre-accounting"""
    return radiusd.RLM_MODULE_OK

def accounting(p):
    """Accounting"""
    return radiusd.RLM_MODULE_OK

def checksimul(p):
    """Simultaneous use check"""
    return radiusd.RLM_MODULE_OK

def pre_proxy(p):
    """Pre-proxy"""
    return radiusd.RLM_MODULE_OK

def post_proxy(p):
    """Post-proxy"""
    return radiusd.RLM_MODULE_OK

def post_auth(p):
    """Post-authentication"""
    return radiusd.RLM_MODULE_OK

def recv_coa(p):
    """Change of Authorization"""
    return radiusd.RLM_MODULE_OK

def send_coa(p):
    """Send Change of Authorization"""
    return radiusd.RLM_MODULE_OK

def detach():
    """Module cleanup"""
    radiusd.radlog(radiusd.L_INFO, "PrivacyIDEA RADIUS module detached")
    return radiusd.RLM_MODULE_OK