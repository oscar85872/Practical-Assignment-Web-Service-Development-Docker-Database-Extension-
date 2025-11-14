import requests

expense = {
    "amount": 500.0,
    "description": "PS5", 
    "category": "entertainment",
    "date": "2025-11-13",
    "type": "expense"
}

headers = {
    "X-API-Key": "OMHT2409"
}

response = requests.post("http://127.0.0.1:5000/api/expenses", json=expense, headers=headers)

if response.status_code == 201:
    print("Expense added!")
else:
    print("Error:", response.json()['error'])