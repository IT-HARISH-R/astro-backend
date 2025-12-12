from django.urls import path
from .views import (
    PlanListView,
    PlanDetailView,
    CreateOrderView,
    VerifyPaymentView
)

urlpatterns = [
    path('list/', PlanListView.as_view(), name='plan-list'),
    path('plan/<int:pk>/', PlanDetailView.as_view(), name='plan-detail'),
    path('create-order/', CreateOrderView.as_view(), name='create-order'),
    path('verify-payment/', VerifyPaymentView.as_view(), name='verify-payment'),
]
