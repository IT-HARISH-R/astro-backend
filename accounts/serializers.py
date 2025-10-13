from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = (
            'password', 'username', 'email', 'role', 'profile_image',
            'birth_year', 'birth_month', 'birth_day', 'birth_hour', 'birth_minute'
        )
        read_only_fields = ('id',)
        
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "last_name", "role",
            "birth_year", "birth_month", "birth_day", "birth_hour", "birth_minute"
        )
