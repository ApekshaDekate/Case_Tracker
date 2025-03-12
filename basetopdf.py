import json
import base64
# Open and read the JSON file
with open("task15\case_data5.json", "r") as file:
    data = json.load(file)  # Load JSON data into a Python dictionary

# Print the data
# print(data)

if "Orders" in data and isinstance(data["Orders"], list) and data["Orders"]:
    order_details_base64 = data["Orders"][0]["OrderDetailsBase64"]

    # Decode Base64 and save as PDF
    pdf_data = base64.b64decode(order_details_base64)
    with open("output.pdf", "wb") as pdf_file:
        pdf_file.write(pdf_data)

    print("PDF file saved as 'output.pdf' successfully!")
else:
    print("No orders found")


print(order_details_base64)