from django.urls import path
from .views import (
    GetPaymentsView,
    GetPaymentDetailsView,
    UpdatePaymentStatusView,
    ExportPaymentsView,
    PaymentAnalyticsView
)

urlpatterns = [
    path('', GetPaymentsView.as_view(), name='get-payments'),
    path('<int:payment_id>/', GetPaymentDetailsView.as_view(), name='get-payment-details'),
    path('<int:payment_id>/update-status/', UpdatePaymentStatusView.as_view(), name='update-payment-status'),
    path('export/', ExportPaymentsView.as_view(), name='export-payments'),
    path('analytics/', PaymentAnalyticsView.as_view(), name='payment-analytics'),
]