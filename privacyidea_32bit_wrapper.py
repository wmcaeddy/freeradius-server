#!/usr/bin/env python3
"""
32-bit PrivacyIDEA wrapper for VASCO library integration
This wrapper ensures proper 32-bit compatibility for VASCO library calls
"""
import ctypes
import sys
import os
import platform
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VascoLibraryWrapper:
    """Wrapper class for 32-bit VASCO library integration"""
    
    def __init__(self, library_path='/opt/vasco/libaal2sdk.so'):
        """Initialize the VASCO library wrapper"""
        self.library_path = library_path
        self.library = None
        self.is_32bit_compatible = self._check_32bit_compatibility()
        
    def _check_32bit_compatibility(self):
        """Check if the system supports 32-bit library loading"""
        try:
            # Check if the library exists
            if not os.path.exists(self.library_path):
                logger.error(f"VASCO library not found: {self.library_path}")
                return False
            
            # Check library architecture
            import subprocess
            result = subprocess.run(['file', self.library_path], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Library info: {result.stdout.strip()}")
                
                # Check if it's a 32-bit library
                if '32-bit' in result.stdout and 'Intel 80386' in result.stdout:
                    logger.info("✓ 32-bit VASCO library detected")
                    return True
                else:
                    logger.warning("⚠ Library may not be 32-bit compatible")
                    return False
            else:
                logger.error("Cannot determine library architecture")
                return False
                
        except Exception as e:
            logger.error(f"Error checking 32-bit compatibility: {e}")
            return False
    
    def load_library(self):
        """Load the VASCO library with proper 32-bit handling"""
        if not self.is_32bit_compatible:
            logger.error("System is not 32-bit compatible")
            return False
        
        try:
            # Load the library
            self.library = ctypes.CDLL(self.library_path)
            logger.info("✓ VASCO library loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading VASCO library: {e}")
            
            # Try with explicit 32-bit loading
            try:
                # Set up environment for 32-bit loading
                os.environ['LD_LIBRARY_PATH'] = '/opt/vasco:/usr/lib32:/lib32'
                
                # Load with explicit path
                self.library = ctypes.CDLL(self.library_path)
                logger.info("✓ VASCO library loaded with 32-bit compatibility")
                return True
                
            except Exception as e2:
                logger.error(f"Failed to load library with 32-bit compatibility: {e2}")
                return False
    
    def get_library_info(self):
        """Get information about the loaded library"""
        if not self.library:
            return None
        
        try:
            # Get library version or info (depends on VASCO library API)
            info = {
                'loaded': True,
                'path': self.library_path,
                'compatibility': '32-bit' if self.is_32bit_compatible else 'unknown',
                'platform': platform.platform(),
                'architecture': platform.architecture(),
                'pointer_size': ctypes.sizeof(ctypes.c_void_p),
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting library info: {e}")
            return None
    
    def validate_token(self, token_data, challenge=None):
        """Validate a token using the VASCO library"""
        if not self.library:
            logger.error("Library not loaded")
            return False
        
        try:
            # This is a placeholder - actual implementation depends on
            # the specific VASCO library API
            logger.info("Token validation requested")
            logger.info(f"Token data length: {len(token_data) if token_data else 0}")
            
            # Example validation logic (needs to be adapted to actual VASCO API)
            # result = self.library.validate_token(token_data, challenge)
            
            # For now, return success for testing
            return True
            
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return False

class PrivacyIDEA32BitService:
    """Main service class for 32-bit PrivacyIDEA integration"""
    
    def __init__(self, config_file='pi-32bit.cfg'):
        """Initialize the 32-bit PrivacyIDEA service"""
        self.config_file = config_file
        self.vasco_wrapper = VascoLibraryWrapper()
        self.service_info = self._get_service_info()
        
    def _get_service_info(self):
        """Get service information"""
        return {
            'name': 'PrivacyIDEA 32-bit Service',
            'version': '3.11.4',
            'architecture': 'i386-compatible',
            'config_file': self.config_file,
            'vasco_support': self.vasco_wrapper.is_32bit_compatible,
            'system_info': {
                'platform': platform.platform(),
                'machine': platform.machine(),
                'architecture': platform.architecture(),
                'python_version': platform.python_version(),
                'pointer_size': ctypes.sizeof(ctypes.c_void_p),
            }
        }
    
    def initialize(self):
        """Initialize the service"""
        logger.info("Initializing 32-bit PrivacyIDEA service...")
        
        # Load VASCO library
        if not self.vasco_wrapper.load_library():
            logger.error("Failed to load VASCO library")
            return False
        
        # Set up environment
        os.environ['PRIVACYIDEA_CONFIGFILE'] = os.path.abspath(self.config_file)
        
        logger.info("✓ 32-bit PrivacyIDEA service initialized")
        return True
    
    def get_status(self):
        """Get service status"""
        return {
            'initialized': self.vasco_wrapper.library is not None,
            'vasco_library': self.vasco_wrapper.get_library_info(),
            'service_info': self.service_info,
            'configuration': {
                'config_file': self.config_file,
                'config_exists': os.path.exists(self.config_file),
                'database_exists': os.path.exists('pi-32bit.db'),
                'log_file': 'pi-32bit.log',
                'log_exists': os.path.exists('pi-32bit.log'),
            }
        }
    
    def authenticate(self, user, token):
        """Authenticate user with token"""
        logger.info(f"Authentication request for user: {user}")
        
        if not self.vasco_wrapper.library:
            logger.error("VASCO library not loaded")
            return False
        
        # Validate token using VASCO library
        return self.vasco_wrapper.validate_token(token)

def main():
    """Main function for testing"""
    print("32-bit PrivacyIDEA Service Test")
    print("=" * 50)
    
    # Initialize service
    service = PrivacyIDEA32BitService()
    
    # Initialize
    if service.initialize():
        print("✓ Service initialized successfully")
        
        # Get status
        status = service.get_status()
        print(f"\nService Status:")
        print(f"  Initialized: {status['initialized']}")
        print(f"  Config file: {status['configuration']['config_file']}")
        print(f"  Config exists: {status['configuration']['config_exists']}")
        print(f"  Database exists: {status['configuration']['database_exists']}")
        print(f"  VASCO support: {status['service_info']['vasco_support']}")
        print(f"  System architecture: {status['service_info']['system_info']['architecture']}")
        print(f"  Pointer size: {status['service_info']['system_info']['pointer_size']} bytes")
        
        # Test authentication
        print(f"\nTesting authentication...")
        result = service.authenticate("testuser", "123456")
        print(f"Authentication result: {result}")
        
    else:
        print("✗ Service initialization failed")

if __name__ == '__main__':
    main()