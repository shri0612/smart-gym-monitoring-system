import json
import random
import time
from pathlib import Path

import requests

FOG_URL = "http://localhost:5000/fog/equipment"
STATE_FILE = Path("machines_state.json")

MACHINES = ["treadmill_1", "treadmill_2", "treadmill_3"]
USERS = ["user_1", "user_2", "user_3", "user_4", "user_5"]

SEND_INTERVAL = 10  # seconds


def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        machine: {
            "status": "idle",
            "duration": 0,
            "user_id": None
        }
        for machine in MACHINES
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def update_machine_state(state):
    machine_id = random.choice(MACHINES)
    machine = state[machine_id]

    # If machine is idle, sometimes start using it
    if machine["status"] == "idle":
        if random.random() < 0.6:
            available_users = USERS[:]
            busy_users = {
                m["user_id"] for m in state.values()
                if m["user_id"] is not None
            }
            free_users = [u for u in available_users if u not in busy_users]

            if free_users:
                machine["status"] = "in_use"
                machine["duration"] = random.randint(5, 15)
                machine["user_id"] = random.choice(free_users)

    else:
        # If machine is in use, either continue or stop
        if random.random() < 0.75:
            machine["duration"] += random.randint(3, 8)
        else:
            machine["status"] = "idle"
            machine["duration"] = 0
            machine["user_id"] = None

    return machine_id, state[machine_id]


def main():
    state = load_state()
    print("🚀 Equipment sensor started...")

    while True:
        machine_id, machine = update_machine_state(state)
        save_state(state)

        if machine["status"] == "in_use":
            payload = {
                "machine_id": machine_id,
                "status": machine["status"],
                "duration": machine["duration"]
            }

            try:
                response = requests.post(FOG_URL, json=payload, timeout=5)
                print(f"✅ Equipment Sent: {payload} | status_code={response.status_code}")
            except Exception as e:
                print("❌ Equipment error:", e)
        else:
            print(f"ℹ️ {machine_id} is idle, not sending usage data")

        time.sleep(SEND_INTERVAL)


if __name__ == "__main__":
    main()