from django.contrib import admin
from .models import Plan, Subscription, Payment, UserPlanFeature

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'duration', 'is_active']
    list_filter = ['plan_type', 'duration', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'is_active']
    list_filter = ['status', 'is_active', 'plan', 'start_date']
    search_fields = ['user__username', 'user__email', 'plan__name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'amount', 'status', 'payment_date']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['subscription__user__username', 'gateway_payment_id']
    readonly_fields = ['created_at']

@admin.register(UserPlanFeature)
class UserPlanFeatureAdmin(admin.ModelAdmin):
    list_display = ['user', 'feature_name', 'is_active']
    list_filter = ['feature_name', 'is_active']
    search_fields = ['user__username', 'feature_name']