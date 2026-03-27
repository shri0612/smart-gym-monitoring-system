from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render
import boto3


alerts = []  # temporary storage (later DB)


@csrf_exempt
def receive_alert(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            print("🚨 Alert received in Django:", data)

            alerts.append(data)

            return JsonResponse({"message": "Alert saved"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=405)


def get_alerts(request):
    return JsonResponse({"alerts": alerts})


def dashboard(request):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('gym_data')

    response = table.scan()
    items = response.get('Items', [])

    # 🔥 Sort + limit (last 20 records)
    items = sorted(items, key=lambda x: x.get('timestamp', ''))[-20:]

    # 🔥 Initialize
    latest_temp = None
    latest_people = None

    equipment_data = []
    temp_data = []
    occupancy_data = []

    # 🔥 Get latest values properly (reverse loop)
    for item in reversed(items):
        if item.get('type') == 'temperature' and latest_temp is None:
            latest_temp = item.get('value')

        elif item.get('type') == 'occupancy' and latest_people is None:
            latest_people = item.get('value')

        if latest_temp is not None and latest_people is not None:
            break

    # 🔥 Separate data for charts
    for item in items:
        if item.get('type') == 'equipment':
            equipment_data.append(item)

        elif item.get('type') == 'temperature':
            temp_data.append(item)

        elif item.get('type') == 'occupancy':
            occupancy_data.append(item)

    # 🔥 Limit chart data (last 10)
    equipment_data = equipment_data[-10:]
    temp_data = temp_data[-10:]
    occupancy_data = occupancy_data[-10:]

    # 🔥 Unique machine count (correct logic)
    machines = set()
    for item in items:
        if item.get('type') == 'equipment':
            machines.add(item.get('key'))

    machine_count = len(machines)

    context = {
        "items": items,
        "latest_temp": latest_temp,
        "latest_people": latest_people,
        "equipment_data": equipment_data,
        "temp_data": temp_data,
        "occupancy_data": occupancy_data,
        "machine_count": machine_count,
    }

    return render(request, "dashboard.html", context)