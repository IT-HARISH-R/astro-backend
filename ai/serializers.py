from rest_framework import serializers

class GenerateTextSerializer(serializers.Serializer):
    prompt = serializers.CharField(min_length=1, max_length=2000)
    model = serializers.CharField(default="gemini-2.5-flash", required=False)
