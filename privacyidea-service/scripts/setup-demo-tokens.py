#!/usr/bin/env python3
"""
Setup demo tokens in PrivacyIDEA for testing
"""

import requests
import json
import os
from urllib.parse import urljoin

# Configuration
PRIVACYIDEA_URL = "http://localhost:80"
ADMIN_USER = "admin"
ADMIN_PASSWORD = os.environ.get('PI_ADMIN_PASSWORD', 'admin')

def log(message):
    print(f"[SETUP] {message}")

def api_request(endpoint, method='GET', data=None, token=None):
    """Make API request to PrivacyIDEA"""
    url = urljoin(PRIVACYIDEA_URL, endpoint)
    headers = {'Content-Type': 'application/json'}
    
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log(f"API request failed: {e}")
        return None

def get_auth_token():
    """Get authentication token from PrivacyIDEA"""
    log("Getting authentication token...")
    
    data = {
        'username': ADMIN_USER,
        'password': ADMIN_PASSWORD
    }
    
    response = api_request('/auth', method='POST', data=data)
    if response and response.get('result', {}).get('status'):
        token = response.get('result', {}).get('value', {}).get('token')
        log("Authentication successful")
        return token
    else:
        log("Authentication failed")
        return None

def create_user(token, username, givenname, surname, email):
    """Create a user in PrivacyIDEA"""
    log(f"Creating user: {username}")
    
    data = {
        'user': username,
        'givenname': givenname,
        'surname': surname,
        'email': email,
        'realm': 'default'
    }
    
    response = api_request('/user', method='POST', data=data, token=token)
    if response and response.get('result', {}).get('status'):
        log(f"User {username} created successfully")
        return True
    else:
        log(f"Failed to create user {username}")
        return False

def create_token(token, username, token_type, secret=None, description=None):
    """Create a token for a user"""
    log(f"Creating {token_type} token for user: {username}")
    
    data = {
        'user': username,
        'realm': 'default',
        'type': token_type
    }
    
    if secret:
        data['otpkey'] = secret
    
    if description:
        data['description'] = description
    
    response = api_request('/token', method='POST', data=data, token=token)
    if response and response.get('result', {}).get('status'):
        serial = response.get('result', {}).get('value', {}).get('serial')
        log(f"Token created successfully: {serial}")
        return serial
    else:
        log(f"Failed to create token for user {username}")
        return None

def setup_demo_tokens():
    """Setup demo tokens and users"""
    log("Starting PrivacyIDEA demo setup...")
    
    # Wait for PrivacyIDEA to be ready
    import time
    time.sleep(5)
    
    # Get authentication token
    auth_token = get_auth_token()
    if not auth_token:
        log("Failed to authenticate with PrivacyIDEA")
        return False
    
    # Demo users and tokens to create
    demo_users = [
        {
            'username': 'demo',
            'givenname': 'Demo',
            'surname': 'User',
            'email': 'demo@example.com',
            'tokens': [
                {
                    'type': 'hotp',
                    'secret': '3132333435363738393031323334353637383930',
                    'description': 'Demo HOTP Token'
                },
                {
                    'type': 'totp',
                    'secret': '3132333435363738393031323334353637383930',
                    'description': 'Demo TOTP Token'
                }
            ]
        },
        {
            'username': 'vasco_demo',
            'givenname': 'Vasco',
            'surname': 'Demo',
            'email': 'vasco@example.com',
            'tokens': [
                {
                    'type': 'hotp',
                    'secret': '76617363615f64656d6f5f746f6b656e5f736563726574',
                    'description': 'Vasco Demo Token'
                }
            ]
        },
        {
            'username': 'testuser',
            'givenname': 'Test',
            'surname': 'User',
            'email': 'test@example.com',
            'tokens': [
                {
                    'type': 'hotp',
                    'secret': '746573745f746f6b656e5f736563726574',
                    'description': 'Test Token'
                }
            ]
        }
    ]
    
    # Create users and tokens
    for user_data in demo_users:
        # Create user
        if create_user(
            auth_token,
            user_data['username'],
            user_data['givenname'],
            user_data['surname'],
            user_data['email']
        ):
            # Create tokens for user
            for token_data in user_data['tokens']:
                create_token(
                    auth_token,
                    user_data['username'],
                    token_data['type'],
                    token_data['secret'],
                    token_data['description']
                )
    
    log("Demo setup completed!")
    log("Available demo users:")
    log("  - demo (HOTP/TOTP tokens)")
    log("  - vasco_demo (Vasco token)")
    log("  - testuser (HOTP token)")
    return True

if __name__ == '__main__':
    setup_demo_tokens()