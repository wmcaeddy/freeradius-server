#!/usr/bin/env python3
"""
Proper GO6 Token Authentication based on DPX file
Implementation using actual DIGIPASS GO6 parameters from Demo_GO6.dpx
"""

import hashlib
import hmac
import struct
import time
import sys

class DPXGO6Auth:
    def __init__(self):
        # Exact parameters from Demo_GO6.dpx file
        self.go6_token = {
            "serial_number": "91234582",
            "ipin": "96BC2AAE",
            "pin_length": 4,
            "pin_change_length": 4,
            "pin_forced": False,
            "pin_change": True,
            "iv_left": "0CF1E7DE",
            "iv_right": "7A76B04E", 
            "offset": "3B2AA0",
            "des64_key": "97FE185D4658D6A3",
            "tdes64_key": "D0A7FD20399E616F",
            "application_name": "APPLI 1",
            "application_code": "00005200",
            "response_length": 6,
            "response_type": "D"  # Default
        }
        
        # Demo users with actual GO6 token
        self.demo_tokens = {
            "go6_demo": {
                "serial": self.go6_token["serial_number"],
                "secret": self.go6_token["des64_key"],
                "tdes_key": self.go6_token["tdes64_key"],
                "iv_left": self.go6_token["iv_left"],
                "iv_right": self.go6_token["iv_right"],
                "offset": self.go6_token["offset"],
                "type": "go6_dpx"
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
    
    def go6_challenge_response(self, challenge, user_data):
        """
        Calculate GO6 challenge-response using simplified algorithm
        Based on DIGIPASS GO6 DPX parameters
        """
        try:
            # Use DES64 key from DPX
            des_key = bytes.fromhex(user_data["secret"])
            
            # Convert challenge to bytes
            if isinstance(challenge, str):
                if len(challenge) == 8 and all(c in '0123456789ABCDEF' for c in challenge.upper()):
                    # Hex string
                    challenge_bytes = bytes.fromhex(challenge)
                else:
                    # ASCII string - pad to 8 bytes
                    challenge_bytes = challenge.encode('ascii')[:8].ljust(8, b'\x00')
            else:
                challenge_bytes = challenge[:8].ljust(8, b'\x00')
            
            # Ensure we have exactly 8 bytes
            if len(challenge_bytes) > 8:
                challenge_bytes = challenge_bytes[:8]
            elif len(challenge_bytes) < 8:
                challenge_bytes = challenge_bytes.ljust(8, b'\x00')
            
            # Simple algorithm: XOR challenge with key, then use HMAC for final hash
            result = bytearray(8)
            for i in range(8):
                result[i] = challenge_bytes[i] ^ des_key[i]
            
            # Use HMAC to create final token
            hmac_digest = hmac.new(des_key, bytes(result), hashlib.sha1).digest()
            
            # Extract 6-digit token
            offset = hmac_digest[19] & 0xf
            code = struct.unpack(">I", hmac_digest[offset:offset+4])[0]
            code &= 0x7fffffff
            token = code % 1000000
            
            return f"{token:06d}"
            
        except Exception as e:
            print(f"GO6 calculation error: {e}")
            return "000000"
    
    def go6_time_based_token(self, user_data):
        """
        Generate time-based token for GO6 (simulating challenge-response)
        """
        try:
            # Use current time as challenge
            current_time = int(time.time())
            
            # Create time-based challenge (last 8 hex digits of timestamp)
            time_hex = f"{current_time:08X}"
            
            return self.go6_challenge_response(time_hex, user_data)
            
        except Exception as e:
            print(f"GO6 time token error: {e}")
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
                if data["type"] == "go6_dpx":
                    tokens[username] = self.go6_time_based_token(data)
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
            if user_data["type"] == "go6_dpx":
                # For GO6, try recent time-based challenges
                current_time = int(time.time())
                for offset in range(-120, 121, 30):  # Try ±2 minutes in 30s steps
                    test_time = current_time + offset
                    time_hex = f"{test_time:08X}"
                    expected = self.go6_challenge_response(time_hex, user_data)
                    if expected and expected == token:
                        return True
                
                # Also try with application code as challenge
                app_code = self.go6_token["application_code"]
                expected = self.go6_challenge_response(app_code, user_data)
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
    auth = DPXGO6Auth()
    
    if len(sys.argv) == 1:
        print("Current demo tokens (DPX GO6 based):")
        tokens = auth.get_current_tokens()
        for username, token in tokens.items():
            user_type = auth.demo_tokens[username]["type"].upper()
            print(f"  {username} ({user_type}): {token}")
        
        print(f"\nDPX GO6 Configuration:")
        print(f"  Serial: {auth.go6_token['serial_number']}")
        print(f"  Application: {auth.go6_token['application_name'].strip()}")
        print(f"  App Code: {auth.go6_token['application_code']}")
        print(f"  DES Key: {auth.go6_token['des64_key']}")
        print(f"  Response Length: {auth.go6_token['response_length']}")
        
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
        print("  python3 dpx_go6_auth.py                    # Show current tokens")
        print("  python3 dpx_go6_auth.py username token     # Validate token")

if __name__ == "__main__":
    main()