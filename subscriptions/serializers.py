from rest_framework import serializers
from .models import Plan, Subscription, Payment, UserPlanFeature
from django.contrib.auth import get_user_model

User = get_user_model()

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    plan_details = PlanSerializer(source='plan', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    days_remaining = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class CreateSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('plan', 'payment_method')

    def validate(self, attrs):
        user = self.context['request'].user
        plan = attrs['plan']
        
        # Check if user already has an active subscription for this plan
        active_subscription = Subscription.objects.filter(
            user=user, 
            plan=plan, 
            is_active=True
        ).exists()
        
        if active_subscription:
            raise serializers.ValidationError("You already have an active subscription for this plan.")
        
        return attrs

class PaymentSerializer(serializers.ModelSerializer):
    subscription_details = SubscriptionSerializer(source='subscription', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('created_at',)

class UserPlanFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPlanFeature
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class UserSubscriptionSummarySerializer(serializers.ModelSerializer):
    current_subscription = serializers.SerializerMethodField()
    plan_features = UserPlanFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'current_subscription', 'plan_features')

    def get_current_subscription(self, obj):
        active_subscription = obj.subscriptions.filter(is_active=True).first()
        if active_subscription:
            return SubscriptionSerializer(active_subscription).data
        return None