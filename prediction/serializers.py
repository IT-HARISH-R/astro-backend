from rest_framework import serializers

from rest_framework import serializers

class BirthDataSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    gender = serializers.CharField(max_length=10)
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    day = serializers.IntegerField()
    hour = serializers.IntegerField()
    minute = serializers.IntegerField()
    second = serializers.IntegerField(default=0)
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()
    timezone = serializers.FloatField()
    place = serializers.CharField(max_length=100)
