from rest_framework import serializers

class STTSerializer(serializers.Serializer):
    audio = serializers.FileField()
