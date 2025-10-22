from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'user', 'razorpay_order_id', 'razorpay_payment_id', 'amount', 'status', 'created_at']
