from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.db.models import Count, Q

from accounts.models import DoctorProfile, PatientProfile, DoctorPatientLink
from dashboards.forms import (
    LinkDoctorForm, 
    LinkPatientForm, 
    LinkPatientToRelativeForm, 
    LinkRelativeToPatientForm
)
from prescriptions.models import Prescription
from logs.models import MedicationLog
from .forms import AddCaregiverForm
from .models import PatientCaregiver

User = get_user_model()


@login_required
def main_dashboard(request):
    """
    Tableau de bord principal / redirection administrative.
    """
    user = request.user
    
    if user.is_staff or user.is_superuser:
        patients = User.objects.filter(role=User.Role.PATIENT)
        relatives_count = User.objects.filter(role=User.Role.RELATIVE).count()
        doctors_count = User.objects.filter(role=User.Role.DOCTOR).count()
        
        context = {
            'patients': patients,
            'patients_count': patients.count(),
            'relatives_count': relatives_count,
            'doctors_count': doctors_count,
            'devices_count': patients.count(),
        }
        return render(request, 'dashboards/main_dashboard.html', context)
    
    if user.is_doctor:
        return redirect('dashboards:doctor-dashboard')
    elif user.is_relative:
        return redirect('dashboards:relative-dashboard')
    
    return redirect('dashboards:patient-dashboard')


@login_required
def doctor_dashboard(request):
    """Dashboard du Médecin : Gestion des invitations/demandes, suivi des patients et ordonnances."""
    is_doctor = getattr(request.user, "is_doctor", False)
    if callable(is_doctor):
        is_doctor = is_doctor()

    if not is_doctor:
        raise PermissionDenied("Accès réservé aux médecins.")

    doctor_profile, _ = DoctorProfile.objects.get_or_create(user=request.user)

    pending_requests = DoctorPatientLink.objects.filter(
        doctor=request.user,
        status=DoctorPatientLink.Status.PENDING,
        initiated_by=DoctorPatientLink.Initiator.PATIENT,
    ).select_related("patient")

    active_links = DoctorPatientLink.objects.filter(
        doctor=request.user, status=DoctorPatientLink.Status.ACCEPTED
    ).select_related("patient", "patient__patient_profile")

    patient_data = []
    for link in active_links:
        patient_user = link.patient
        patient_profile = getattr(patient_user, "patient_profile", None)

        prescriptions = (
            Prescription.objects.filter(patient=patient_user, doctor=request.user)
            .prefetch_related("items")
            .order_by("-created_at")
        )

        total_logs = MedicationLog.objects.filter(
            prescription__patient=patient_user
        ).count()
        taken_logs = MedicationLog.objects.filter(
            prescription__patient=patient_user, status="TAKEN"
        ).count()

        adherence_rate = (
            round((taken_logs / total_logs * 100), 1) if total_logs > 0 else 100.0
        )

        patient_data.append({
            "link": link,
            "patient_user": patient_user,
            "patient_profile": patient_profile,
            "adherence_rate": adherence_rate,
            "total_prescriptions": prescriptions.count(),
            "prescriptions": prescriptions,
        })

    context = {
        "doctor_profile": doctor_profile,
        "pending_requests": pending_requests,
        "patient_data": patient_data,
        "link_form": LinkPatientForm(),
    }
    return render(request, "dashboards/doctor_dashboard.html", context)


@login_required
def patient_dashboard(request):
    """
    Dashboard du Patient : Prises de la journée, médecin traitant, proches et demandes de raccordement.
    """
    if not request.user.is_patient and not request.user.is_staff:
        messages.warning(request, "Accès réservé aux patients.")
        return redirect('dashboards:main-dashboard')

    patient_user = request.user
    patient_profile, _ = PatientProfile.objects.get_or_create(user=patient_user)
    today = timezone.now().date()

    # Liens Médecins
    doctor_links = DoctorPatientLink.objects.filter(patient=patient_user).select_related('doctor')

    # Liens Proches Aidants associés à ce patient
    relatives_links = PatientCaregiver.objects.filter(patient=patient_user).select_related('caregiver')

    # Logs de prise de médicaments du jour
    today_logs = MedicationLog.objects.filter(
        prescription__patient=patient_user,
        scheduled_datetime__date=today
    ).select_related('prescription').order_by('scheduled_datetime')

    taken_doses_count = today_logs.filter(status='TAKEN').count()
    total_doses_count = today_logs.count()

    next_log = today_logs.filter(
        status='PENDING',
        scheduled_datetime__gte=timezone.now()
    ).first()

    context = {
        'patient_profile': patient_profile,
        'doctor_links': doctor_links,
        'relatives_links': relatives_links,
        'link_form': LinkDoctorForm(),
        'link_relative_form': LinkRelativeToPatientForm(),
        'today_logs': today_logs,
        'taken_doses_count': taken_doses_count,
        'total_doses_count': total_doses_count,
        'next_log': next_log,
        'battery_level': 88,
        'box_status': 'ONLINE',
    }
    return render(request, 'dashboards/patient_dashboard.html', context)


