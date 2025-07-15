#!/usr/bin/env python3
"""
PrivacyIDEA Authentication Module for FreeRADIUS
Supports Vasco and other token types via PrivacyIDEA API
"""

import radiusd
import requests
import json
import os
import sys
from urllib.parse import urljoin

# Configuration from environment
PRIVACYIDEA_URL = os.environ.get('PRIVACYIDEA_URL', 'http://privacyidea:80')
VALIDATE_SSL = os.environ.get('PRIVACYIDEA_VALIDATE_SSL', 'false').lower() == 'true'
REALM = os.environ.get('PRIVACYIDEA_REALM', 'default')
TIMEOUT = int(os.environ.get('PRIVACYIDEA_TIMEOUT', '10'))

# For demo Vasco tokens
VASCO_DEMO_URL = "https://gs.onespan.cloud/te-demotokens/go6"

def log(level, msg):
    """Log messages to FreeRADIUS log"""
    radiusd.radlog(level, f"privacyidea_auth: {msg}")

def validate_vasco_demo(username, password):
    """
    Validate against Vasco demo tokens
    This is specifically for testing with the demo environment
    """
    try:
        # For demo purposes, we might need to interact with the Vasco demo page
        # In production, this would be replaced with actual PrivacyIDEA validation
        log(radiusd.L_INFO, f"Validating Vasco demo token for user: {username}")
        
        # Placeholder for Vasco demo validation
        # In a real implementation, you would:
        # 1. Parse the demo page or use an API if available
        # 2. Validate the token
        # For now, we'll pass through to PrivacyIDEA
        return None
    except Exception as e:
        log(radiusd.L_ERR, f"Vasco demo validation error: {str(e)}")
        return None

def privacyidea_validate(username, password, client_ip=None):
    """
    Validate user credentials against PrivacyIDEA
    """
    try:
        # Build validation URL
        validate_url = urljoin(PRIVACYIDEA_URL, '/validate/check')
        
        # Prepare request data
        data = {
            'user': username,
            'pass': password
        }
        
        if REALM:
            data['realm'] = REALM
            
        if client_ip:
            data['client'] = client_ip
        
        # Make request to PrivacyIDEA
        log(radiusd.L_INFO, f"Validating user {username} against PrivacyIDEA")
        
        response = requests.post(
            validate_url,
            data=data,
            verify=VALIDATE_SSL,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('result', {}).get('value'):
                log(radiusd.L_INFO, f"Authentication successful for user {username}")
                return radiusd.RLM_MODULE_OK
            else:
                log(radiusd.L_AUTH, f"Authentication failed for user {username}")
                return radiusd.RLM_MODULE_REJECT
        else:
            log(radiusd.L_ERR, f"PrivacyIDEA returned status code: {response.status_code}")
            return radiusd.RLM_MODULE_FAIL
            
    except requests.exceptions.Timeout:
        log(radiusd.L_ERR, "PrivacyIDEA request timeout")
        return radiusd.RLM_MODULE_FAIL
    except Exception as e:
        log(radiusd.L_ERR, f"PrivacyIDEA validation error: {str(e)}")
        return radiusd.RLM_MODULE_FAIL

def instantiate(p):
    """Module instantiation"""
    log(radiusd.L_INFO, "PrivacyIDEA module instantiated")
    log(radiusd.L_INFO, f"PrivacyIDEA URL: {PRIVACYIDEA_URL}")
    log(radiusd.L_INFO, f"SSL Validation: {VALIDATE_SSL}")
    return radiusd.RLM_MODULE_OK

def authenticate(p):
    """Process authentication requests"""
    # Extract username and password from request
    username = None
    password = None
    client_ip = None
    
    for attr in p:
        if attr[0] == 'User-Name':
            username = attr[1]
        elif attr[0] == 'User-Password':
            password = attr[1]
        elif attr[0] == 'Client-IP-Address':
            client_ip = attr[1]
    
    if not username or not password:
        log(radiusd.L_AUTH, "Missing username or password")
        return radiusd.RLM_MODULE_INVALID
    
    # Check if this is a Vasco demo token request
    if username.startswith('vasco_demo_'):
        demo_result = validate_vasco_demo(username, password)
        if demo_result is not None:
            return demo_result
    
    # Validate against PrivacyIDEA
    return privacyidea_validate(username, password, client_ip)

def authorize(p):
    """Process authorization requests"""
    # For now, we just accept if authentication passed
    return radiusd.RLM_MODULE_OK

def preacct(p):
    """Process preaccounting requests"""
    return radiusd.RLM_MODULE_OK

def accounting(p):
    """Process accounting requests"""
    return radiusd.RLM_MODULE_OK

def detach(p):
    """Module detach"""
    log(radiusd.L_INFO, "PrivacyIDEA module detached")
    return radiusd.RLM_MODULE_OK

# FreeRADIUS module entry points
def pre_proxy(p):
    return radiusd.RLM_MODULE_OK

def post_proxy(p):
    return radiusd.RLM_MODULE_OK

def post_auth(p):
    return radiusd.RLM_MODULE_OK