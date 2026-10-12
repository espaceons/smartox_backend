from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class ConnectedBox(models.Model):
    STATUS_CHOICES = (
        ('ONLINE', 'En ligne'),
        ('OFFLINE', 'Hors ligne'),
        ('MAINTENANCE', 'En maintenance'),
    )

    uid = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Identifiant unique matériel (ex: ESP32-MAC ou Serial)"
    )
    patient = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='connected_box',
        limit_choices_to={'role': 'PATIENT'}
    )
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OFFLINE')
    last_ping = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Boîte Connectée IoT"
        verbose_name_plural = "Boîtes Connectées IoT"

    def __str__(self):
        patient_name = self.patient.get_full_name() if self.patient else "Non attribuée"
        return f"Boîte {self.uid} - ({patient_name})"


class Compartment(models.Model):
    box = models.ForeignKey(ConnectedBox, on_delete=models.CASCADE, related_name='compartments')
    number = models.PositiveSmallIntegerField(help_text="Numéro du casier (1, 2, 3...)")
    medication_name = models.CharField(max_length=100, blank=True, verbose_name="Nom du médicament")
    dosage = models.CharField(max_length=50, blank=True, verbose_name="Dosage")

    class Meta:
        unique_together = ('box', 'number')

    def __str__(self):
        return f"Boîte {self.box.uid} - Compartiment {self.number}"


class DispenseLog(models.Model):
    STATUS_CHOICES = (
        ('TAKEN', 'Pris'),
        ('MISSED', 'Manqué'),
        ('PENDING', 'En attente'),
    )

    box = models.ForeignKey(ConnectedBox, on_delete=models.CASCADE, related_name='logs')
    compartment = models.ForeignKey(Compartment, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField(verbose_name="Heure prévue")
    dispensed_at = models.DateTimeField(null=True, blank=True, verbose_name="Heure effective")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    class Meta:
        ordering = ['-scheduled_time']

    def __str__(self):
        return f"Log {self.box.uid} - {self.scheduled_time.strftime('%d/%m %H:%M')} [{self.status}]"