@login_required
def relative_dashboard(request):
    """
    Dashboard du Proche : Suivi du patient et consultation de son médecin traitant.
    """
    is_relative = getattr(request.user, 'is_relative', False)
    if callable(is_relative):
        is_relative = is_relative()

    if not is_relative and getattr(request.user, 'role', None) != 'RELATIVE':
        raise PermissionDenied("Accès réservé aux proches autorisés.")

    caregiver_links = PatientCaregiver.objects.filter(
        caregiver=request.user
    ).select_related('patient')

    patients = []
    for link in caregiver_links:
        patient_user = link.patient
        profile, _ = PatientProfile.objects.get_or_create(user=patient_user)
        patients.append(profile)

    selected_patient_id = request.GET.get('patient_id')
    current_patient = None

    if selected_patient_id:
        current_patient = next(
            (p for p in patients if str(p.id) == selected_patient_id or str(p.user.id) == selected_patient_id), 
            None
        )

    if not current_patient and patients:
        current_patient = patients[0]

    today_logs = []
    prescriptions = []
    total_doses_count = 0
    taken_doses_count = 0
    missed_doses_count = 0
    adherence_rate = 100.0
    next_log = None
    patient_doctor = None
    today = timezone.now().date()

    if current_patient and current_patient.user:
        patient_user = current_patient.user
        patient_doctor = getattr(current_patient, 'doctor', None)

        today_logs = MedicationLog.objects.filter(
            prescription__patient=patient_user,
            scheduled_datetime__date=today
        ).select_related('prescription').order_by('scheduled_datetime')

        total_doses_count = today_logs.count()
        taken_doses_count = today_logs.filter(status='TAKEN').count()
        missed_doses_count = today_logs.filter(status='MISSED').count()

        all_logs = MedicationLog.objects.filter(prescription__patient=patient_user)
        total_all = all_logs.count()
        taken_all = all_logs.filter(status='TAKEN').count()
        if total_all > 0:
            adherence_rate = round((taken_all / total_all) * 100, 1)

        next_log = today_logs.filter(
            status='PENDING',
            scheduled_datetime__gte=timezone.now()
        ).first()

        prescriptions = Prescription.objects.filter(patient=patient_user)\
                                           .prefetch_related('items')\
                                           .order_by('-created_at')

    context = {
        'patients': patients,
        'current_patient': current_patient,
        'patient_doctor': patient_doctor,
        'today_logs': today_logs,
        'prescriptions': prescriptions,
        'today': today,
        'total_doses_count': total_doses_count,
        'taken_doses_count': taken_doses_count,
        'missed_doses_count': missed_doses_count,
        'adherence_rate': adherence_rate,
        'next_log': next_log,
        'battery_level': 90,
        'box_status': 'ONLINE',
    }
    return render(request, 'dashboards/relative_dashboard.html', context)


# ==========================================
# VUES D'ACTIONS : LIAISONS MÉDECIN / PROCHE <-> PATIENT
# ==========================================

@login_required
@require_POST
def request_doctor_link(request):
    """Demande envoyée par un Patient via le Code Médecin."""
    if not request.user.is_patient:
        raise PermissionDenied("Seul un patient peut effectuer cette demande.")

    form = LinkDoctorForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data['doctor_code']
        try:
            doctor_profile = DoctorProfile.objects.get(doctor_code=code)
            doctor_user = doctor_profile.user

            link, created = DoctorPatientLink.objects.get_or_create(
                doctor=doctor_user,
                patient=request.user,
                defaults={
                    'initiated_by': DoctorPatientLink.Initiator.PATIENT,
                    'status': DoctorPatientLink.Status.PENDING
                }
            )

            if created:
                messages.success(request, f"Demande envoyée au Dr. {doctor_user.get_full_name() or doctor_user.username}.")
            elif link.status == DoctorPatientLink.Status.ACCEPTED:
                messages.info(request, f"Vous êtes déjà suivi par le Dr. {doctor_user.get_full_name() or doctor_user.username}.")
            else:
                messages.warning(request, f"Une demande est déjà en cours avec ce médecin ({link.get_status_display()}).")

        except DoctorProfile.DoesNotExist:
            messages.error(request, "Aucun médecin trouvé avec ce code. Veuillez vérifier le code.")

    return redirect('dashboards:patient-dashboard')


