import requests
import json

url = "http://127.0.0.1:5000/api/auth/login"
payload = {
    "email": "admin@attendance.com",
    "password": "Admin@123"
}
headers = {
    "Content-Type": "application/json"
}

try:
    print(f"Testing login to {url}...")
    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
