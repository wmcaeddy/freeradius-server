#!/usr/bin/env python3
"""
Simple Vasco token authentication simulator
Integrates with demo tokens from https://gs.onespan.cloud/te-demotokens/go6
"""

import sys
import hashlib
import hmac
import struct
import time
import json
import requests
from urllib.parse import urlparse

class VascoTokenAuth:
    def __init__(self):
        # Demo tokens from https://gs.onespan.cloud/te-demotokens/go6
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
        """Generate HOTP token"""
        # Convert hex secret to bytes
        if len(secret) % 2 == 0:
            try:
                key = bytes.fromhex(secret)
            except:
                key = secret.encode('utf-8')
        else:
            key = secret.encode('utf-8')
        
        # Create counter bytes
        counter_bytes = struct.pack(">Q", counter)
        
        # Generate HMAC
        hmac_digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        
        # Dynamic truncation
        offset = hmac_digest[19] & 0xf
        code = struct.unpack(">I", hmac_digest[offset:offset+4])[0]
        code &= 0x7fffffff
        code %= 10 ** digits
        
        return f"{code:0{digits}d}"
    
    def totp(self, secret, time_step=30, digits=6):
        """Generate TOTP token"""
        counter = int(time.time()) // time_step
        return self.hotp(secret, counter, digits)
    
    def validate_token(self, username, token):
        """Validate token for user"""
        if username not in self.demo_tokens:
            return False
        
        user_data = self.demo_tokens[username]
        secret = user_data["secret"]
        
        if user_data["type"] == "hotp":
            # Try counter and next few values
            for i in range(user_data["counter"], user_data["counter"] + 10):
                expected = self.hotp(secret, i)
                if expected == token:
                    # Update counter
                    self.demo_tokens[username]["counter"] = i + 1
                    return True
            return False
        
        elif user_data["type"] == "totp":
            # Try current time window and previous/next
            current_time = int(time.time())
            for offset in [-30, 0, 30]:
                test_time = current_time + offset
                counter = test_time // 30
                expected = self.hotp(secret, counter)
                if expected == token:
                    return True
            return False
        
        return False
    
    def get_current_tokens(self):
        """Get current tokens for all demo users"""
        tokens = {}
        for username, data in self.demo_tokens.items():
            if data["type"] == "hotp":
                tokens[username] = self.hotp(data["secret"], data["counter"])
            elif data["type"] == "totp":
                tokens[username] = self.totp(data["secret"])
        return tokens

def main():
    auth = VascoTokenAuth()
    
    if len(sys.argv) == 1:
        # Show current tokens
        print("Current demo tokens:")
        tokens = auth.get_current_tokens()
        for username, token in tokens.items():
            print(f"  {username}: {token}")
        
        print("\nDemo users:")
        for username, data in auth.demo_tokens.items():
            print(f"  {username} ({data['type']}): secret={data['secret'][:10]}...")
    
    elif len(sys.argv) == 3:
        username, token = sys.argv[1], sys.argv[2]
        if auth.validate_token(username, token):
            print(f"SUCCESS: Token {token} valid for {username}")
            sys.exit(0)
        else:
            print(f"FAILED: Token {token} invalid for {username}")
            sys.exit(1)
    
    else:
        print("Usage:")
        print("  python3 vasco_token_auth.py                    # Show current tokens")
        print("  python3 vasco_token_auth.py username token     # Validate token")

if __name__ == "__main__":
    main()