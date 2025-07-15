#!/usr/bin/env python3
"""
Proxy Load Balance Module for FreeRADIUS
Implements "first positive response wins" logic for multiple backends
"""

import radiusd
import pyrad.packet
import pyrad.dictionary
import pyrad.client
import socket
import threading
import time
import json
import os

# Configuration
BACKENDS = json.loads(os.environ.get('PROXY_BACKENDS', '[]'))
TIMEOUT = int(os.environ.get('PROXY_TIMEOUT', '5'))
DICTIONARY_PATH = "/usr/share/freeradius/dictionary"

# Load RADIUS dictionary
try:
    DICTIONARY = pyrad.dictionary.Dictionary(DICTIONARY_PATH)
except:
    DICTIONARY = None

def log(level, msg):
    """Log messages to FreeRADIUS log"""
    radiusd.radlog(level, f"proxy_loadbalance: {msg}")

class BackendProxy:
    """Handles proxying to a single backend"""
    
    def __init__(self, config):
        self.host = config['host']
        self.port = config.get('port', 1812)
        self.secret = config['secret'].encode('utf-8')
        self.name = config.get('name', self.host)
        
    def send_request(self, username, password, nas_ip='127.0.0.1'):
        """Send authentication request to backend"""
        try:
            # Create RADIUS client
            client = pyrad.client.Client(
                server=self.host,
                authport=self.port,
                secret=self.secret,
                dict=DICTIONARY
            )
            client.timeout = TIMEOUT
            
            # Create Access-Request packet
            req = client.CreateAuthPacket(code=pyrad.packet.AccessRequest)
            req["User-Name"] = username
            req["User-Password"] = req.PwCrypt(password)
            req["NAS-IP-Address"] = nas_ip
            
            # Send request and get reply
            reply = client.SendPacket(req)
            
            if reply.code == pyrad.packet.AccessAccept:
                return True, "Access-Accept", reply
            elif reply.code == pyrad.packet.AccessReject:
                return False, "Access-Reject", reply
            else:
                return False, f"Unknown code: {reply.code}", reply
                
        except socket.timeout:
            return False, "Timeout", None
        except Exception as e:
            return False, str(e), None

def proxy_to_backends(username, password, nas_ip='127.0.0.1'):
    """
    Proxy request to all backends in parallel
    Return success if ANY backend accepts
    """
    if not BACKENDS:
        log(radiusd.L_ERR, "No backends configured")
        return radiusd.RLM_MODULE_FAIL
    
    results = {}
    threads = []
    lock = threading.Lock()
    
    def check_backend(backend_config):
        """Thread function to check a single backend"""
        proxy = BackendProxy(backend_config)
        log(radiusd.L_INFO, f"Checking backend: {proxy.name}")
        
        success, message, reply = proxy.send_request(username, password, nas_ip)
        
        with lock:
            results[proxy.name] = {
                'success': success,
                'message': message,
                'reply': reply
            }
        
        if success:
            log(radiusd.L_INFO, f"Backend {proxy.name} returned: {message}")
        else:
            log(radiusd.L_AUTH, f"Backend {proxy.name} failed: {message}")
    
    # Start threads for all backends
    for backend in BACKENDS:
        thread = threading.Thread(target=check_backend, args=(backend,))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Wait for all threads to complete or timeout
    start_time = time.time()
    for thread in threads:
        remaining = TIMEOUT - (time.time() - start_time)
        if remaining > 0:
            thread.join(timeout=remaining)
    
    # Check results - if ANY backend accepted, we accept
    for backend_name, result in results.items():
        if result['success']:
            log(radiusd.L_INFO, f"Authentication accepted by {backend_name}")
            return radiusd.RLM_MODULE_OK
    
    # All backends rejected or failed
    log(radiusd.L_AUTH, f"All backends rejected authentication for {username}")
    return radiusd.RLM_MODULE_REJECT

def instantiate(p):
    """Module instantiation"""
    log(radiusd.L_INFO, "Proxy loadbalance module instantiated")
    log(radiusd.L_INFO, f"Configured backends: {len(BACKENDS)}")
    return radiusd.RLM_MODULE_OK

def authenticate(p):
    """Process authentication requests"""
    # Extract attributes from request
    username = None
    password = None
    nas_ip = '127.0.0.1'
    
    for attr in p:
        if attr[0] == 'User-Name':
            username = attr[1]
        elif attr[0] == 'User-Password':
            password = attr[1]
        elif attr[0] == 'NAS-IP-Address':
            nas_ip = attr[1]
    
    if not username or not password:
        log(radiusd.L_AUTH, "Missing username or password")
        return radiusd.RLM_MODULE_INVALID
    
    # Proxy to backends
    return proxy_to_backends(username, password, nas_ip)

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
    log(radiusd.L_INFO, "Proxy loadbalance module detached")
    return radiusd.RLM_MODULE_OK