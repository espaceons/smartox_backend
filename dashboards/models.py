from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# permettre à un patient d'associer un proche aidant à son compte

class PatientCaregiver(models.Model):
    patient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='caregivers'
    )
    caregiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='caregiver_patients'
    )
    relationship = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)