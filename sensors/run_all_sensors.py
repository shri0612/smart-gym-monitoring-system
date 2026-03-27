import subprocess

print("🚀 Starting all sensors...")

subprocess.Popen(["python", "equipment_sensor.py"])
subprocess.Popen(["python", "heartrate_sensor.py"])
subprocess.Popen(["python", "temperature_sensor.py"])
subprocess.Popen(["python", "occupancy_sensor.py"])

print("✅ All sensors running...")