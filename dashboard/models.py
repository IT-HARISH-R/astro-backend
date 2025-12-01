# dashboard/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class DashboardAnalytics(models.Model):
    total_users = models.IntegerField(default=0)
    active_subscriptions = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    horoscopes_generated = models.IntegerField(default=0)
    date_recorded = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Dashboard Analytics"
        ordering = ['-date_recorded']

class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('prediction', 'Future Prediction'),
        ('horoscope', 'Daily Horoscope'),
        ('kundli', 'Kundli Analysis'),
        ('subscription', 'Subscription Purchase'),
        ('login', 'User Login'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "User Activities"
        ordering = ['-created_at']