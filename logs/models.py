from django.db import models
from prescriptions.models import Prescription

class MedicationLog(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('TAKEN', 'Pris'),
        ('MISSED', 'Manqué'),
    )
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='logs')
    scheduled_datetime = models.DateTimeField()
    actual_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"{self.prescription.medication_name} - {self.scheduled_datetime.strftime('%Y-%m-%d %H:%M')} [{self.status}]"