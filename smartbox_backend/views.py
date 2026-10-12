from django.shortcuts import render
from accounts.models import User
from iot.models import ConnectedBox  # Ajustez l'import selon l'emplacement de ConnectedBox

def home(request):
    """
    Vue de la page d'accueil avec comptages dynamiques basés sur accounts.User
    """
    total_doctors = User.objects.filter(role='DOCTOR').count()
    total_patients = User.objects.filter(role='PATIENT').count()
    total_relatives = User.objects.filter(role='RELATIVE').count()
    
    # Nombre de boîtes IoT actives
    total_boxes = ConnectedBox.objects.filter(is_active=True).count()

    context = {
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_relatives': total_relatives,
        'total_boxes': total_boxes,
    }
    return render(request, 'home.html', context)