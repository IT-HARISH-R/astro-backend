from rest_framework import serializers
from .models import ChatRoom, ChatMessage

class STTSerializer(serializers.Serializer):
    audio = serializers.FileField()


class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ['id', 'title', 'created_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'user_text', 'ai_text', 'tts_url', 'created_at']
