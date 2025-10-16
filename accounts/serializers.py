from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
import re
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
    def validate_profile_image(self, value):
        # Allow URL or None (no file validation here, as view handles files)
        if value and isinstance(value, str):
            if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', value):
                raise serializers.ValidationError("Invalid profile image URL.")
        elif value and not isinstance(value, str):
            raise serializers.ValidationError("Profile image must be a URL or null.")
        return value

    class Meta:
        model = User
        fields = [
            "username",  # Added to support username updates
            "first_name", "last_name",
            "birth_year", "birth_month", "birth_day",
            "birth_hour", "birth_minute",
            "profile_image",
        ]
