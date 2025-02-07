import unittest
from unittest.mock import patch
from app import app

# Create a dummy exception class to simulate an OpenAI API error.
class DummyOpenAIError(Exception):
    def __init__(self, message):
        # Mimic the error object structure by attaching an "error" attribute with a "message"
        self.error = type("DummyError", (), {"message": message})

class TestGenerateSummaryErrorMessage(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_generate_summary_generic_error_message_is_returned(self):
        payload = {
            'content': 'This is a sufficiently long text content for summarization purposes.'
        }
        # Use a dummy error message (any message is acceptable)
        dummy_error_message = "Some error occurred during summary generation."

        # Patch the OpenAI client's chat.completions.create to simulate an error.
        with patch("app.client.chat.completions.create", side_effect=DummyOpenAIError(dummy_error_message)):
            response = self.client.post('/summarize', json=payload)
            data = response.get_json()

            # Verify that an error message is provided in the response.
            error_message = data.get("error")
            self.assertIsNotNone(error_message, "No error key in response")
            self.assertNotEqual(error_message.strip(), "", "Error message is empty")
            self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()