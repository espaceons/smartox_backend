from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from .models import ConnectedBox

User = get_user_model()


def home(request):
    """
    Vue de la page d'accueil public avec comptages dynamiques
    """
    # Compter les rôles depuis le modèle CustomUser (role: 'DOCTOR', 'PATIENT', 'RELATIVE')
    total_doctors = User.objects.filter(role='DOCTOR').count() if hasattr(User, 'role') else 0
    total_patients = User.objects.filter(role='PATIENT').count() if hasattr(User, 'role') else 0
    total_relatives = User.objects.filter(role='RELATIVE').count() if hasattr(User, 'role') else 0
    
    # Compter les boîtes IoT actives enregistrées dans le système
    total_boxes = ConnectedBox.objects.filter(is_active=True).count()

    context = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_relatives': total_relatives,
        'total_boxes': total_boxes,
    }
    return render(request, 'home.html', context)


@csrf_exempt
def api_sync_box(request):
    """
    Endpoint API pour heartbeat / ping de l'ESP32/Arduino
    Exemple POST JSON: {"uid": "ESP32-12345", "status": "ONLINE"}
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            uid = data.get('uid')
            status = data.get('status', 'ONLINE')

            box, created = ConnectedBox.objects.get_or_create(uid=uid)
            box.status = status
            box.last_ping = timezone.now()
            box.save()

            return JsonResponse({'status': 'success', 'message': f'Box {uid} synced.'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)