import requests
import time
import random

FOG_URL = "http://localhost:5000/fog/temperature"

def generate_data():
    return {
        "temperature": random.randint(15, 40)
    }

while True:
    data = generate_data()

    try:
        requests.post(FOG_URL, json=data)
        print("🌡️ Temperature Sent:", data)
    except Exception as e:
        print("❌ Error:", e)

    time.sleep(5)