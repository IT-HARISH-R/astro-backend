from django.db import models
from accounts.models import User
from django.utils import timezone
from datetime import timedelta


class Plan(models.Model):
    PLAN_TYPE_CHOICES = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('one_time', 'One-Time'),
    )

    name = models.CharField(max_length=50, default="Free")
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default='monthly')
    price = models.IntegerField(default=0)
    description = models.TextField(blank=True, default="")
    features = models.JSONField(default=list)

    # ⭐ Duration added (for auto end date)
    duration_days = models.IntegerField(default=30)

    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Automatically set duration based on plan_type
        if self.plan_type == "monthly":
            self.duration_days = 30
        elif self.plan_type == "yearly":
            self.duration_days = 365
        else:
            self.duration_days = 0  # One-time / lifetime
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.plan_type})"


class UserPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    def set_end_date(self):
        """Automatically set end date based on duration"""
        if self.plan and self.plan.duration_days > 0:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        else:
            self.end_date = None  # for lifetime plans

    def save(self, *args, **kwargs):
        if not self.end_date:  # calculate only once
            self.set_end_date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="plan_payments")
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    amount = models.IntegerField(default=0)
    currency = models.CharField(max_length=3, default='INR')

    payment_gateway = models.CharField(max_length=50, default='razorpay')
    gateway_order_id = models.CharField(max_length=100, null=True, blank=True)
    gateway_payment_id = models.CharField(max_length=100, null=True, blank=True)
    gateway_signature = models.CharField(max_length=255, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # AUTO END DATE
    end_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # 1. Auto end date calculation
        if self.plan and not self.end_date:
            if self.plan.duration_days > 0:
                self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
            else:
                self.end_date = None  # Lifetime (free / one-time)

        super().save(*args, **kwargs)

        # 2. If payment is completed, update USER plan details
        if self.status == "completed":
            self.user.is_premium = True

            # update plan type (monthly / yearly / one_time / free)
            self.user.plan_type = self.plan.plan_type

            self.user.save()

            # 3. Create or update UserPlan
            user_plan, created = UserPlan.objects.get_or_create(
                user=self.user,
                defaults={
                    "plan": self.plan,
                    "is_active": True,
                    "start_date": timezone.now(),
                }
            )
            user_plan.plan = self.plan
            user_plan.is_active = True
            user_plan.end_date = self.end_date
            user_plan.save()
