import requests
from bs4 import BeautifulSoup
import csv

url = "https://hcservices.ecourts.gov.in/ecourtindiaHC/"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Extract and store data
data = []
links = soup.find_all('a', href=True)

for link in links:
    href = link['href']
    if "index_highcourt.php" in href:
        params = dict(param.split('=') for param in href.split('?')[1].split('&'))
        state_code = params.get('state_cd', '')
        dist_code = params.get('dist_cd', '')
        court_code = params.get('court_code', '')
        state_name = params.get('stateNm', '').replace('+', ' ')
        court_name = link.text.strip()

        data.append({
            "State Code": state_code,
            "District Code": dist_code,
            "Court Code": court_code,
            "State Name": state_name,
            "Court Name": court_name
        })

# Save data to CSV
with open("courts_data.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["State Code", "District Code", "Court Code", "State Name", "Court Name"])
    writer.writeheader()
    writer.writerows(data)

print("Data saved to courts_data.csv")
