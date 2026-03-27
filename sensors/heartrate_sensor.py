import requests
import time
import random

FOG_URL = "http://localhost:5000/fog/heartrate"

def generate_data():
    return {
        "user_id": f"user_{random.randint(1,5)}",
        "heart_rate": random.randint(80, 180)
    }

while True:
    data = generate_data()

    try:
        requests.post(FOG_URL, json=data)
        print("❤️ Heart Rate Sent:", data)
    except Exception as e:
        print("❌ Error:", e)

    time.sleep(5)  # later change to 300