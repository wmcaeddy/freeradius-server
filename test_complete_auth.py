#!/usr/bin/env python3
"""
Complete RADIUS OTP Authentication Test
Tests FreeRADIUS with Vasco token authentication including demo tokens from gs.onespan.cloud
"""

import subprocess
import time
import sys
import os
sys.path.append('./test-scripts')
from vasco_token_auth import VascoTokenAuth

def run_radtest(username, password, server="localhost", port="1812", secret="testing123"):
    """Run radtest command and return result"""
    cmd = ["radtest", username, password, server, port, secret]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def test_user_authentication(username, token):
    """Test authentication for a specific user"""
    print(f"\n🔐 Testing {username} with token {token}")
    
    success, stdout, stderr = run_radtest(username, token)
    
    if success and "Access-Accept" in stdout:
        print(f"✅ SUCCESS: {username} authenticated successfully")
        return True
    else:
        print(f"❌ FAILED: {username} authentication failed")
        if stderr:
            print(f"   Error: {stderr}")
        return False

def main():
    print("🚀 FreeRADIUS OTP Authentication Test Suite")
    print("=" * 50)
    
    # Initialize token authenticator
    auth = VascoTokenAuth()
    
    # Get current tokens
    print("\n📊 Current Demo Tokens:")
    current_tokens = auth.get_current_tokens()
    for username, token in current_tokens.items():
        print(f"   {username}: {token}")
    
    print("\n🧪 Running Authentication Tests...")
    
    # Test each demo user
    test_results = {}
    for username, token in current_tokens.items():
        test_results[username] = test_user_authentication(username, token)
    
    # Test invalid authentication
    print(f"\n🔒 Testing Invalid Authentication...")
    invalid_success = test_user_authentication("demo", "123456")  # Wrong token
    test_results["invalid_test"] = not invalid_success  # Should fail
    
    if not invalid_success:
        print("✅ SUCCESS: Invalid token correctly rejected")
    else:
        print("❌ FAILED: Invalid token incorrectly accepted")
    
    # Summary
    print(f"\n📈 Test Summary:")
    print("=" * 30)
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests completed successfully!")
        print("\n🌐 Vasco Demo Token Integration:")
        print("   - FreeRADIUS server is ready for production testing")
        print("   - Demo tokens from gs.onespan.cloud/te-demotokens/go6 can be tested")
        print("   - RADIUS authentication on port 1812 is working")
        print("   - OTP validation is functioning correctly")
        
        print(f"\n🔧 Test Commands:")
        for username, token in current_tokens.items():
            print(f"   radtest {username} {token} localhost 0 testing123")
        
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())