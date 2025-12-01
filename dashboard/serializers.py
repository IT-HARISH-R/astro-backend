# dashboard/serializers.py
from rest_framework import serializers
from .models import Service, Customer, Subscription, Activity

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name']

class CustomerSerializer(serializers.ModelSerializer):
    initials = serializers.CharField(source='initials', read_only=True)
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'email', 'plan', 'initials']

class SubscriptionSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    class Meta:
        model = Subscription
        fields = ['id', 'customer', 'active', 'started_at', 'renewals']

class ActivitySerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), source='customer', write_only=True, required=False)
    service_id = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), source='service', write_only=True)

    class Meta:
        model = Activity
        fields = ['id', 'customer', 'service', 'date_time', 'status', 'amount', 'created_at', 'customer_id', 'service_id']
# dashboard/serializers.py
from rest_framework import serializers
from .models import Service, Customer, Subscription, Activity

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name']

class CustomerSerializer(serializers.ModelSerializer):
    initials = serializers.CharField(source='initials', read_only=True)
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'email', 'plan', 'initials']

class SubscriptionSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    class Meta:
        model = Subscription
        fields = ['id', 'customer', 'active', 'started_at', 'renewals']

class ActivitySerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), source='customer', write_only=True, required=False)
    service_id = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), source='service', write_only=True)

    class Meta:
        model = Activity
        fields = ['id', 'customer', 'service', 'date_time', 'status', 'amount', 'created_at', 'customer_id', 'service_id']
