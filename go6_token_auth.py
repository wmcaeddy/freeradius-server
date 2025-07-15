#!/usr/bin/env python3
"""
GO6 Demo Token Authentication
Based on the actual GO6 DPX file parameters from gs.onespan.cloud
"""

import hashlib
import hmac
import struct
import time
from Crypto.Cipher import DES3
import binascii

class GO6TokenAuth:
    def __init__(self):
        # GO6 Demo Token parameters from Demo_GO6.dpx
        self.go6_config = {
            "serial_number": "91234582",
            "iv_left": "0CF1E7DE",
            "iv_right": "7A76B04E", 
            "offset": "3B2AA0",
            "des64_key": "97FE185D4658D6A3",
            "tdes64_key": "D0A7FD20399E616F",
            "ipin": "96BC2AAE",
            "pin_length": 4,
            "application_code": "00005200"
        }
        
        # Convert hex keys to bytes
        self.des_key = bytes.fromhex(self.go6_config["des64_key"])
        self.tdes_key = bytes.fromhex(self.go6_config["tdes64_key"])
        
        # Demo users with GO6 compatibility
        self.demo_tokens = {
            "go6_demo": {
                "serial": self.go6_config["serial_number"],
                "secret": self.go6_config["tdes64_key"],
                "type": "go6",
                "counter": 0
            },
            "vasco_demo": {
                "secret": "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",
                "counter": 0,
                "type": "totp"
            },
            "demo": {
                "secret": "12345678901234567890",
                "counter": 0,
                "type": "hotp"
            }
        }
    
    def go6_calculate(self, challenge, key_hex):
        """Calculate GO6 response using simplified HOTP-like algorithm"""
        try:
            # Use HMAC-SHA1 with the DES key for compatibility
            key = bytes.fromhex(self.go6_config["des64_key"])
            
            # Convert challenge to counter-like value
            if isinstance(challenge, str):
                counter = int(challenge[-8:], 16) if challenge else int(time.time())
            else:
                counter = int(time.time())
            
            # Use HOTP algorithm with GO6 key
            counter_bytes = struct.pack(">Q", counter)
            hmac_digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()
            
            offset = hmac_digest[19] & 0xf
            code = struct.unpack(">I", hmac_digest[offset:offset+4])[0]
            code &= 0x7fffffff
            code %= 1000000
            
            return f"{code:06d}"
            
        except Exception as e:
            print(f"GO6 calculation error: {e}")
            # Fallback to simple time-based calculation
            try:
                seed = int(key_hex[:8], 16)
                time_factor = int(time.time()) // 30
                token = (seed + time_factor) % 1000000
                return f"{token:06d}"
            except:
                return "000000"
    
    def hotp(self, secret, counter, digits=6):
        """Generate HOTP token"""
        try:
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
        except Exception as e:
            print(f"HOTP error: {e}")
            return "000000"
    
    def totp(self, secret, time_step=30, digits=6):
        """Generate TOTP token"""
        counter = int(time.time()) // time_step
        return self.hotp(secret, counter, digits)
    
    def get_current_tokens(self):
        """Get current tokens for all demo users"""
        tokens = {}
        for username, data in self.demo_tokens.items():
            try:
                if data["type"] == "go6":
                    # For GO6, use current time as challenge
                    challenge = str(int(time.time()))[-8:]  # Last 8 digits of timestamp
                    token = self.go6_calculate(challenge, data["secret"])
                    tokens[username] = token if token else "000000"
                elif data["type"] == "hotp":
                    tokens[username] = self.hotp(data["secret"], data["counter"])
                elif data["type"] == "totp":
                    tokens[username] = self.totp(data["secret"])
            except Exception as e:
                print(f"Error generating token for {username}: {e}")
                tokens[username] = "000000"
        
        return tokens
    
    def validate_token(self, username, token):
        """Validate token for user"""
        if username not in self.demo_tokens:
            return False
        
        user_data = self.demo_tokens[username]
        
        try:
            if user_data["type"] == "go6":
                # For GO6, try recent time challenges
                current_time = int(time.time())
                for offset in range(-60, 61, 30):  # Try ±60 seconds in 30s steps
                    test_time = current_time + offset
                    challenge = str(test_time)[-8:]
                    expected = self.go6_calculate(challenge, user_data["secret"])
                    if expected and expected == token:
                        return True
                return False
                
            elif user_data["type"] == "hotp":
                # Try counter and next few values
                for i in range(user_data["counter"], user_data["counter"] + 10):
                    expected = self.hotp(user_data["secret"], i)
                    if expected == token:
                        self.demo_tokens[username]["counter"] = i + 1
                        return True
                return False
                
            elif user_data["type"] == "totp":
                # Try current time window and previous/next
                current_time = int(time.time())
                for offset in [-30, 0, 30]:
                    test_time = current_time + offset
                    counter = test_time // 30
                    expected = self.hotp(user_data["secret"], counter)
                    if expected == token:
                        return True
                return False
                
        except Exception as e:
            print(f"Validation error for {username}: {e}")
            return False
        
        return False

def main():
    auth = GO6TokenAuth()
    
    if len(sys.argv) == 1:
        print("Current demo tokens (including GO6):")
        tokens = auth.get_current_tokens()
        for username, token in tokens.items():
            user_type = auth.demo_tokens[username]["type"].upper()
            print(f"  {username} ({user_type}): {token}")
        
        print(f"\nGO6 Configuration:")
        print(f"  Serial: {auth.go6_config['serial_number']}")
        print(f"  DES Key: {auth.go6_config['des64_key']}")
        print(f"  3DES Key: {auth.go6_config['tdes64_key']}")
        
    elif len(sys.argv) == 3:
        username, token = sys.argv[1], sys.argv[2]
        if auth.validate_token(username, token):
            print(f"SUCCESS: Token {token} valid for {username}")
            exit(0)
        else:
            print(f"FAILED: Token {token} invalid for {username}")
            exit(1)
    
    else:
        print("Usage:")
        print("  python3 go6_token_auth.py                    # Show current tokens")
        print("  python3 go6_token_auth.py username token     # Validate token")

if __name__ == "__main__":
    import sys
    main()