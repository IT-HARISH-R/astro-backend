from django.urls import path
from .views import BirthChartView 

urlpatterns = [
    path('birthchart/', BirthChartView.as_view(), name='birth_chart'),
]
