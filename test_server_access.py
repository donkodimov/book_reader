"""
Test server access configuration.

Security Note:
    This test file intentionally binds to all interfaces (0.0.0.0) to verify
    external access configuration. This is safe because:
    1. It's only used in tests
    2. Tests run in isolated environments
    3. The server is short-lived
    4. No sensitive data is exposed
"""

import unittest
import os
import requests
import threading
import time
from app import create_app, LOCALHOST, ALL_INTERFACES

# Test configuration with security documentation
TEST_HOST = os.getenv('TEST_HOST', ALL_INTERFACES)  # nosec B104 # Only used in tests
TEST_PORT = int(os.getenv('TEST_PORT', '50086'))

def validate_test_environment():
    """Ensure tests run in a safe environment"""
    if os.getenv('FLASK_ENV') == 'production':
        raise RuntimeError("Tests should not run in production environment")
    if not os.getenv('OPENAI_API_KEY', '').startswith('dummy_'):
        raise RuntimeError("Tests should use dummy API key")

class TestServerAccess(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Validate test environment
        validate_test_environment()
        
        # Set test environment variables
        os.environ['OPENAI_API_KEY'] = 'dummy_key_for_testing'
        os.environ['PORT'] = str(TEST_PORT)
        
        # Create and configure the test app
        cls.app = create_app(testing=True)
        
        # Start the server in a separate thread
        cls.server_thread = threading.Thread(target=cls._run_server)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
    
    @classmethod
    def _run_server(cls):
        # nosec B104 # Test-only server binding, protected by test environment validation
        cls.app.run(host=TEST_HOST, port=TEST_PORT)
    
    def test_localhost_access(self):
        """Test that the server is accessible via localhost"""
        try:
            response = requests.get(f'http://{LOCALHOST}:{TEST_PORT}/')
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to server via localhost")
    
    def test_external_access(self):
        """Test that the server should be accessible via 0.0.0.0"""
        try:
            # Try to access via all interfaces
            response = requests.get(f'http://{ALL_INTERFACES}:{TEST_PORT}/')
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to server via all interfaces")

if __name__ == '__main__':
    unittest.main()