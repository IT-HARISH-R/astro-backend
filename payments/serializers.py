from rest_framework import serializers
from plans.models import Payment, Plan
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    initials = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'initials']

    def get_initials(self, obj):
        if not obj.username:
            return "U"
        name = obj.username.strip().split()
        return (name[0][0] + (name[1][0] if len(name) > 1 else "")).upper()


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'plan_type', 'price', 'duration_days']


class PaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plan = PlanSerializer(read_only=True)
    transaction_id = serializers.CharField(source='gateway_order_id', read_only=True)
    method = serializers.CharField(source='payment_gateway', read_only=True)
    date = serializers.DateTimeField(source='created_at', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'plan', 'amount', 'currency',
            'transaction_id', 'method', 'status', 'date',
            'duration', 'gateway_payment_id'
        ]

    def get_duration(self, obj):
        if obj.plan:
            if obj.plan.plan_type == 'monthly':
                return 'Monthly'
            elif obj.plan.plan_type == 'yearly':
                return 'Yearly'
            elif obj.plan.plan_type == 'one_time':
                return 'One-time'
        return 'N/A'


class PaymentDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plan = PlanSerializer(read_only=True)
    base_amount = serializers.SerializerMethodField()
    tax = serializers.SerializerMethodField()
    fee = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'plan', 'amount', 'currency',
            'payment_gateway', 'gateway_order_id',
            'gateway_payment_id', 'status', 'created_at',
            'end_date', 'base_amount', 'tax', 'fee'
        ]

    def get_base_amount(self, obj):
        # Assuming base amount is 90% of total amount (10% for tax+fee)
        return round(obj.amount * 0.9, 2)

    def get_tax(self, obj):
        # Assuming tax is 5% of total amount
        return round(obj.amount * 0.05, 2)

    def get_fee(self, obj):
        # Assuming fee is 5% of total amount
        return round(obj.amount * 0.05, 2)