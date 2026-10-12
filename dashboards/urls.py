from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    # Tableaux de bord
    path('', views.main_dashboard, name='main-dashboard'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete-user'),
    path('patient/', views.patient_dashboard, name='patient-dashboard'),
    path('doctor/', views.doctor_dashboard, name='doctor-dashboard'),
    path('relative/', views.relative_dashboard, name='relative-dashboard'),
    
    # Liaisons Médecin <-> Patient
    path('request-doctor/', views.request_doctor_link, name='request-doctor-link'),
    path('request-patient/', views.request_patient_link, name='request-patient-link'),
    path('respond-link/<int:link_id>/<str:action>/', views.respond_link_request, name='respond-link'),
    path('remove-patient/<int:link_id>/', views.remove_patient_link, name='remove-patient-link'),
    
    # Liaisons Proche <-> Patient
    path('request-patient-relative/', views.request_patient_relative_link, name='request-patient-relative-link'),
    path('patient/proches/ajouter/', views.add_caregiver_view, name='add_caregiver'),
    path('patient/link-relative/', views.request_relative_patient_link, name='request-relative-patient-link'),
    
    # Route de suppression / dissociation Proche <-> Patient
    path('remove-caregiver/<int:link_id>/', views.remove_caregiver_link, name='remove-caregiver-link'),
]