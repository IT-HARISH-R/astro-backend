from django.urls import path
from .views import TodayPredictions, RegeneratePrediction , LoveCalculatorView
 
urlpatterns = [
    path("today/", TodayPredictions.as_view(), name="today_predictions"),
    path("regenerate/", RegeneratePrediction.as_view(), name="regenerate_prediction"),
    path('love/', LoveCalculatorView.as_view(), name='love_calculator'),
]
