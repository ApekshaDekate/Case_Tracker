import unittest
from unittest.mock import patch, MagicMock, mock_open
import requests
import base64
import json
import cv2
from io import BytesIO
from CaseDetailsExtractor import (
    get_captcha, 
    download_and_encode_pdf, 
    parse_html_to_json, 
    get_case_types_xhr, 
    decode_pdf,
    fetch_case_data  # Ensure this function is properly imported
)

class TestYourScript(unittest.TestCase):

    @patch("CaseDetailsExtractor.requests.Session.get")
    @patch("CaseDetailsExtractor.pytesseract.image_to_string", return_value="ABCD12")
    def test_get_captcha(self, mock_tesseract, mock_get):
        """ Test Captcha Extraction """
        mock_get.return_value.content = b"fake_captcha_image_bytes"
        session = requests.Session()
        captcha_text = get_captcha(session)
        self.assertEqual(captcha_text, "ABCD12")

    @patch("CaseDetailsExtractor.requests.Session.get")
    def test_download_and_encode_pdf(self, mock_get):
        """ Test PDF Download and Encoding """
        fake_pdf_content = b"%PDF-1.4 Fake PDF content"
        mock_get.return_value.content = fake_pdf_content
        mock_get.return_value.raise_for_status = MagicMock()

        session = requests.Session()
        pdf_url = "https://example.com/fake.pdf"
        encoded_pdf = download_and_encode_pdf(session, pdf_url)

        expected_encoded_pdf = base64.b64encode(fake_pdf_content).decode("utf-8")
        self.assertEqual(encoded_pdf, expected_encoded_pdf)

    @patch("builtins.open", new_callable=mock_open, read_data="<html><body><div id='CaseDetails'></div></body></html>")
    @patch("CaseDetailsExtractor.requests.Session")
    def test_parse_html_to_json(self, mock_session, mock_open_file):
        """ Test HTML Parsing to JSON """
        json_result = parse_html_to_json("fake_file.html", mock_session)
        self.assertIsInstance(json_result, dict)  # Ensure it's a dictionary
        self.assertIn("CaseDetails", json_result)  # Ensure expected key exists

    @patch("CaseDetailsExtractor.requests.Session.post")
    def test_get_case_types_xhr(self, mock_post):
        """ Test Fetching Case Types """
        mock_post.return_value.content = "C1~Civil Case#C2~Criminal Case"
        mock_post.return_value.raise_for_status = MagicMock()

        session = requests.Session()
        case_types = get_case_types_xhr(session, 1, 2, 3)  # Hardcoded input values: 1, 2, 3

        expected_case_types = {"C1": "Civil Case", "C2": "Criminal Case"}
        self.assertEqual(case_types, expected_case_types)

    @patch("builtins.open", new_callable=mock_open)
    def test_decode_pdf(self, mock_open_file):
        """ Test PDF Decoding """
        base64_data = base64.b64encode(b"Fake PDF Data").decode("utf-8")
        decode_pdf(base64_data, "output.pdf")

        mock_open_file.assert_called_with("output.pdf", "wb")
        handle = mock_open_file()
        handle.write.assert_called_once()

    @patch("builtins.input", side_effect=["1", "Civil Case", "2024"])  # Hardcoded inputs
    def test_fetch_case_data(self, mock_input):
        """ Test Fetch Case Data with Hardcoded Inputs """
        state_code, case_type, year = fetch_case_data()

        self.assertEqual(state_code, 1)
        self.assertEqual(case_type, "Civil Case")
        self.assertEqual(year, "2024")

# Run tests without asking for input
if __name__ == "__main__":
    with patch("builtins.input", side_effect=["1", "Civil Case", "2024"]):  # Hardcode inputs for ALL TESTS
        unittest.main()
