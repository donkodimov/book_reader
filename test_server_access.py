import unittest
import os
import requests
import threading
import time
from app import create_app

class TestServerAccess(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set test environment variables
        os.environ['OPENAI_API_KEY'] = 'dummy_key_for_testing'
        os.environ['PORT'] = '50086'  # Use the assigned port
        
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
        cls.app.run(host='0.0.0.0', port=50086)
    
    def test_localhost_access(self):
        """Test that the server is accessible via localhost"""
        try:
            response = requests.get('http://127.0.0.1:50086/')
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to server via localhost")
    
    def test_external_access(self):
        """Test that the server should be accessible via 0.0.0.0"""
        try:
            # Try to access via 0.0.0.0
            response = requests.get('http://0.0.0.0:50086/')
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.ConnectionError:
            self.fail("Could not connect to server via 0.0.0.0")

if __name__ == '__main__':
    unittest.main()