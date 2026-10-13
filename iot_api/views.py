import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from prescriptions.models import Prescription
from .models import DoseLog

User = get_user_model()


@require_http_methods(["GET"])
def get_arduino_schedule(request, patient_id):
    """
    Endpoint GET: /api/iot/schedule/<patient_id>/
    Renvoie le planning actif du patient sous forme de JSON structuré par
    Compartiment IoT et Heure de prise pour le microcontrôleur Arduino / ESP32.
    """
    patient = get_object_or_404(User, id=patient_id, role='PATIENT')

    # Récupérer la prescription la plus récente pour ce patient
    latest_prescription = (
        Prescription.objects.filter(patient=patient)
        .order_by('-created_at')
        .first()
    )

    if not latest_prescription:
        return JsonResponse({
            'status': 'success',
            'patient_id': patient.id,
            'server_time': timezone.now().strftime("%H:%M:%S"),
            'schedules': [],
            'message': 'Aucune prescription active trouvée.'
        }, status=200)

    # Récupérer la liste des compartiments et horaires via la méthode du modèle Prescription
    compartments = latest_prescription.get_compartments_by_time()

    # Formater les données pour une consommation facile sur microcontrôleur (C++)
    schedules_data = []
    for comp in compartments:
        schedules_data.append({
            'compartment': comp['compartment_number'],  # Ex: 1, 2, 3...
            'time': comp['time'],                       # Format HH:MM (Ex: "08:00")
            'medications_count': len(comp['medications']),
            'medications': [
                {
                    'name': med['medication_name'],
                    'dosage': med['dosage'] or '1 dose'
                }
                for med in comp['medications']
            ]
        })

    return JsonResponse({
        'status': 'success',
        'patient_id': patient.id,
        'prescription_id': latest_prescription.id,
        'server_time': timezone.now().strftime("%H:%M:%S"),
        'schedules': schedules_data
    }, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def record_dose_taken(request):
    """
    Endpoint POST: /api/iot/log/
    Reçoit la confirmation d'ouverture / prise depuis l'Arduino/ESP32.
    
    Format JSON attendu depuis l'Arduino:
    {
        "patient_id": 5,
        "compartment": 1,
        "status": "TAKEN"  // "TAKEN" ou "MISSED"
    }
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({
            'status': 'error',
            'message': 'Format JSON invalide.'
        }, status=400)

    patient_id = data.get('patient_id')
    compartment_number = data.get('compartment')
    status = data.get('status', 'TAKEN')  # 'TAKEN' par défaut

    if not patient_id or not compartment_number:
        return JsonResponse({
            'status': 'error',
            'message': 'Les champs patient_id et compartment sont obligatoires.'
        }, status=400)

    patient = get_object_or_404(User, id=patient_id, role='PATIENT')

    # Enregistrer le journal de prise dans la base de données
    log = DoseLog.objects.create(
        patient=patient,
        compartment_number=compartment_number,
        status=status,
        taken_at=timezone.now()
    )

    return JsonResponse({
        'status': 'success',
        'message': 'Prise enregistrée avec succès.',
        'log_id': log.id,
        'timestamp': log.taken_at.strftime("%Y-%m-%d %H:%M:%S")
    }, status=201)