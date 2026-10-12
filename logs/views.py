from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from devices.models import SmartBox
from .models import MedicationLog
from notifications.services import send_alert_sms

class DeviceMedicationUpdateView(APIView):
    def post(self, request):
        api_key = request.headers.get('X-Box-API-Key')
        
        try:
            box = SmartBox.objects.get(api_key=api_key, is_active=True)
            box.last_ping = timezone.now()
            box.save()
        except SmartBox.DoesNotExist:
            return Response({"error": "Clé d'API invalide ou boîte inactive"}, status=status.HTTP_401_UNAUTHORIZED)

        log_id = request.data.get('log_id')
        new_status = request.data.get('status')  # 'TAKEN' ou 'MISSED'

        try:
            log = MedicationLog.objects.get(id=log_id, prescription__patient=box.patient)
            log.status = new_status
            log.actual_datetime = timezone.now()
            log.save()

            # Si le médicament a été manqué, envoyer un SMS au proche
            if new_status == 'MISSED':
                relative = box.patient.relative
                if relative:
                    patient_name = box.patient.user.get_full_name() or box.patient.user.username
                    med_name = log.prescription.medication_name
                    msg = f"Alerte Boîte Intelligente : {patient_name} n'a pas pris son médicament ({med_name}) à l'heure prévue."
                    send_alert_sms(relative, msg)

            return Response({"status": "Mise à jour réussie"}, status=status.HTTP_200_OK)
        except MedicationLog.DoesNotExist:
            return Response({"error": "Enregistrement non trouvé"}, status=status.HTTP_404_NOT_FOUND)