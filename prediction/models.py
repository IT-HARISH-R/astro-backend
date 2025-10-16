from django.db import models
from django.conf import settings

class Prediction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="predictions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # astrology data
    julian_day = models.FloatField()
    sun_longitude = models.FloatField()
    moon_longitude = models.FloatField()

    # AI output
    thanglish_explanation = models.TextField()

    def __str__(self):
        return f"Prediction for {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"
