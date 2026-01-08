from rest_framework import serializers
from .models import Contact

class ContactSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True, required=False)
    user_email = serializers.CharField(source='user.email', read_only=True, required=False)
    
    class Meta:
        model = Contact
        fields = [
            'id',
            'user',
            'user_username',
            'user_email',
            'name',
            'email',
            'subject',
            'message',
            'status',
            'replied_at',
            'archived_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user']