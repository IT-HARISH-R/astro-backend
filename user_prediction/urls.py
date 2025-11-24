from django.urls import path
from .views import *

urlpatterns = [
    path("chat/", VoiceAIView.as_view()), 
]
  