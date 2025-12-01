from django.urls import path
from .views import (
    PlanListView, SubscribeView, UserSubscriptionView, CancelSubscriptionView,
    SubscriptionListView, PaymentListView, PlanManagementView
)

urlpatterns = [
    # User endpoints
    path('plans/', PlanListView.as_view(), name='plan-list'),
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('my-subscription/', UserSubscriptionView.as_view(), name='user-subscription'),
    path('cancel/<int:subscription_id>/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    
    # Admin endpoints
    path('admin/subscriptions/', SubscriptionListView.as_view(), name='admin-subscription-list'),
    path('admin/payments/', PaymentListView.as_view(), name='admin-payment-list'),
    path('admin/plans/', PlanManagementView.as_view(), name='admin-plan-create'),
    path('admin/plans/<int:plan_id>/', PlanManagementView.as_view(), name='admin-plan-update'),
]