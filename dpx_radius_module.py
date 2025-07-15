#!/usr/bin/env python3
"""
FreeRADIUS Python3 module for DPX GO6 authentication
Direct DPX-based authentication without PrivacyIDEA server
"""

import radiusd
import sys
import os

# Add the mods-config/python3 directory to the path
sys.path.insert(0, '/etc/freeradius/3.0/mods-config/python3')

try:
    from dpx_go6_auth import DPXGO6Auth
    auth = DPXGO6Auth()
    radiusd.radlog(radiusd.L_INFO, "DPX GO6 Auth module loaded successfully")
except ImportError as e:
    radiusd.radlog(radiusd.L_ERR, f"Failed to import DPX GO6 auth module: {e}")
    auth = None

def instantiate(p):
    """Module instantiation"""
    radiusd.radlog(radiusd.L_INFO, "DPX GO6 Auth module instantiated")
    if auth:
        radiusd.radlog(radiusd.L_INFO, f"DPX Serial: {auth.go6_token['serial_number']}")
        radiusd.radlog(radiusd.L_INFO, f"DPX Application: {auth.go6_token['application_name']}")
    return radiusd.RLM_MODULE_OK

def authenticate(p):
    """Authenticate user with DPX GO6 token"""
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
            radiusd.radlog(radiusd.L_AUTH, "DPX GO6: Missing username or password")
            return radiusd.RLM_MODULE_REJECT
        
        radiusd.radlog(radiusd.L_AUTH, f"DPX GO6: Authenticating user: {username}")
        
        if auth and auth.validate_token(username, password):
            radiusd.radlog(radiusd.L_AUTH, f"DPX GO6: Authentication successful for {username}")
            return radiusd.RLM_MODULE_OK
        else:
            radiusd.radlog(radiusd.L_AUTH, f"DPX GO6: Authentication failed for {username}")
            return radiusd.RLM_MODULE_REJECT
            
    except Exception as e:
        radiusd.radlog(radiusd.L_ERR, f"DPX GO6: Authentication error: {e}")
        return radiusd.RLM_MODULE_FAIL

def authorize(p):
    """Authorization - set Auth-Type"""
    radiusd.radlog(radiusd.L_INFO, "DPX GO6: Authorization")
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
    radiusd.radlog(radiusd.L_INFO, "DPX GO6 Auth module detached")
    return radiusd.RLM_MODULE_OK