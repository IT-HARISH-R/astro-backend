from django.urls import path
from .views import VoiceAIView, ChatListView, ChatMessageListView, ChatDeleteView

urlpatterns = [
    path("chat/", VoiceAIView.as_view(), name="voice-chat"),
    path("chat/list/", ChatListView.as_view(), name="chat-list"),
    path("chat/<int:chat_id>/messages/", ChatMessageListView.as_view(), name="chat-messages"),
    path("chat/<int:pk>/", ChatDeleteView.as_view(), name="chat-delete"),  

]
