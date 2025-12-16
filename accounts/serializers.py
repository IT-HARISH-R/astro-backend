from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
import re
from prediction.serializers import PredictionSerializer 
from email_utils.services import send_account_created_email

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = (
            'password', 'username', 'email', 'role', 'profile_image',
            'birth_year', 'birth_month', 'birth_day', 'birth_hour', 'birth_minute',
            'language','birth_place'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # send_account_created_email(
        #     user=user,
        #     subject="Welcome to Astro Platform!",
        #     template_name="email_utils/account_created.html",
        #     context={"custom_message": "Your account is now active!"}
        # )

        return user

 

class UserSerializer(serializers.ModelSerializer):
    # Sort predictions: newest first
    predictions = serializers.SerializerMethodField()

    def get_predictions(self, obj):
        # Order predictions by created_at descending
        predictions_qs = obj.predictions.all().order_by('-created_at')
        return PredictionSerializer(predictions_qs, many=True).data

    # Validate profile image URL
    def validate_profile_image(self, value):
        if value and isinstance(value, str):
            pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(pattern, value):
                raise serializers.ValidationError("Invalid profile image URL.")
        elif value and not isinstance(value, str):
            raise serializers.ValidationError("Profile image must be a URL or null.")
        return value

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "birth_year",
            "birth_month",
            "birth_day",
            "birth_hour",
            "birth_minute",
            "profile_image",
            "predictions",
            "role",
            'is_premium', 
            'plan_type',
            'email',
            "language",
            "date_joined",
            'birth_place',
        ]
        read_only_fields = ("predictions",)
