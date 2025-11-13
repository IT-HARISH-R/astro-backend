from rest_framework import serializers
from .models import ZodiacPrediction , LoveResult

class ZodiacPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZodiacPrediction
        fields = ["id","sign","date","prediction_text","ai_prompt","source_data","created_at"]

class LoveCalculatorSerializer(serializers.Serializer):
    name1 = serializers.CharField(max_length=100)
    name2 = serializers.CharField(max_length=100)



class LoveResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoveResult
        fields = '__all__'