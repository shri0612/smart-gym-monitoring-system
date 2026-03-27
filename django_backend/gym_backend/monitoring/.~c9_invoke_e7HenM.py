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

    # Sort by timestamp
    items = sorted(items, key=lambda x: x.get('timestamp', ''))

    # Latest values
    latest_temp = None
    latest_people = None

    equipment_data = []
    temp_data = []
    occupancy_data = []

    for item in items[-20:]:  # last 20 records
        if item['type'] == 'temperature':
            latest_temp = item['value']
            temp_data.append(item)

        elif item['type'] == 'occupancy':
            latest_people = item['value']
            occupancy_data.append(item)

        elif item['type'] == 'equipment':
            equipment_data.append(item)

    context = {
        "items": items[-20:],
        "latest_temp": latest_temp,
        "latest_people": latest_people,
        "equipment_data": equipment_data,
        "temp_data": temp_data,
        "occupancy_data": occupancy_data
    }

    return render(request, "dashboard.html", context)