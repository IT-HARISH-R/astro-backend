# dashboard/urls.py
from django.urls import path
from .views import DashboardStatsView, RecentActivityView, RevenueAnalyticsView

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('recent-activities/', RecentActivityView.as_view(), name='recent-activities'),
    path('revenue-analytics/', RevenueAnalyticsView.as_view(), name='revenue-analytics'),
]