from django.urls import path
from .views import FuturePredictionView

urlpatterns = [
    path("predict-future/", FuturePredictionView.as_view()),
]
