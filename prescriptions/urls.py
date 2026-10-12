from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    path('create/<int:patient_id>/', views.create_prescription, name='create-prescription'),
    path('patient/<int:patient_id>/', views.list_patient_prescriptions, name='patient-prescriptions'),
    path('update/<int:pk>/', views.update_prescription, name='update-prescription'),
    path('delete/<int:pk>/', views.delete_prescription, name='delete-prescription'),
]