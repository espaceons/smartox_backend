from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

from accounts.models import DoctorPatientLink
from .models import Prescription
from .forms import PrescriptionForm, PrescriptionItemFormSet

User = get_user_model()

@login_required
def create_prescription(request, patient_id):
    """Permet au médecin de créer une ordonnance avec plusieurs médicaments."""
    
    # Vérification du rôle
    is_doctor = getattr(request.user, "is_doctor", False)
    if callable(is_doctor):
        is_doctor = is_doctor()

    if not is_doctor and getattr(request.user, "role", None) != User.Role.DOCTOR:
        raise PermissionDenied("Seul un médecin peut rédiger une prescription.")

    patient = get_object_or_404(User, id=patient_id, role=User.Role.PATIENT)

    # Vérification de l'association Médecin-Patient
    is_linked = DoctorPatientLink.objects.filter(
        doctor=request.user,
        patient=patient,
        status=DoctorPatientLink.Status.ACCEPTED
    ).exists()

    if not is_linked:
        messages.error(request, "Vous n'êtes pas autorisé à prescrire à ce patient.")
        return redirect('dashboards:doctor-dashboard')

    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        formset = PrescriptionItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            prescription = form.save(commit=False)
            prescription.doctor = request.user
            prescription.patient = patient
            prescription.save()

            # Enregistrement des médicaments liés
            items = formset.save(commit=False)
            for item in items:
                item.prescription = prescription
                item.save()
            formset.save_m2m()

            patient_name = patient.get_full_name() or patient.username
            messages.success(request, f"Ordonnance enregistrée avec succès pour {patient_name}.")
            return redirect('dashboards:doctor-dashboard')
    else:
        form = PrescriptionForm()
        formset = PrescriptionItemFormSet()

    return render(request, 'prescriptions/create_prescription.html', {
        'form': form,
        'formset': formset,
        'patient': patient
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Prescription
from .forms import PrescriptionForm, PrescriptionItemFormSet

User = get_user_model()

# listes des prescriptions
@login_required
def list_patient_prescriptions(request, patient_id):
    """
    Affiche la liste des ordonnances et médicaments d'un patient spécifique.
    """
    patient = get_object_or_404(User, id=patient_id)
    
    # 1. Vérification du rôle du médecin
    is_doctor = getattr(request.user, 'is_doctor', False)
    if callable(is_doctor):
        is_doctor = is_doctor()
    
    if not is_doctor and getattr(request.user, 'role', None) == User.Role.DOCTOR:
        is_doctor = True

    # 2. Contrôle d'accès (Le patient lui-même, un médecin ou le staff)
    if request.user != patient and not is_doctor and not request.user.is_staff:
        raise PermissionDenied("Accès non autorisé.")

    # 3. Sécurité supplémentaire : Si c'est un médecin, vérifier qu'il est lié à ce patient
    if is_doctor and request.user != patient and not request.user.is_staff:
        is_linked = DoctorPatientLink.objects.filter(
            doctor=request.user,
            patient=patient,
            status=DoctorPatientLink.Status.ACCEPTED
        ).exists()
        
        if not is_linked:
            raise PermissionDenied("Vous n'êtes pas autorisé à consulter les ordonnances de ce patient.")

    # 4. Récupération des ordonnances avec leurs médicaments préchargés
    prescriptions = Prescription.objects.filter(patient=patient).prefetch_related('items').order_by('-created_at')
    
    return render(request, 'prescriptions/prescription_list.html', {
        'patient': patient,
        'prescriptions': prescriptions
    })


# --- VUE DE MODIFICATION ---
@login_required
def update_prescription(request, pk):
    """
    Permet au médecin de modifier une prescription/ordonnance existante et ses médicaments.
    """
    is_doctor = getattr(request.user, 'is_doctor', False)
    if callable(is_doctor):
        is_doctor = is_doctor()

    if not is_doctor:
        raise PermissionDenied("Seul un médecin peut modifier une prescription.")

    # Récupération de la prescription appartenant au médecin connecté
    prescription = get_object_or_404(Prescription, pk=pk, doctor=request.user)
    patient = prescription.patient

    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription)
        formset = PrescriptionItemFormSet(request.POST, instance=prescription)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            patient_name = patient.get_full_name() or patient.username
            messages.success(request, f"L'ordonnance #{prescription.id} de {patient_name} a été mise à jour avec succès.")
            return redirect('prescriptions:patient-prescriptions', patient_id=patient.id)
    else:
        form = PrescriptionForm(instance=prescription)
        formset = PrescriptionItemFormSet(instance=prescription)

    return render(request, 'prescriptions/update_prescription.html', {
        'form': form,
        'formset': formset,
        'prescription': prescription,
        'patient': patient,
    })


# --- VUE DE SUPPRESSION ---
@login_required
def delete_prescription(request, pk):
    """
    Permet au médecin de supprimer/annuler une prescription complète.
    """
    is_doctor = getattr(request.user, 'is_doctor', False)
    if callable(is_doctor):
        is_doctor = is_doctor()

    if not is_doctor:
        raise PermissionDenied("Seul un médecin peut supprimer une prescription.")

    prescription = get_object_or_404(Prescription, pk=pk, doctor=request.user)
    patient_id = prescription.patient.id
    prescription_id = prescription.id

    if request.method == 'POST':
        prescription.delete()
        messages.success(request, f"L'ordonnance #{prescription_id} a été supprimée.")
        return redirect('prescriptions:patient-prescriptions', patient_id=patient_id)

    return render(request, 'prescriptions/delete_confirm.html', {
        'prescription': prescription,
        'patient': prescription.patient
    })