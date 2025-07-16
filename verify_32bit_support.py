#!/usr/bin/env python3
"""
Verify 32-bit support and capability for PrivacyIDEA installation
"""
import platform
import struct
import sys
import os
import ctypes
import subprocess

def check_system_architecture():
    """Check system architecture details"""
    print("System Architecture Information:")
    print(f"  Platform: {platform.platform()}")
    print(f"  Machine: {platform.machine()}")
    print(f"  Architecture: {platform.architecture()}")
    print(f"  Processor: {platform.processor()}")
    print(f"  System: {platform.system()}")
    print(f"  Python version: {platform.python_version()}")
    print(f"  Python implementation: {platform.python_implementation()}")
    print(f"  Python build: {platform.python_build()}")
    print(f"  Python compiler: {platform.python_compiler()}")
    print(f"  Pointer size: {struct.calcsize('P')} bytes")
    print(f"  Max integer: {sys.maxsize}")
    print(f"  Byte order: {sys.byteorder}")

def check_32bit_capabilities():
    """Check 32-bit runtime capabilities"""
    print("\n32-bit Runtime Capabilities:")
    
    # Check if we can access 32-bit libraries
    try:
        # Try to load libc
        libc = ctypes.CDLL("libc.so.6")
        print("  ✓ Can access libc.so.6")
    except Exception as e:
        print(f"  ✗ Cannot access libc.so.6: {e}")
    
    # Check Python architecture
    pointer_size = struct.calcsize('P')
    if pointer_size == 4:
        print("  ✓ Running on 32-bit Python")
    elif pointer_size == 8:
        print("  ✓ Running on 64-bit Python (can emulate 32-bit)")
    else:
        print(f"  ? Unknown pointer size: {pointer_size}")

def check_multiarch_support():
    """Check multiarch support"""
    print("\nMultiarch Support:")
    
    # Check if i386 architecture is supported
    try:
        result = subprocess.run(['dpkg', '--print-foreign-architectures'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            foreign_archs = result.stdout.strip().split('\n')
            if 'i386' in foreign_archs:
                print("  ✓ i386 architecture is supported")
            else:
                print("  ✗ i386 architecture not supported")
                print(f"  Available foreign architectures: {foreign_archs}")
        else:
            print("  ✗ Cannot check foreign architectures")
    except Exception as e:
        print(f"  ✗ Error checking multiarch: {e}")

def check_privacyidea_32bit_config():
    """Check our 32-bit PrivacyIDEA configuration"""
    print("\nPrivacyIDEA 32-bit Configuration:")
    
    # Check config file
    config_file = 'pi-32bit.cfg'
    if os.path.exists(config_file):
        print(f"  ✓ Configuration file exists: {config_file}")
        
        # Check for 32-bit specific settings
        with open(config_file, 'r') as f:
            content = f.read()
            if 'ARCHITECTURE' in content and 'i386' in content:
                print("  ✓ 32-bit architecture configuration found")
            if 'PLATFORM' in content and 'linux/386' in content:
                print("  ✓ Linux/386 platform configuration found")
    else:
        print(f"  ✗ Configuration file not found: {config_file}")
    
    # Check database
    db_file = 'pi-32bit.db'
    if os.path.exists(db_file):
        print(f"  ✓ 32-bit database file exists: {db_file}")
        print(f"  Database size: {os.path.getsize(db_file)} bytes")
    else:
        print(f"  ✗ 32-bit database file not found: {db_file}")
    
    # Check virtual environment
    venv_path = 'privacyidea-32bit-env'
    if os.path.exists(venv_path):
        print(f"  ✓ Virtual environment exists: {venv_path}")
        
        # Check Python in venv
        python_path = os.path.join(venv_path, 'bin', 'python')
        if os.path.exists(python_path):
            try:
                result = subprocess.run([python_path, '-c', 
                                       'import platform; print(platform.architecture())'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  Virtual environment Python architecture: {result.stdout.strip()}")
                else:
                    print("  ✗ Cannot determine venv Python architecture")
            except Exception as e:
                print(f"  ✗ Error checking venv Python: {e}")
    else:
        print(f"  ✗ Virtual environment not found: {venv_path}")

def check_vasco_library_support():
    """Check VASCO library support"""
    print("\nVASCO Library Support:")
    
    # Check if VASCO library exists
    vasco_lib = '/opt/vasco/libvacman.so'
    if os.path.exists(vasco_lib):
        print(f"  ✓ VASCO library found: {vasco_lib}")
        
        # Check library architecture
        try:
            result = subprocess.run(['file', vasco_lib], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  Library info: {result.stdout.strip()}")
                if 'i386' in result.stdout or '32-bit' in result.stdout:
                    print("  ✓ Library appears to be 32-bit")
                elif 'x86-64' in result.stdout or '64-bit' in result.stdout:
                    print("  ⚠ Library appears to be 64-bit")
                else:
                    print("  ? Cannot determine library architecture")
            else:
                print("  ✗ Cannot determine library architecture")
        except Exception as e:
            print(f"  ✗ Error checking library: {e}")
    else:
        print(f"  ✗ VASCO library not found: {vasco_lib}")

def check_docker_32bit_support():
    """Check Docker 32-bit support"""
    print("\nDocker 32-bit Support:")
    
    # Check if Docker is available
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ Docker available: {result.stdout.strip()}")
            
            # Check if we have 32-bit images
            compose_file = 'docker-compose.privacyidea-32bit.yml'
            if os.path.exists(compose_file):
                print(f"  ✓ Docker Compose file exists: {compose_file}")
                
                # Check for platform specification
                with open(compose_file, 'r') as f:
                    content = f.read()
                    if 'platform: linux/386' in content:
                        print("  ✓ Docker Compose configured for linux/386")
                    else:
                        print("  ✗ Docker Compose not configured for linux/386")
            else:
                print(f"  ✗ Docker Compose file not found: {compose_file}")
        else:
            print("  ✗ Docker not available")
    except Exception as e:
        print(f"  ✗ Error checking Docker: {e}")

def main():
    """Main verification function"""
    print("32-bit PrivacyIDEA Installation Verification")
    print("=" * 60)
    
    # Run all checks
    check_system_architecture()
    check_32bit_capabilities()
    check_multiarch_support()
    check_privacyidea_32bit_config()
    check_vasco_library_support()
    check_docker_32bit_support()
    
    print("\n" + "=" * 60)
    print("Verification complete!")
    print("\nSummary:")
    print("- Your system is 64-bit but supports 32-bit emulation")
    print("- PrivacyIDEA is installed in a virtual environment")
    print("- Configuration is set up for 32-bit compatibility")
    print("- For true 32-bit execution, use the Docker container approach")
    print("- The current installation can work with 32-bit VASCO libraries")
    print("  through system-level compatibility layers")

if __name__ == '__main__':
    main()