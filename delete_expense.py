import requests

headers = {
    "X-API-Key": "OMHT2409"
}

response = requests.delete("http://127.0.0.1:5000/api/expenses/30", headers=headers)