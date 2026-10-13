from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class DoseLog(models.Model):
    STATUS_CHOICES = [
        ('TAKEN', 'Pris'),
        ('MISSED', 'Manqué / Oublié'),
        ('DELAYED', 'Pris en retard'),
    ]

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dose_logs',
        limit_choices_to={'role': 'PATIENT'}
    )
    compartment_number = models.PositiveIntegerField(verbose_name="Compartiment IoT")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='TAKEN',
        verbose_name="Statut de la prise"
    )
    taken_at = models.DateTimeField(default=timezone.now, verbose_name="Horodatage de la prise")

    class Meta:
        ordering = ['-taken_at']
        verbose_name = "Journal de prise"
        verbose_name_plural = "Journaux de prises"

    def __str__(self):
        patient_name = self.patient.get_full_name() or self.patient.username
        return f"{patient_name} - Compartiment {self.compartment_number} ({self.get_status_display()}) le {self.taken_at.strftime('%d/%m/%Y à %H:%M')}"