from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('password', 'username', 'email', 'role', 'profile_image')  # include profile_image
        read_only_fields = ('id',)
        
    def create(self, validated_data):
        password = validated_data.pop("password")  # remove password from dict
        user = User.objects.create(**validated_data)  # create user without password
        user.set_password(password)  # set hashed password
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role")
