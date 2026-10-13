import requests
import json

url = "http://192.168.43.146:8000/api/iot/log/"
payload = {
    "patient_id": 7,
    "compartment": 1,
    "status": "TAKEN"
}
headers = {'Content-Type': 'application/json'}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print(response.status_code)
print(response.json())