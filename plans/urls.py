from django.urls import path
from .views import PlanListView, CreateOrderView, VerifyPaymentView , PlanDetailView

urlpatterns = [
    path('list/', PlanListView.as_view(), name='plan-list'),
    path('create-order/', CreateOrderView.as_view(), name='create-order'),
    path('verify-payment/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('plan/<int:pk>/', PlanDetailView.as_view(), name='plan-detail'),

]
