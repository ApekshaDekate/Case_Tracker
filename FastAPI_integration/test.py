from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
#import json
#import time
from io import BytesIO
#import base64
import numpy as np
import cv2
import pytesseract

app = FastAPI()

# Enable CORS (optional for frontend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend domain for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Threshold for captcha processing
gray_lo = np.array([110, 110, 110])
gray_hi = np.array([255, 255, 255])

CAPTCHA = r'https://hcservices.ecourts.gov.in/ecourtindiaHC/securimage/securimage_show.php'

# Captcha Extraction Function
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

# Pydantic Model for JSON Input
class CaseData(BaseModel):
    state_code: int
    dist_code: int
    court_code: int
    case_type: int
    case_no: int
    rgyear: int

# API Endpoint for Captcha Data
@app.post("/fetch/")
async def fetch_case_data(data: CaseData):
    try:
        s = requests.Session()
        captcha = get_captcha(s)

        params = {
            "action_code": "showRecords",
            "state_code": data.state_code,
            "dist_code": data.dist_code,
            "case_type": data.case_type,
            "case_no": data.case_no,
            "rgyear": data.rgyear,
            "caseNoType": "new",
            "displayOldCaseNo": "NO",
            "captcha": captcha,
            "court_code": data.court_code,
        }

        res = s.post(
            "https://hcservices.ecourts.gov.in/ecourtindiaHC/cases/case_no_qry.php",
            data=params
        ).text.strip('\ufeff')

        if "Invalid Captcha" in res:
            raise HTTPException(status_code=400, detail="Invalid Captcha. Please try again.")

        # Process case data
        case_res = res.split('~')
        if len(case_res) < 4:
            raise HTTPException(status_code=400, detail="Unexpected response format.")

        payload_2 = {
            "court_code": data.court_code,
            "state_code": data.state_code,
            "dist_code": data.dist_code,
            "case_no": case_res[0],
            "cino": case_res[3],
            "token": case_res[-1][:-2],
            "appFlag": ""
        }

        case_data = s.post(
            "https://hcservices.ecourts.gov.in/ecourtindiaHC/cases/o_civil_case_history.php",
            data=payload_2
        ).text

        html_file = "case_data.html"
        with open(html_file, "w", encoding='ascii', errors='ignore') as f:
            f.write(case_data)

        return JSONResponse(content={"message": "Case data fetched successfully!", "data": case_data})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root Endpoint for Testing
@app.get("/")
async def root():
    return {"message": "FastAPI Server is Running!"}
