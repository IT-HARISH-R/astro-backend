from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class FuturePrediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prediction_text = models.TextField()
    planetary_data = models.JSONField()
    birth_details = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        """Return True if prediction is less than 3 days old."""
        return timezone.now() - self.created_at < timedelta(days=3)

    def __str__(self):
        return f"Prediction for {self.user.username} on {self.created_at}"
