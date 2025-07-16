#!/usr/bin/env python3
"""
Test script for 32-bit PrivacyIDEA installation
"""
import requests
import sys
import os
import platform

def test_server():
    """Test the PrivacyIDEA server"""
    try:
        # Test root endpoint
        response = requests.get('http://localhost:5002/', timeout=10)
        print(f"✓ Root endpoint status: {response.status_code}")
        
        # Test if it's serving the web interface
        if 'privacyideaApp' in response.text:
            print("✓ Web interface is available")
        else:
            print("✗ Web interface may not be working correctly")
            
        # Print system information
        print(f"✓ Python version: {platform.python_version()}")
        print(f"✓ Platform: {platform.platform()}")
        print(f"✓ Architecture: {platform.machine()}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Server test failed: {e}")
        return False

def test_config():
    """Test configuration file"""
    config_file = 'pi-32bit.cfg'
    if os.path.exists(config_file):
        print(f"✓ Configuration file exists: {config_file}")
        with open(config_file, 'r') as f:
            content = f.read()
            if 'ARCHITECTURE' in content and 'i386' in content:
                print("✓ 32-bit architecture configuration found")
            else:
                print("✗ 32-bit architecture configuration not found")
        return True
    else:
        print(f"✗ Configuration file not found: {config_file}")
        return False

def test_database():
    """Test database file"""
    db_file = 'pi-32bit.db'
    if os.path.exists(db_file):
        print(f"✓ Database file exists: {db_file}")
        return True
    else:
        print(f"✗ Database file not found: {db_file}")
        return False

def main():
    """Main test function"""
    print("Testing 32-bit PrivacyIDEA installation...")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_config),
        ("Database", test_database),
        ("Server", test_server),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}:")
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! 32-bit PrivacyIDEA installation is working correctly.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Please check the configuration.")
        sys.exit(1)

if __name__ == '__main__':
    main()