from django.urls import path
from .views import receive_alert, get_alerts
from .views import dashboard

urlpatterns = [
    path('alerts/', receive_alert),
    path('alerts/view/', get_alerts),
     path('dashboard/', dashboard),
]