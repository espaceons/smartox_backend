import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    class Role(models.TextChoices):
        DOCTOR = 'DOCTOR', 'Médecin'
        RELATIVE = 'RELATIVE', 'Proche / Famille'
        PATIENT = 'PATIENT', 'Patient'

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.PATIENT,
        verbose_name="Rôle Utilisateur"
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Numéro de Téléphone"
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    # Helpers pour tester facilement le rôle dans Python / Django Templates
    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_relative(self):
        return self.role == self.Role.RELATIVE

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    def __str__(self):
        full_name = self.get_full_name()
        display_name = full_name if full_name else self.username
        return f"{display_name} ({self.get_role_display()})"


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        limit_choices_to={'role': 'DOCTOR'}
    )
    doctor_code = models.CharField(
        max_length=10, 
        unique=True, 
        editable=False,
        verbose_name="Code Médecin Unique"
    )
    specialty = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Spécialité"
    )

    class Meta:
        verbose_name = "Profil Médecin"
        verbose_name_plural = "Profils Médecins"

    def save(self, *args, **kwargs):
        if not self.doctor_code:
            # Génère un code unique du type DOC-A1B2
            self.doctor_code = f"DOC-{uuid.uuid4().hex[:4].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username} ({self.doctor_code})"


class PatientProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='patient_profile',
        limit_choices_to={'role': 'PATIENT'}
    )
    doctor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='doctor_patients',  # <-- MODIFIÉ : évite le conflit avec PatientCaregiver
        limit_choices_to={'role': 'DOCTOR'},
        verbose_name="Médecin Traitant Actif"
    )
    relative = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='relative_patients',  # <-- OPTIONNEL/CONSEILLÉ : plus clair que monitored_patients
        limit_choices_to={'role': 'RELATIVE'},
        verbose_name="Proche / Famille"
    )
    date_of_birth = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="Date de naissance"
    )

    class Meta:
        verbose_name = "Profil Patient"
        verbose_name_plural = "Profils Patients"

    def __str__(self):
        return f"Profil Patient: {self.user.get_full_name() or self.user.username}"


class DoctorPatientLink(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        ACCEPTED = 'ACCEPTED', 'Accepté'
        REJECTED = 'REJECTED', 'Refusé'

    class Initiator(models.TextChoices):
        PATIENT = 'PATIENT', 'Patient'
        DOCTOR = 'DOCTOR', 'Médecin'

    doctor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='doctor_patient_links',
        limit_choices_to={'role': 'DOCTOR'},
        verbose_name="Médecin"
    )
    patient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='patient_doctor_links',
        limit_choices_to={'role': 'PATIENT'},
        verbose_name="Patient"
    )
    initiated_by = models.CharField(
        max_length=10, 
        choices=Initiator.choices,
        verbose_name="Initié par"
    )
    status = models.CharField(
        max_length=10, 
        choices=Status.choices, 
        default=Status.PENDING,
        verbose_name="Statut de la demande"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        unique_together = ('doctor', 'patient')
        verbose_name = "Demande d'Association Médecin-Patient"
        verbose_name_plural = "Demandes d'Association Médecin-Patient"

    def __str__(self):
        return f"Lien: {self.patient.username} <-> Dr. {self.doctor.username} [{self.get_status_display()}]"



# Signal pour mettre à jour PatientProfile.doctor dès qu'une demande est ACCEPTED
@receiver(post_save, sender=DoctorPatientLink)
def update_patient_active_doctor(sender, instance, **kwargs):
    if instance.status == DoctorPatientLink.Status.ACCEPTED:
        patient_profile = getattr(instance.patient, 'patient_profile', None)
        if patient_profile:
            patient_profile.doctor = instance.doctor
            patient_profile.save()


# Signals pour créer / sauvegarder automatiquement les profils selon le rôle
@receiver(post_save, sender=User)
def create_or_update_user_profiles(sender, instance, created, **kwargs):
    if instance.role == User.Role.PATIENT:
        if created:
            PatientProfile.objects.create(user=instance)
        elif hasattr(instance, 'patient_profile'):
            instance.patient_profile.save()
        else:
            PatientProfile.objects.create(user=instance)

    elif instance.role == User.Role.DOCTOR:
        if created:
            DoctorProfile.objects.create(user=instance)
        elif hasattr(instance, 'doctor_profile'):
            instance.doctor_profile.save()
        else:
            DoctorProfile.objects.create(user=instance)