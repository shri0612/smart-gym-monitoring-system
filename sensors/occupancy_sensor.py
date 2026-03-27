import requests
import time
import random

FOG_URL = "http://localhost:5000/fog/occupancy"

def generate_data():
    return {
        "people_count": random.randint(10, 70)
    }

while True:
    data = generate_data()

    try:
        requests.post(FOG_URL, json=data)
        print("👥 Occupancy Sent:", data)
    except Exception as e:
        print("❌ Error:", e)

    time.sleep(5)