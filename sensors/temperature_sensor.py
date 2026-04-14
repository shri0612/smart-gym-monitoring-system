import json
import random
import time
from pathlib import Path

import requests

FOG_URL = "http://localhost:5000/fog/temperature"
STATE_FILE = Path("temperature_state.json")
OCCUPANCY_FILE = Path("occupancy_state.json")
MACHINE_FILE = Path("machines_state.json")

SEND_INTERVAL = 30  # seconds for demo
MIN_TEMP = 15
MAX_TEMP = 40


def load_temperature():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f).get("temperature", 25)
        except Exception:
            pass
    return 25


def save_temperature(value):
    with open(STATE_FILE, "w") as f:
        json.dump({"temperature": value}, f, indent=2)


def load_occupancy():
    if OCCUPANCY_FILE.exists():
        try:
            with open(OCCUPANCY_FILE, "r") as f:
                return json.load(f).get("people_count", 20)
        except Exception:
            pass
    return 20


def count_active_machines():
    if MACHINE_FILE.exists():
        try:
            with open(MACHINE_FILE, "r") as f:
                data = json.load(f)
            return sum(1 for m in data.values() if m.get("status") == "in_use")
        except Exception:
            pass
    return 0


def generate_temperature(current_temp, people_count, active_machines):
    # Base effect from gym activity
    target_temp = 22 + (people_count // 15) + active_machines

    # Move slowly toward target
    if current_temp < target_temp:
        current_temp += random.randint(0, 2)
    elif current_temp > target_temp:
        current_temp -= random.randint(0, 2)
    else:
        current_temp += random.randint(-1, 1)

    current_temp = max(MIN_TEMP, min(MAX_TEMP, current_temp))
    return current_temp


def main():
    current_temp = load_temperature()
    print("🚀 Temperature sensor started...")

    while True:
        people_count = load_occupancy()
        active_machines = count_active_machines()

        current_temp = generate_temperature(current_temp, people_count, active_machines)
        save_temperature(current_temp)

        data = {"temperature": current_temp}

        try:
            response = requests.post(FOG_URL, json=data, timeout=5)
            print(f"🌡️ Temperature Sent: {data} | status_code={response.status_code}")
        except Exception as e:
            print("❌ Temperature error:", e)

        time.sleep(SEND_INTERVAL)


if __name__ == "__main__":
    main()