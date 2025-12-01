# dashboard/admin.py
from django.contrib import admin
from .models import DashboardAnalytics, UserActivity

@admin.register(DashboardAnalytics)
class DashboardAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date_recorded', 'total_users', 'active_subscriptions', 'total_revenue']
    list_filter = ['date_recorded']
    readonly_fields = ['created_at']

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'amount', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at']