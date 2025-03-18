import unittest
import numpy as np
import requests
import base64
import json
import cv2
from unittest.mock import patch, MagicMock
from io import BytesIO
from fastapi.testclient import TestClient

# Import functions and app from your FastAPI script (rename test.py to app_module.py to avoid conflicts)
from test import (
    get_captcha,
    fetch_case_data,
    app  # Ensure `app` is the FastAPI instance in your script
)


class TestFastAPIEndpoints(unittest.TestCase):

    @patch("test.requests.Session.get")
    @patch("test.pytesseract.image_to_string", return_value="ABCD12")
    def test_get_captcha(self, mock_tesseract, mock_get):
        """Test Captcha Extraction."""
        # Create a fake white image for testing
        fake_image = np.ones((100, 100, 3), dtype=np.uint8) * 255  
        _, encoded_image = cv2.imencode('.png', fake_image)
        mock_get.return_value.content = encoded_image.tobytes()

        session = requests.Session()
        captcha_text = get_captcha(session)
        
        # Ensure extracted text matches expected output
        self.assertEqual(captcha_text, "ABCD12")

    @patch("test.requests.Session.post")
    def test_fetch_case_data(self, mock_post):
        """Test Fetch Case Data API."""
        # Mock API response
        mock_post.return_value.text = json.dumps({"message": "Case data fetched successfully!"})
        mock_post.return_value.status_code = 200
        
        sample_data = {
            "state_code": 1,
            "dist_code": 1,
            "court_code": 1,
            "case_type": 1,
            "case_no": 1,
            "rgyear": 2024
        }

        # Use TestClient to simulate a FastAPI request
        client = TestClient(app)
        response = client.post("/fetch/", json=sample_data)

        # Validate API response
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

# Run tests
if __name__ == "__main__":
    unittest.main()
