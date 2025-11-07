from rest_framework import serializers
from .models import ZodiacPrediction

class ZodiacPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZodiacPrediction
        fields = ["id","sign","date","prediction_text","ai_prompt","source_data","created_at"]
