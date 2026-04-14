from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render
import boto3

alerts = []


# ============================
# 🚨 RECEIVE ALERT
# ============================
@csrf_exempt
def receive_alert(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            print("🚨 Alert received in Django:", data)

            alerts.append(data)

            # keep only latest 50 alerts
            if len(alerts) > 50:
                del alerts[:-50]

            return JsonResponse({"message": "Alert saved"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=405)


# ============================
# 📡 GET ALERTS
# ============================
def get_alerts(request):
    latest_alerts = sorted(alerts, key=lambda x: x.get('timestamp', ''), reverse=True)[:20]
    return JsonResponse({"alerts": latest_alerts})


# ============================
# 📊 GET LATEST DATA API
# Returns enough recent records so frontend can find latest 10 per type
# ============================
def get_latest_data(request):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
        table = dynamodb.Table('gym_data')

        response = table.scan()
        items = response.get('Items', [])

        items = sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)

        # return more records so charts can consistently get latest 10 per type
        latest = items[:100]

        return JsonResponse(latest, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ============================
# 📊 DASHBOARD
# ============================
def dashboard(request):
    try:
        print("🔌 Connecting to DynamoDB...")

        dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
        table = dynamodb.Table('gym_data')

        response = table.scan()
        items = response.get('Items', [])

        items = sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)

        print(f"✅ DynamoDB items fetched: {len(items)}")

    except Exception as e:
        print("❌ DynamoDB error:", e)
        items = []

    latest_temp = None
    latest_people = None

    for item in items:
        if item.get('type') == 'temperature' and latest_temp is None:
            latest_temp = item.get('value')

        elif item.get('type') == 'occupancy' and latest_people is None:
            latest_people = item.get('value')

        if latest_temp is not None and latest_people is not None:
            break

    # latest 10 per type
    equipment_data = [item for item in items if item.get('type') == 'equipment'][:10]
    temp_data = [item for item in items if item.get('type') == 'temperature'][:10]
    occupancy_data = [item for item in items if item.get('type') == 'occupancy'][:10]

    # machine count based on latest equipment status per machine
    latest_status = {}
    for item in items:
        if item.get('type') == 'equipment':
            key = item.get('key')
            if key not in latest_status:
                latest_status[key] = item.get('value')

    machine_count = sum(
        1 for v in latest_status.values()
        if v is not None and str(v).isdigit() and int(v) > 0
    )

    latest_alerts = sorted(alerts, key=lambda x: x.get('timestamp', ''), reverse=True)[:20]

    print("DEBUG machine_status:", latest_status)

    context = {
        "items": items[:20],
        "latest_temp": latest_temp,
        "latest_people": latest_people,
        "equipment_data": equipment_data,
        "temp_data": temp_data,
        "occupancy_data": occupancy_data,
        "machine_count": machine_count,
        "latest_alerts": latest_alerts,
    }

    return render(request, "dashboard.html", context)