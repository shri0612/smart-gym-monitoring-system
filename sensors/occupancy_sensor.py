import json
import random
import time
from pathlib import Path

import requests

FOG_URL = "http://localhost:5000/fog/occupancy"
STATE_FILE = Path("occupancy_state.json")
MACHINE_FILE = Path("machines_state.json")

SEND_INTERVAL = 30  # seconds for demo
MIN_PEOPLE = 8
MAX_PEOPLE = 70


def load_occupancy():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f).get("people_count", 20)
        except Exception:
            pass
    return 20


def save_occupancy(value):
    with open(STATE_FILE, "w") as f:
        json.dump({"people_count": value}, f, indent=2)


def count_active_machines():
    if MACHINE_FILE.exists():
        try:
            with open(MACHINE_FILE, "r") as f:
                data = json.load(f)
            return sum(1 for m in data.values() if m.get("status") == "in_use")
        except Exception:
            pass
    return 0


def generate_occupancy(current_people, active_machines):
    # Slow change, not random big jumps
    change = random.randint(-3, 3)
    next_people = current_people + change

    # Keep occupancy logically above active machines
    minimum_based_on_machines = active_machines + random.randint(5, 12)
    next_people = max(next_people, minimum_based_on_machines)

    next_people = max(MIN_PEOPLE, min(MAX_PEOPLE, next_people))
    return next_people


def main():
    current_people = load_occupancy()
    print("🚀 Occupancy sensor started...")

    while True:
        active_machines = count_active_machines()
        current_people = generate_occupancy(current_people, active_machines)
        save_occupancy(current_people)

        data = {"people_count": current_people}

        try:
            response = requests.post(FOG_URL, json=data, timeout=5)
            print(f"👥 Occupancy Sent: {data} | status_code={response.status_code}")
        except Exception as e:
            print("❌ Occupancy error:", e)

        time.sleep(SEND_INTERVAL)


if __name__ == "__main__":
    main()