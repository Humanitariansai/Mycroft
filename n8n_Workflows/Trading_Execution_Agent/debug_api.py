#!/usr/bin/env python3
import requests
import json

response = requests.post(
    "http://localhost:8001/api/analyze",
    json={"ticker": "AAPL"},
    timeout=30
)

print("Status Code:", response.status_code)
print("Response:")
data = response.json()
print(json.dumps(data, indent=2))

# Check final_recommendation structure
final_rec = data["data"]["final_recommendation"]
print("\nFinal Recommendation Keys:", list(final_rec.keys()))
print("Final Recommendation:", final_rec)