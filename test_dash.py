import requests

url = "http://127.0.0.1:8000/api/v1/auth/login"
resp = requests.post(url, json={"badge_no": "PN-2024-ADMIN", "pin": "1234"})
token = resp.json()["data"]["access_token"]

url2 = "http://127.0.0.1:8000/api/v1/dashboard/audit-logs?offset=0&limit=10"
resp2 = requests.get(url2, headers={"Authorization": f"Bearer {token}"})
print(resp2.status_code, resp2.text[:200])