@login_required
@require_POST
def request_patient_link(request):
    """Invitation envoyée par un Médecin via le nom d'utilisateur du Patient."""
    if not request.user.is_doctor:
        raise PermissionDenied("Seul un médecin peut envoyer des invitations.")

    form = LinkPatientForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data['patient_identifier'].strip()
        
        patient_user = User.objects.filter(username__iexact=username, role=User.Role.PATIENT).first()
        if patient_user:
            link, created = DoctorPatientLink.objects.get_or_create(
                doctor=request.user,
                patient=patient_user,
                defaults={
                    'initiated_by': DoctorPatientLink.Initiator.DOCTOR,
                    'status': DoctorPatientLink.Status.PENDING
                }
            )

            if created:
                messages.success(request, f"Invitation envoyée au patient {patient_user.get_full_name() or patient_user.username}.")
            elif link.status == DoctorPatientLink.Status.ACCEPTED:
                messages.info(request, "Ce patient fait déjà partie de vos patients suivis.")
            else:
                messages.warning(request, "Une invitation est déjà en attente pour ce patient.")
        else:
            messages.error(request, f"Aucun patient trouvé sous le nom '{username}'.")

    return redirect('dashboards:doctor-dashboard')


@login_required
@require_POST
def request_patient_relative_link(request):
    """Permet à un PROCHE d'associer un patient à son compte."""
    is_relative = getattr(request.user, 'is_relative', False)
    if callable(is_relative):
        is_relative = is_relative()

    if not is_relative and getattr(request.user, 'role', None) != 'RELATIVE':
        raise PermissionDenied("Seul un proche aidant peut effectuer cette action.")

    form = LinkPatientToRelativeForm(request.POST)
    if form.is_valid():
        identifier = form.cleaned_data['patient_identifier'].strip()
        
        patient_user = User.objects.filter(username__iexact=identifier, role=User.Role.PATIENT).first() or \
                       User.objects.filter(email__iexact=identifier, role=User.Role.PATIENT).first()

        if not patient_user:
            messages.error(request, f"Aucun patient trouvé avec l'identifiant '{identifier}'.")
            return redirect('dashboards:relative-dashboard')

        caregiver_link, created = PatientCaregiver.objects.get_or_create(
            patient=patient_user,
            caregiver=request.user,
            defaults={'relationship': 'Proche Aidant'}
        )

        if created:
            messages.success(
                request, 
                f"Le patient {patient_user.get_full_name() or patient_user.username} a été associé à votre compte avec succès !"
            )
        else:
            messages.info(request, "Ce patient est déjà associé à votre compte.")

    return redirect('dashboards:relative-dashboard')


@login_required
@require_POST
def request_relative_patient_link(request):
    """Permet à un PATIENT d'associer un proche aidant à son compte."""
    if not request.user.is_patient and getattr(request.user, 'role', None) != 'PATIENT':
        raise PermissionDenied("Seul un patient peut effectuer cette action.")

    form = LinkRelativeToPatientForm(request.POST)
    if form.is_valid():
        identifier = form.cleaned_data['relative_identifier'].strip()
        
        relative_user = User.objects.filter(username__iexact=identifier, role=User.Role.RELATIVE).first() or \
                        User.objects.filter(email__iexact=identifier, role=User.Role.RELATIVE).first()

        if not relative_user:
            messages.error(request, f"Aucun proche aidant trouvé avec l'identifiant '{identifier}'.")
            return redirect('dashboards:patient-dashboard')

        if relative_user == request.user:
            messages.error(request, "Vous ne pouvez pas vous ajouter vous-même comme proche.")
            return redirect('dashboards:patient-dashboard')

        caregiver_link, created = PatientCaregiver.objects.get_or_create(
            patient=request.user,
            caregiver=relative_user,
            defaults={'relationship': 'Proche Aidant'}
        )

        if created:
            messages.success(
                request, 
                f"Le proche {relative_user.get_full_name() or relative_user.username} a été associé à votre compte avec succès !"
            )
        else:
            messages.info(request, "Ce proche aidant est déjà enregistré sur votre compte.")

    return redirect('dashboards:patient-dashboard')


