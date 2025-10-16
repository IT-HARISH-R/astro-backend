from rest_framework import serializers
from prediction.models import Prediction  

class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = [
            "id",
            "created_at",
            "birth_year",
            "birth_month",
            "birth_day",
            "birth_hour",
            "birth_minute",
            "julian_day",
            "sun_longitude",
            "moon_longitude",
            "thanglish_explanation"
        ]
