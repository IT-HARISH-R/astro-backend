from django.urls import path
from .views import GenerateTextAPIView

urlpatterns = [
    path("text/", GenerateTextAPIView.as_view(), name="generate-text"),
]
