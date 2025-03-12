import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import cv2
from io import BytesIO
import pytesseract
from PIL import Image
import json
import os



# Threshold for captcha processing
gray_lo = np.array([110, 110, 110])
gray_hi = np.array([255, 255, 255])

CAPTCHA = r'https://hcservices.ecourts.gov.in/ecourtindiaHC/securimage/securimage_show.php'


# Function to extract captcha
def get_captcha(session: requests.Session) -> str:
    try:
        res = session.get(CAPTCHA).content
        opencvImage = cv2.imdecode(np.asarray(bytearray(BytesIO(res).read()), dtype=np.uint8), cv2.IMREAD_COLOR)
        mask = cv2.inRange(opencvImage, gray_lo, gray_hi)
        opencvImage[mask > 0] = (255, 255, 255)
        cv2.imwrite("./captcha.png", opencvImage)
        image = cv2.imread("./captcha.png")
        whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        captcha_text = pytesseract.image_to_string(image, config=f'--psm 7 -c tessedit_char_whitelist={whitelist}').strip()
        return captcha_text
    except Exception as e:
        print(f"Captcha error: {e}")
        return ''


def get_text(element):
    """ Utility function to get text from an element, handling None gracefully. """
    return element.get_text(strip=True) if element else ""
    
def parse_html_to_json(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    result = {}

    #  Extract case details and split combined fields like Filing Date and Registration Date. """
    result["CaseDetails"] = {}
    case_details = soup.find_all('span', class_='case_details_table')

    for detail in case_details:
        label = detail.find('label')
        if label:
            key = label.get_text(strip=True).replace(":", "")
            value = detail.get_text(strip=True).replace(f"{key}:", "").strip()

            # Handle special cases for Filing and Registration Date fields
            if "Filing Number" in key:
                # Extract Filing Number and Filing Date separately
                filing_parts = value.split("Filing Date")
                result["CaseDetails"]["Filing Number"] = filing_parts[0].strip()
                if len(filing_parts) > 1:
                    result["CaseDetails"]["Filing Date"] = filing_parts[1].strip()

            elif "Registration Number" in key:
                # Extract Registration Number and Registration Date separately
                registration_parts = value.split("Registration Date")
                result["CaseDetails"]["Registration Number"] = registration_parts[0].strip()
                if len(registration_parts) > 1:
                    result["CaseDetails"]["Registration Date"] = registration_parts[1].strip().replace("\u00a0", " ")

            else:
                result["CaseDetails"][key] = value


    # Extract Case Status
    result["CaseStatus"] = {}
    case_status = soup.find_all('label', style=True)
    for status in case_status:
        strong_tags = status.find_all('strong')
        if len(strong_tags) >= 2:
            key = strong_tags[0].get_text(strip=True).replace(":", "")
            value = strong_tags[1].get_text(strip=True).replace("\u00a0", " ")
            result["CaseStatus"][key] = value

    # Extract Petitioner and Advocate
    petitioner_section = soup.find('span', class_='Petitioner_Advocate_table')
    result["PetitionerAndAdvocate"] = petitioner_section.get_text(strip=True, separator=" ") if petitioner_section else ""

    # Extract Respondent and Advocate
    respondent_section = soup.find('span', class_='Respondent_Advocate_table')
    result["RespondentAndAdvocate"] = respondent_section.get_text(strip=True, separator=" ") if respondent_section else ""
    

    # Extract History of Case Hearing on Filing Number (optional)
    result["HistoryOfCaseHearingOnFilingNumber"] = []
    history_on_filing_number_table = soup.find('table', class_='history_table')
    # Check for the presence of distinct header for "History of Case Hearing on Filing Number"
    header = soup.find(string="History of Case Hearing on Filing Number")
    if header and history_on_filing_number_table:
        rows = history_on_filing_number_table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:  # Ensure there are enough cells
                history_entry = {
                    "CauseListType": get_text(cells[0]),  # e.g., "Officer Causelist"
                    "Judge": get_text(cells[1]),  # e.g., "ASSISTANT REGISTRAR"
                    "BusinessOnDate": get_text(cells[2]),  # e.g., "17-12-2024"
                    "HearingDate": get_text(cells[3]),  # e.g., ""
                    "PurposeOfHearing": get_text(cells[4])  # e.g., "OBJECTIONS TO BE REMOVED"
                }
                result["HistoryOfCaseHearingOnFilingNumber"].append(history_entry)

        # Extract History of Case Hearing
    result["HistoryOfCaseHearing"] = []
    history_of_case_hearing_header = soup.find(string="History of Case Hearing")

    if history_of_case_hearing_header:
        history_table = history_of_case_hearing_header.find_next('table', class_='history_table')

        if history_table:
            rows = history_table.find_all('tr')[1:]  # Skip the header row
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 5:
                    cause_list_type = get_text(cells[0])
                    if cause_list_type.lower() == "order number":  # Stop reading further rows
                        break
                    history_entry = {
                        "CauseListType": cause_list_type,
                        "Judge": get_text(cells[1]),
                        "BusinessOnDate": get_text(cells[2]),
                        "HearingDate": get_text(cells[3]),
                        "PurposeOfHearing": get_text(cells[4])
                    }
                    result["HistoryOfCaseHearing"].append(history_entry)
                    
    # Extract Orders
    result["Orders"] = []
    order_table = soup.find('table', class_='order_table')
    if order_table:
        rows = order_table.find_all('tr')[1:]  # Skip the header row
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:  # Ensure there are enough cells
                order_entry = {
                    "OrderNumber": get_text(cells[0]),
                    "OrderOn": get_text(cells[1]),
                    "Judge": get_text(cells[2]),
                    "OrderDate": get_text(cells[3]),
                    "OrderDetails": get_text(cells[4])
                }
                result["Orders"].append(order_entry)

    # Extract Category Details
    result["CategoryDetails"] = {}
    category_table = soup.find_all('table')[-3]
    rows = category_table.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        key = get_text(cells[0])
        value = get_text(cells[1])
        result["CategoryDetails"][key] = value

    # Extract Objections
    result["Objections"] = []
    objection_table = soup.find_all('table')[-1]
    rows = objection_table.find_all('tr')[1:]
    for row in rows:
        cells = row.find_all('td')
        objection_entry = {
            "SrNo": get_text(cells[0]),
            "ScrutinyDate": get_text(cells[1]),
            "Objection": get_text(cells[2]),
            "ComplianceDate": get_text(cells[3]),
            "ReceiptDate": get_text(cells[4])
        }
        result["Objections"].append(objection_entry)

    return result

# Example usage
# file_path = "case_data.html"  # Replace with your HTML file path
# output_json_file = "case_data.json"

# parsed_data = parse_html_to_json(file_path)

# # Save parsed data to a JSON file
# with open(output_json_file, 'w', encoding='utf-8') as json_file:
#     json.dump(parsed_data, json_file, indent=4, ensure_ascii=False)

# print(f"JSON data has been saved to {output_json_file}")



# Main script
s = requests.Session()
get_captcha(s)

while True:
    try:
        # User input for the parameters
        print("Enter the required parameters for fetching case data:")
        state_code = int(input("State Code (integer): "))
        dist_code = int(input("District Code (integer): "))
        court_code = int(input("Court Code (integer): "))
        case_type = int(input("Case Type (integer): "))
        case_no = int(input("Case Number (integer): "))
        rgyear = int(input("Registration Year (integer, e.g., 2025): "))

        # Request for csrf token
        data = s.get(f"https://hcservices.ecourts.gov.in/ecourtindiaHC/cases/case_no.php?state_cd={state_code}&dist_cd={dist_code}&court_code={court_code}&stateNm=Bombay#")
        data = BeautifulSoup(data.text, 'lxml')
        csrf_token = data.find_all('input', attrs={'name': '__csrf_magic'})[0]['value']

        # Get captcha
        captcha = get_captcha(s)

        # Prepare parameters for the POST request
        params = {
            "action_code": "showRecords",
            "state_code": state_code,
            "dist_code": dist_code,
            "case_type": case_type,
            "case_no": case_no,
            "rgyear": rgyear,
            "caseNoType": "new",
            "displayOldCaseNo": "NO",
            "captcha": captcha,
            "court_code": court_code,
            "__csrf_magic": csrf_token,
        }

        print("Sending the following parameters:")
        print(json.dumps(params, indent=2))

        # First request to get case data
        res = s.post(r"https://hcservices.ecourts.gov.in/ecourtindiaHC/cases/case_no_qry.php", data=params).text.strip('\ufeff')
        print(res)  # Check the response content for errors
        case_res = res.split('~')
        print("Split result:", case_res)
        if len(case_res) < 4:
            raise ValueError("Unexpected response format.")


        # Prepare payload for the second request
        payload_2 = {
            "__csrf_magic": csrf_token,
            "court_code": court_code,
            "state_code": state_code,
            "dist_code": dist_code,
            "case_no": case_res[0],
            "cino": case_res[3],
            "token": case_res[-1][:-2],
            "appFlag": ""
        }

        # Second request to fetch detailed case history
        case_data = s.post(r'https://hcservices.ecourts.gov.in/ecourtindiaHC/cases/o_civil_case_history.php', data=payload_2).text

        # Save the case history data as an HTML file
        html_file = "case_data_4.html"
        with open(html_file, "w", encoding='ascii', errors='ignore') as f:
            f.write(case_data)

        # Convert the HTML to JSON
        json_data = parse_html_to_json(html_file)
        
        # Save the JSON data to a file
        json_file = "case_data_4.json"
        with open(json_file, "w", encoding='utf-8') as f:
            json.dump(json_data, f, indent=4)

        print(f"Case data has been successfully saved to {json_file}")

    except Exception as e:
        print(f"Error: {e}")

    input("Press Enter to continue...")


#This code is for Bombay High Court