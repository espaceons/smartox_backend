from django.db import models
from accounts.models import User

class SMSNotification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)

    def __str__(self):
        return f"SMS à {self.recipient.username} - {'Succès' if self.success else 'Échec'}"