#!/usr/bin/env python3
"""
FreeRADIUS Python3 module for Vasco token authentication
"""

import radiusd
import sys
import os

# Add the mods-config/python3 directory to the path
sys.path.insert(0, '/etc/freeradius/3.0/mods-config/python3')

try:
    from go6_token_auth import GO6TokenAuth
    auth = GO6TokenAuth()
    radiusd.radlog(radiusd.L_INFO, "GO6 Token Auth module loaded successfully")
except ImportError as e:
    try:
        from vasco_token_auth import VascoTokenAuth
        auth = VascoTokenAuth()
        radiusd.radlog(radiusd.L_INFO, "Vasco Token Auth module loaded successfully")
    except ImportError as e2:
        radiusd.radlog(radiusd.L_ERR, f"Failed to import token auth modules: {e}, {e2}")
        auth = None

def instantiate(p):
    """Module instantiation"""
    radiusd.radlog(radiusd.L_INFO, "Vasco Token Auth module instantiated")
    return radiusd.RLM_MODULE_OK

def authenticate(p):
    """Authenticate user with token"""
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
            radiusd.radlog(radiusd.L_AUTH, "Missing username or password")
            return radiusd.RLM_MODULE_REJECT
        
        radiusd.radlog(radiusd.L_AUTH, f"Authenticating user: {username}")
        
        if auth and auth.validate_token(username, password):
            radiusd.radlog(radiusd.L_AUTH, f"Authentication successful for {username}")
            return radiusd.RLM_MODULE_OK
        else:
            radiusd.radlog(radiusd.L_AUTH, f"Authentication failed for {username}")
            return radiusd.RLM_MODULE_REJECT
            
    except Exception as e:
        radiusd.radlog(radiusd.L_ERR, f"Authentication error: {e}")
        return radiusd.RLM_MODULE_FAIL

def authorize(p):
    """Authorization - set Auth-Type"""
    radiusd.radlog(radiusd.L_INFO, "Vasco Token Auth authorization")
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
    radiusd.radlog(radiusd.L_INFO, "Vasco Token Auth module detached")
    return radiusd.RLM_MODULE_OK