from django.urls import path
from .views import *

urlpatterns = [
    path("compute/", AstroThanglishAPIView.as_view(), name="astro-compute"),
]
