from django.db import models
from accounts.models import User

class Plan(models.Model):
    PLAN_TYPE_CHOICES = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('one_time', 'One-Time'),
    )

    name = models.CharField(max_length=50, default="Free")         # free, premium
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default='monthly')
    price = models.IntegerField(default=0)                         # amount in INR
    description = models.TextField(blank=True, default="")         # plan description
    features = models.JSONField(default=list)

    def __str__(self):
        return f"{self.name} ({self.plan_type})"

class UserPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
