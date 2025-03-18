import unittest
from unittest.mock import patch
import json
import numpy as np
import cv2
import requests
from fastapi.testclient import TestClient
from test import app, get_captcha, fetch_case_data  # Import FastAPI app

class TestFastAPIEndpoints(unittest.TestCase):
    
    @patch("test.requests.Session.get")
    @patch("test.pytesseract.image_to_string", return_value="ABCD12")
    def test_get_captcha(self, mock_tesseract, mock_get):
        """Test Captcha Extraction."""
        fake_image = np.ones((100, 100, 3), dtype=np.uint8) * 255  # White image
        _, encoded_image = cv2.imencode('.png', fake_image)
        mock_get.return_value.content = encoded_image.tobytes()
        session = requests.Session()
        captcha_text = get_captcha(session)
        self.assertEqual(captcha_text, "ABCD12")

    def test_fetch_case_data(self):
        """Test Fetch Case Data API."""
        client = TestClient(app)  # Create TestClient

        sample_data = {
            "state_code": 1,
            "dist_code": 1,
            "court_code": 1,
            "case_type": 1,
            "case_no": 1,
            "rgyear": 2024
        }

        response = client.post("/fetch/", json=sample_data)  # Send request
        print("Response Status Code:", response.status_code)  # Debug
        print("Response Content:", response.text)  # Debug (full error message)

        self.assertEqual(response.status_code, 200)  # Expect 200 OK
        self.assertIn("message", response.json())  # Check response format

# Run tests
if __name__ == "__main__":
    unittest.main()
