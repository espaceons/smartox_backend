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
        Regroupe les médicaments par heure de prise tout en conservant le numéro 
        de compartiment IoT spécifié par le médecin sur le médicament.
        """
        # Clé = Heure de prise, Valeur = dict{'compartment_number': int, 'medications': list}
        time_to_compartment = {}

        for item in self.items.all():
            # Filtre les heures renseignées (TimeField ou string)
            times = [t for t in [item.intake_time_1, item.intake_time_2, item.intake_time_3] if t]
            
            for t in times:
                # Formatage HH:MM
                if hasattr(t, 'strftime'):
                    time_str = t.strftime("%H:%M")
                else:
                    time_str = str(t)[:5]

                if time_str not in time_to_compartment:
                    time_to_compartment[time_str] = {
                        # Récupère le compartiment choisi par le médecin pour ce médicament
                        'compartment_number': item.compartment_number,
                        'medications': []
                    }

                # Ajout du médicament sans doublon
                if item not in time_to_compartment[time_str]['medications']:
                    time_to_compartment[time_str]['medications'].append(item)

        # Tri chronologique des heures de prise
        sorted_times = sorted(time_to_compartment.keys())

        compartments = []
        for time_str in sorted_times:
            data = time_to_compartment[time_str]
            compartments.append({
                'compartment_number': data['compartment_number'], # Fixé par le médecin
                'time': time_str,
                'medications': data['medications']
            })

        return compartments


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
    
    intake_time_1 = models.TimeField(null=True, blank=True, verbose_name="Heure de prise 1")
    intake_time_2 = models.TimeField(null=True, blank=True, verbose_name="Heure de prise 2")
    intake_time_3 = models.TimeField(null=True, blank=True, verbose_name="Heure de prise 3")
    
    # Le médecin choisit ce numéro lors de la création/modification de la prescription (ex: 1, 2, 3...)
    compartment_number = models.PositiveIntegerField(default=1, verbose_name="Compartiment IoT")
    item_notes = models.TextField(blank=True, null=True, verbose_name="Consignes spécifiques au médicament")

    def __str__(self):
        return f"{self.medication_name} ({self.dosage}) - Comp. N°{self.compartment_number}"