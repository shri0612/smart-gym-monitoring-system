import requests
import time
import random

FOG_URL = "http://localhost:5000/fog/equipment"

def generate_data():
    return {
        "machine_id": f"treadmill_{random.randint(1,3)}",
        "status": "in_use",
        "duration": random.randint(10, 60)
    }

while True:
    data = generate_data()

    try:
        response = requests.post(FOG_URL, json=data)
        print("✅ Equipment Sent:", data)
    except Exception as e:
        print("❌ Error:", e)

    time.sleep(5)  # 🔥 testing (later change to 300)