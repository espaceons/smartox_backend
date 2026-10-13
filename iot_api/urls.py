from django.urls import path
from . import views

app_name = 'iot_api'

urlpatterns = [
    path('schedule/<int:patient_id>/', views.get_arduino_schedule, name='arduino-schedule'),
    path('log/', views.record_dose_taken, name='record-dose'),
]