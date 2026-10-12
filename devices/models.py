import uuid
from django.db import models
from accounts.models import PatientProfile

class SmartBox(models.Model):
    device_id = models.CharField(max_length=100, unique=True)
    patient = models.OneToOneField(PatientProfile, on_delete=models.CASCADE, related_name='smart_box')
    api_key = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    is_active = models.BooleanField(default=True)
    last_ping = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Boîte {self.device_id} - {self.patient}"