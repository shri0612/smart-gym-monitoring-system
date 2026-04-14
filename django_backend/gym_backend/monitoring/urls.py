from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('receive-alert/', views.receive_alert, name='receive_alert'),
    path('alerts/view/', views.get_alerts, name='get_alerts'),
    path('api/data/', views.get_latest_data, name='get_latest_data'),
]