@login_required
def respond_link_request(request, link_id, action):
    """Accepter ou refuser une demande de suivi."""
    link = get_object_or_404(DoctorPatientLink, id=link_id)

    is_doctor_recipient = (link.initiated_by == DoctorPatientLink.Initiator.PATIENT and request.user == link.doctor)
    is_patient_recipient = (link.initiated_by == DoctorPatientLink.Initiator.DOCTOR and request.user == link.patient)

    if is_doctor_recipient or is_patient_recipient:
        if action == 'accept':
            link.status = DoctorPatientLink.Status.ACCEPTED
            link.save()
            messages.success(request, "La demande de suivi médical a été acceptée.")
        elif action == 'reject':
            link.status = DoctorPatientLink.Status.REJECTED
            link.save()
            messages.warning(request, "La demande d'association a été refusée.")
    else:
        messages.error(request, "Action non autorisée sur cette demande.")

    return redirect(request.META.get('HTTP_REFERER', 'dashboards:main-dashboard'))


@login_required
@require_POST
def delete_user(request, user_id):
    """
    Supprime un utilisateur spécifique.
    Accès restreint aux administrateurs (is_staff) ou au propriétaire du compte.
    """
    user_to_delete = get_object_or_404(User, id=user_id)

    if request.user.is_staff or request.user == user_to_delete:
        username = user_to_delete.username
        is_self_delete = (request.user == user_to_delete)
        
        user_to_delete.delete()
        messages.success(request, f"L'utilisateur {username} a été supprimé avec succès.")
        
        if is_self_delete:
            return redirect('login')
            
        return redirect('dashboards:main-dashboard')
    
    messages.error(request, "Vous n'avez pas la permission de supprimer cet utilisateur.")
    return redirect('dashboards:main-dashboard')


@login_required
@require_POST
def remove_patient_link(request, link_id):
    """
    Permet à un médecin de rompre le suivi d'un patient.
    """
    if not request.user.is_doctor:
        raise PermissionDenied("Seul un médecin peut effectuer cette action.")
        
    link = get_object_or_404(DoctorPatientLink, id=link_id, doctor=request.user)
    patient_name = link.patient.get_full_name() or link.patient.username
    
    link.delete()
    
    messages.success(request, f"Le suivi du patient {patient_name} a été annulé avec succès.")
    return redirect('dashboards:doctor-dashboard')


@login_required
def add_caregiver_view(request):
    """Ajout d'un proche par le patient lui-même via la vue de formulaire dédiée."""
    if request.method == 'POST':
        form = AddCaregiverForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            relationship = form.cleaned_data['relationship']
            
            caregiver_user = User.objects.filter(email=email).first()
            
            if not caregiver_user:
                messages.error(request, "Aucun utilisateur trouvé avec cette adresse email.")
            elif caregiver_user == request.user:
                messages.error(request, "Vous ne pouvez pas vous ajouter vous-même comme proche.")
            elif PatientCaregiver.objects.filter(patient=request.user, caregiver=caregiver_user).exists():
                messages.warning(request, f"{caregiver_user.get_full_name() or caregiver_user.username} est déjà enregistré comme proche.")
            else:
                PatientCaregiver.objects.create(
                    patient=request.user,
                    caregiver=caregiver_user,
                    relationship=relationship
                )
                messages.success(request, f"{caregiver_user.get_full_name() or caregiver_user.username} a été ajouté avec succès à vos proches !")
                return redirect('dashboards:patient-dashboard')
    else:
        form = AddCaregiverForm()

    return render(request, 'add_caregiver.html', {'form': form})


@login_required
@require_POST
def remove_caregiver_link(request, link_id):
    """
    Permet à un Patient ou à un Proche de rompre leur association (PatientCaregiver).
    """
    # Recherche du lien en vérifiant que l'utilisateur est soit le patient, soit le proche
    link = get_object_or_404(
        PatientCaregiver, 
        Q(id=link_id) & (Q(patient=request.user) | Q(caregiver=request.user))
    )
    
    # Conservation des noms pour le message de confirmation
    patient_name = link.patient.get_full_name() or link.patient.username
    caregiver_name = link.caregiver.get_full_name() or link.caregiver.username
    
    link.delete()
    
    if request.user == link.patient:
        messages.success(request, f"Le proche aidant {caregiver_name} a été détaché de votre compte.")
        return redirect('dashboards:patient-dashboard')
    else:
        messages.success(request, f"L'association avec le patient {patient_name} a été supprimée.")
        return redirect('dashboards:relative-dashboard')