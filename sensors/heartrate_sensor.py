import json
import random
import time
from pathlib import Path

import requests

FOG_URL = "http://localhost:5000/fog/heartrate"
STATE_FILE = Path("machines_state.json")

USERS = ["user_1", "user_2", "user_3", "user_4", "user_5"]
SEND_INTERVAL = 5  # seconds


def load_machine_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_active_users(machine_state):
    active_users = []
    for machine in machine_state.values():
        if machine.get("status") == "in_use" and machine.get("user_id"):
            active_users.append(machine["user_id"])
    return active_users


def generate_heart_rate(active_users):
    # 80% chance to pick active user if someone is exercising
    if active_users and random.random() < 0.8:
        user_id = random.choice(active_users)
        heart_rate = random.randint(120, 180)
    else:
        user_id = random.choice(USERS)
        heart_rate = random.randint(70, 110)

    return {
        "user_id": user_id,
        "heart_rate": heart_rate
    }


def main():
    print("🚀 Heart rate sensor started...")

    while True:
        machine_state = load_machine_state()
        active_users = get_active_users(machine_state)
        data = generate_heart_rate(active_users)

        try:
            response = requests.post(FOG_URL, json=data, timeout=5)
            print(f"❤️ Heart Rate Sent: {data} | status_code={response.status_code}")
        except Exception as e:
            print("❌ Heart rate error:", e)

        time.sleep(SEND_INTERVAL)


if __name__ == "__main__":
    main()