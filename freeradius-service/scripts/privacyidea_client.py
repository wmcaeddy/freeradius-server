#!/usr/bin/env python3
"""
PrivacyIDEA Client Module for FreeRADIUS
Connects to separate PrivacyIDEA service for authentication
"""

import radiusd
import requests
import json
import os
import sys
from urllib.parse import urljoin

# Configuration from environment
PRIVACYIDEA_URL = os.environ.get('PRIVACYIDEA_URL', 'https://localhost')
VALIDATE_SSL = os.environ.get('PRIVACYIDEA_VALIDATE_SSL', 'false').lower() == 'true'
REALM = os.environ.get('PRIVACYIDEA_REALM', 'default')
TIMEOUT = int(os.environ.get('PRIVACYIDEA_TIMEOUT', '30'))
DEBUG = os.environ.get('PRIVACYIDEA_DEBUG', 'false').lower() == 'true'

def log(level, msg):
    """Log messages to FreeRADIUS log"""
    radiusd.radlog(level, f"privacyidea_client: {msg}")

def privacyidea_validate(username, password, client_ip=None):
    """
    Validate user credentials against PrivacyIDEA service
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
        if DEBUG:
            log(radiusd.L_INFO, f"Validating user {username} against PrivacyIDEA at {validate_url}")
        
        response = requests.post(
            validate_url,
            data=data,
            verify=VALIDATE_SSL,
            timeout=TIMEOUT,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        )
        
        if DEBUG:
            log(radiusd.L_INFO, f"PrivacyIDEA response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if DEBUG:
                    log(radiusd.L_INFO, f"PrivacyIDEA response: {json.dumps(result)}")
                
                if result.get('result', {}).get('value'):
                    log(radiusd.L_INFO, f"Authentication successful for user {username}")
                    return radiusd.RLM_MODULE_OK
                else:
                    log(radiusd.L_AUTH, f"Authentication failed for user {username}")
                    return radiusd.RLM_MODULE_REJECT
            except json.JSONDecodeError:
                log(radiusd.L_ERR, f"Invalid JSON response from PrivacyIDEA: {response.text}")
                return radiusd.RLM_MODULE_FAIL
        else:
            log(radiusd.L_ERR, f"PrivacyIDEA returned status code: {response.status_code}")
            log(radiusd.L_ERR, f"Response: {response.text}")
            return radiusd.RLM_MODULE_FAIL
            
    except requests.exceptions.Timeout:
        log(radiusd.L_ERR, f"PrivacyIDEA request timeout after {TIMEOUT} seconds")
        return radiusd.RLM_MODULE_FAIL
    except requests.exceptions.ConnectionError:
        log(radiusd.L_ERR, f"Failed to connect to PrivacyIDEA at {PRIVACYIDEA_URL}")
        return radiusd.RLM_MODULE_FAIL
    except Exception as e:
        log(radiusd.L_ERR, f"PrivacyIDEA validation error: {str(e)}")
        return radiusd.RLM_MODULE_FAIL

def instantiate(p):
    """Module instantiation"""
    log(radiusd.L_INFO, "PrivacyIDEA client module instantiated")
    log(radiusd.L_INFO, f"PrivacyIDEA URL: {PRIVACYIDEA_URL}")
    log(radiusd.L_INFO, f"SSL Validation: {VALIDATE_SSL}")
    log(radiusd.L_INFO, f"Realm: {REALM}")
    log(radiusd.L_INFO, f"Debug mode: {DEBUG}")
    
    # Test connection to PrivacyIDEA
    try:
        health_url = urljoin(PRIVACYIDEA_URL, '/health')
        response = requests.get(health_url, timeout=5, verify=VALIDATE_SSL)
        if response.status_code == 200:
            log(radiusd.L_INFO, "PrivacyIDEA service is reachable")
        else:
            log(radiusd.L_WARN, f"PrivacyIDEA health check returned: {response.status_code}")
    except Exception as e:
        log(radiusd.L_WARN, f"PrivacyIDEA health check failed: {str(e)}")
    
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
    log(radiusd.L_INFO, "PrivacyIDEA client module detached")
    return radiusd.RLM_MODULE_OK

# FreeRADIUS module entry points
def pre_proxy(p):
    return radiusd.RLM_MODULE_OK

def post_proxy(p):
    return radiusd.RLM_MODULE_OK

def post_auth(p):
    return radiusd.RLM_MODULE_OK