from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Prescription(models.Model):
    doctor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='prescriptions_given',
        limit_choices_to={'role': 'DOCTOR'},
        null=True,
        blank=True
    )
    patient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='prescriptions_received',
        limit_choices_to={'role': 'PATIENT'}
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Instructions / Remarques globales")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"

    def __str__(self):
        patient_name = self.patient.get_full_name() or self.patient.username
        return f"Ordonnance #{self.id} - Patient: {patient_name}"

    def get_compartments_by_time(self):
        """
        Organise et regroupe tous les médicaments par Compartiment IoT et Heure de prise.
        """
        # Clé = (numéro_compartiment, heure_formatée)
        compartments_map = {}

        for item in self.items.all():
            # Association directe (Heure, Compartiment)
            schedule_pairs = [
                (item.intake_time_1, item.compartment_1),
                (item.intake_time_2, item.compartment_2),
                (item.intake_time_3, item.compartment_3),
            ]

            for time_val, comp_num in schedule_pairs:
                if time_val and comp_num:
                    time_str = time_val.strftime("%H:%M") if hasattr(time_val, 'strftime') else str(time_val)[:5]
                    
                    key = (comp_num, time_str)
                    if key not in compartments_map:
                        compartments_map[key] = []
                    
                    compartments_map[key].append({
                        'medication_name': item.medication_name,
                        'dosage': item.dosage,
                        'item_notes': item.item_notes,
                    })

        # Tri par Numéro de Compartiment puis par Heure
        sorted_keys = sorted(compartments_map.keys(), key=lambda x: (x[0], x[1]))

        result = []
        for comp_num, time_str in sorted_keys:
            result.append({
                'compartment_number': comp_num,
                'time': time_str,
                'medications': compartments_map[(comp_num, time_str)]
            })

        return result


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(
        Prescription, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    medication_name = models.CharField(max_length=150, verbose_name="Nom du médicament")
    dosage = models.CharField(max_length=100, null=True, blank=True, verbose_name="Dosage / Posologie")
    
    start_date = models.DateField(null=True, blank=True, verbose_name="Date de début")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    
    # Prise 1 : Heure + Compartiment
    intake_time_1 = models.TimeField(null=True, blank=True, verbose_name="Heure Prise 1")
    compartment_1 = models.PositiveIntegerField(default=1, null=True, blank=True, verbose_name="Compartiment Prise 1")
    
    # Prise 2 : Heure + Compartiment
    intake_time_2 = models.TimeField(null=True, blank=True, verbose_name="Heure Prise 2")
    compartment_2 = models.PositiveIntegerField(default=2, null=True, blank=True, verbose_name="Compartiment Prise 2")
    
    # Prise 3 : Heure + Compartiment
    intake_time_3 = models.TimeField(null=True, blank=True, verbose_name="Heure Prise 3")
    compartment_3 = models.PositiveIntegerField(default=3, null=True, blank=True, verbose_name="Compartiment Prise 3")
    
    item_notes = models.TextField(blank=True, null=True, verbose_name="Consignes spécifiques")

    def __str__(self):
        return f"{self.medication_name} ({self.dosage})"