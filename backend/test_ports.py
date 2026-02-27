import requests
import json

def test_port(port):
    url = f"http://127.0.0.1:{port}/api/auth/login"
    payload = {"email": "admin@attendance.com", "password": "Admin@123"}
    headers = {"Content-Type": "application/json"}
    try:
        print(f"Testing port {port}...")
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=2)
        print(f"Port {port} Status: {response.status_code}")
    except Exception as e:
        print(f"Port {port} Error: {e}")

test_port(5000)
test_port(80)
