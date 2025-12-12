from rest_framework import serializers
from .models import Plan, UserPlan, Payment


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'


class UserPlanSerializer(serializers.ModelSerializer):
    plan = PlanSerializer()

    class Meta:
        model = UserPlan
        fields = ['plan', 'is_active', 'start_date', 'end_date']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
