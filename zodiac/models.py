from django.db import models

class ZodiacPrediction(models.Model):
    ZODIAC_CHOICES = [
        ("aries","Aries"), ("taurus","Taurus"), ("gemini","Gemini"),
        ("cancer","Cancer"), ("leo","Leo"), ("virgo","Virgo"),
        ("libra","Libra"), ("scorpio","Scorpio"), ("sagittarius","Sagittarius"),
        ("capricorn","Capricorn"), ("aquarius","Aquarius"), ("pisces","Pisces"),
    ]

    sign = models.CharField(max_length=32, choices=ZODIAC_CHOICES)
    date = models.DateField(db_index=True)  # prediction date (the "day" this prediction is for)
    prediction_text = models.TextField()
    ai_prompt = models.TextField(blank=True, null=True)
    source_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("sign", "date")
        ordering = ["-date", "sign"] 

    def __str__(self):
        return f"{self.sign} - {self.date}"
