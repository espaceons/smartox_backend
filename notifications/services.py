import logging
from .models import SMSNotification

logger = logging.getLogger(__name__)

def send_alert_sms(recipient_user, message_text):
    """
    Fonction centralisée pour l'envoi de SMS (ex: via Twilio ou Gateway GSM)
    """
    if not recipient_user.phone_number:
        return False

    # Exemple d'intégration Twilio / Gateway API :
    # client.messages.create(body=message_text, from_='+123456789', to=recipient_user.phone_number)

    logger.info(f"[SMS Simulé] Envoyé à {recipient_user.phone_number}: {message_text}")
    
    SMSNotification.objects.create(
        recipient=recipient_user,
        message=message_text,
        success=True
    )
    return True