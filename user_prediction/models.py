from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class ChatRoom(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    user_text = models.TextField()
    ai_text = models.TextField()
    tts_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
