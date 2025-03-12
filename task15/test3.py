import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import cv2
from io import BytesIO
import pytesseract
from PIL import Image

gray_lo=np.array([110,110,110])
gray_hi=np.array([255,255,255])


CAPTCHA = r'https://hcservices.ecourts.gov.in/ecourtindiaHC/securimage/securimage_show.php'


def get_captcha(session:requests.Session) -> str:

    try:
        # Get captcha text
        res = session.get(CAPTCHA).content
        opencvImage = cv2.imdecode(np.asarray(bytearray(BytesIO(res).read()), dtype=np.uint8), cv2.COLOR_RGB2BGR)
        mask=cv2.inRange(opencvImage,gray_lo,gray_hi)
        opencvImage[mask>0]=(255,255,255)
        cv2.imwrite("./captcha.png",opencvImage)
        image = cv2.imread("./captcha.png")
        whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

        # Use pytesseract to extract text with a character whitelist
        captcha_text = pytesseract.image_to_string(image, config=f'--psm 7 -c tessedit_char_whitelist={whitelist}').strip()
         
        print(s.cookies.get_dict())
        return captcha_text
        
    except Exception as e:
        print(e)
        return ''
    

import json


s = requests.Session()
get_captcha(s)

while True:

    try:
        data = s.get("https://hcservices.ecourts.gov.in/ecourtindiaHC/cases/case_no.php?state_cd=1&dist_cd=1&court_code=1&stateNm=Bombay#")

        data = BeautifulSoup(data.text,'lxml')
        csrf_token = data.find_all('input',attrs={'name':'__csrf_magic'})[0]['value']

        captcha = get_captcha(s)
        params = {
            "action_code" : "showRecords",
            "state_code" : 24,
            "dist_code" : 1,
            "case_type" : 1,
            "case_no" : 1,
            "rgyear" : 2025,
            "caseNoType" : "new",
            "displayOldCaseNo" : "NO",
            "captcha" : captcha,
            "court_code" : 1,
        }

        params['__csrf_magic'] = csrf_token
        


        print(json.dumps(params,indent=2))

        res = s.post(r"https://hcservices.ecourts.gov.in/ecourtindiaHC/cases/case_no_qry.php",data=params).text.strip('\ufeff')
        case_res = res.split('~')

        payload_2 = {

            "__csrf_magic" : csrf_token,
            "court_code" : params['court_code'],
            "state_code" : params['state_code'],
            "dist_code" : params['dist_code'],
            "case_no" : case_res[0],
            "cino" : case_res[3],
            "token" : case_res[-1][:-2],
            "appFlag" : ""
        }

        case_data = s.post(r'https://hcservices.ecourts.gov.in/ecourtindiaHC/cases/o_civil_case_history.php',data=payload_2).text

        with open("data.html","w",encoding='ascii',errors='ignore') as f:
            f.write(case_data)
    except Exception as e:
        print(e)

    input()