from flask import Flask, request, jsonify
import time
import requests
import boto3

app = Flask(__name__)

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('gym_data')

# Dedup store
last_alert_time = {}
COOLDOWN = 300  # 5 minutes


# 🔥 COMMON FUNCTION (reuse logic)
def process_alert(sensor_type, key, value, thresholds, extra_data=None):
    current_time = time.time()

    alert_type = None

    if value > thresholds["critical"]:
        alert_type = "CRITICAL"
    elif value > thresholds["warning"]:
        alert_type = "WARNING"

    if alert_type:
        last_time = last_alert_time.get(key, 0)

        if current_time - last_time > COOLDOWN:
            alert_payload = {
                "sensor": sensor_type,
                "id": key,
                "value": value,
                "alert_type": alert_type,
                "timestamp": time.strftime("%H:%M:%S")
            }

            print("🚨 Sending alert:", alert_payload)

            try:
                requests.post("http://localhost:8080/api/alerts/", json=alert_payload)
            except Exception as e:
                print("❌ Django error:", e)

            last_alert_time[key] = current_time
        else:
            print(f"⏳ Skipping duplicate alert for {key}")

    else:
        item = {
            "id": str(time.time()),
            "type": sensor_type,
            "key": key,
            "value": value,
            "timestamp": time.strftime("%H:%M:%S")
        }

        if extra_data:
            item.update(extra_data)

        try:
            table.put_item(Item=item)
            print("💾 Stored:", item)
        except Exception as e:
            print("❌ DynamoDB error:", e)


# 🟢 EQUIPMENT
@app.route('/fog/equipment', methods=['POST'])
def equipment():
    data = request.json
    print("📥 Equipment:", data)

    machine_id = data.get("machine_id")
    duration = data.get("duration")

    process_alert(
        sensor_type="equipment",
        key=machine_id,
        value=duration,
        thresholds={"warning": 30, "critical": 45},
        extra_data={"status": data.get("status")}
    )

    return jsonify({"message": "OK"}), 200


# ❤️ HEART RATE
@app.route('/fog/heartrate', methods=['POST'])
def heartrate():
    data = request.json
    print("📥 Heart Rate:", data)

    user_id = data.get("user_id")
    heart_rate = data.get("heart_rate")

    process_alert(
        sensor_type="heartrate",
        key=user_id,
        value=heart_rate,
        thresholds={"warning": 150, "critical": 170}
    )

    return jsonify({"message": "OK"}), 200


# 🌡️ TEMPERATURE
@app.route('/fog/temperature', methods=['POST'])
def temperature():
    data = request.json
    print("📥 Temperature:", data)

    temp = data.get("temperature")

    # Special condition for low temp
    if temp < 18:
        process_alert(
            sensor_type="temperature",
            key="gym",
            value=temp,
            thresholds={"warning": 18, "critical": 18}
        )
    else:
        process_alert(
            sensor_type="temperature",
            key="gym",
            value=temp,
            thresholds={"warning": 30, "critical": 35}
        )

    return jsonify({"message": "OK"}), 200


# 👥 OCCUPANCY
@app.route('/fog/occupancy', methods=['POST'])
def occupancy():
    data = request.json
    print("📥 Occupancy:", data)

    count = data.get("people_count")

    process_alert(
        sensor_type="occupancy",
        key="gym",
        value=count,
        thresholds={"warning": 45, "critical": 60}
    )

    return jsonify({"message": "OK"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)