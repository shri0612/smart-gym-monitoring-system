from flask import Flask, request, jsonify
import time
import requests
import boto3
import json
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

# 🟢 SQS SETUP
sqs = boto3.client('sqs', region_name='eu-north-1')
QUEUE_URL = "https://sqs.eu-north-1.amazonaws.com/605629425467/gym-sensor-queue"

# 🔁 Dedup store
last_alert_time = {}
COOLDOWN = 300  # 5 minutes

# 🌐 Django alert endpoint
DJANGO_ALERT_URL = "http://127.0.0.1/receive-alert/"

# 🇮🇪 Ireland timezone
IRELAND_TZ = ZoneInfo("Europe/Dublin")


# ============================
# 🕒 COMMON TIME FUNCTION
# ============================
def get_current_timestamp():
    return datetime.now(IRELAND_TZ).isoformat()


# ============================
# 📤 SEND TO SQS
# ============================
def send_to_sqs(sensor_type, key, value, extra_data=None):
    message = {
        "type": sensor_type,
        "key": key,
        "value": value,
        "timestamp": get_current_timestamp()
    }

    if extra_data:
        message.update(extra_data)

    try:
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message)
        )
        print("📤 Sent to SQS:", message)
    except Exception as e:
        print("❌ SQS error:", e)


# ============================
# 🚨 SEND ALERT TO DJANGO
# ============================
def send_alert(sensor_type, key, value, alert_type, extra_data=None):
    current_time = time.time()
    dedup_key = f"{sensor_type}:{key}:{alert_type}"

    last_time = last_alert_time.get(dedup_key, 0)

    if current_time - last_time > COOLDOWN:
        alert_payload = {
            "sensor": sensor_type,
            "id": key,
            "value": value,
            "alert_type": alert_type,
            "timestamp": get_current_timestamp()
        }

        if extra_data:
            alert_payload.update(extra_data)

        print("🚨 ALERT:", alert_payload)

        try:
            response = requests.post(DJANGO_ALERT_URL, json=alert_payload)
            print("📡 Sent to Django:", response.status_code)
        except Exception as e:
            print("❌ Django error:", e)

        last_alert_time[dedup_key] = current_time
    else:
        print(f"⏳ Skipping duplicate alert for {dedup_key}")


# ============================
# 🔥 HIGH VALUE ALERT LOGIC
# ============================
def process_high_alert(sensor_type, key, value, warning, critical, extra_data=None):
    # Always store every reading in cloud
    send_to_sqs(sensor_type, key, value, extra_data)

    # Fog decides local alert
    if value > critical:
        send_alert(sensor_type, key, value, "CRITICAL", extra_data)
    elif value > warning:
        send_alert(sensor_type, key, value, "WARNING", extra_data)


# ============================
# ❄️ LOW VALUE ALERT LOGIC
# ============================
def process_low_alert(sensor_type, key, value, warning, critical, extra_data=None):
    # Always store every reading in cloud
    send_to_sqs(sensor_type, key, value, extra_data)

    # Fog decides local alert
    if value < critical:
        send_alert(sensor_type, key, value, "CRITICAL", extra_data)
    elif value < warning:
        send_alert(sensor_type, key, value, "WARNING", extra_data)


# ============================
# 🟢 EQUIPMENT
# ============================
@app.route('/fog/equipment', methods=['POST'])
def equipment():
    data = request.json
    print("📥 Equipment:", data)

    duration = data.get("duration", 0)
    machine_id = data.get("machine_id")
    status = data.get("status")

    process_high_alert(
        sensor_type="equipment",
        key=machine_id,
        value=duration,
        warning=30,
        critical=45,
        extra_data={"status": status}
    )

    return jsonify({"message": "OK"}), 200


# ============================
# ❤️ HEART RATE
# ============================
@app.route('/fog/heartrate', methods=['POST'])
def heartrate():
    data = request.json
    print("📥 Heart Rate:", data)

    heart_rate = data.get("heart_rate", 0)
    user_id = data.get("user_id")

    process_high_alert(
        sensor_type="heartrate",
        key=user_id,
        value=heart_rate,
        warning=150,
        critical=170
    )

    return jsonify({"message": "OK"}), 200


# ============================
# 🌡️ TEMPERATURE
# ============================
@app.route('/fog/temperature', methods=['POST'])
def temperature():
    data = request.json
    print("📥 Temperature:", data)

    temp = data.get("temperature", 0)

    # Always store in cloud first
    send_to_sqs("temperature", "gym", temp)

    # Low temperature alerts
    if temp < 16:
        send_alert("temperature", "gym", temp, "CRITICAL")
    elif temp < 18:
        send_alert("temperature", "gym", temp, "WARNING")

    # High temperature alerts
    elif temp > 35:
        send_alert("temperature", "gym", temp, "CRITICAL")
    elif temp > 30:
        send_alert("temperature", "gym", temp, "WARNING")

    return jsonify({"message": "OK"}), 200


# ============================
# 👥 OCCUPANCY
# ============================
@app.route('/fog/occupancy', methods=['POST'])
def occupancy():
    data = request.json
    print("📥 Occupancy:", data)

    people_count = data.get("people_count", 0)

    process_high_alert(
        sensor_type="occupancy",
        key="gym",
        value=people_count,
        warning=45,
        critical=60
    )

    return jsonify({"message": "OK"}), 200


# ============================
# 🚀 RUN APP
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)