from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator

User = get_user_model()

class Plan(models.Model):
    PLAN_TYPES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    DURATION_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES, default='monthly')
    features = models.JSONField(default=list)  # List of features included in this plan
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - ${self.price}/{self.duration}"

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)  # Payment gateway reference
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    def save(self, *args, **kwargs):
        if not self.end_date and self.plan.duration == 'monthly':
            self.end_date = self.start_date + timezone.timedelta(days=30)
        elif not self.end_date and self.plan.duration == 'yearly':
            self.end_date = self.start_date + timezone.timedelta(days=365)
        elif not self.end_date and self.plan.duration == 'lifetime':
            # Set end date far in the future for lifetime subscriptions
            self.end_date = self.start_date + timezone.timedelta(days=365*100)
        
        # Update is_active based on status and end_date
        if self.status == 'active' and self.end_date > timezone.now():
            self.is_active = True
        else:
            self.is_active = False
            
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.end_date < timezone.now()

    @property
    def days_remaining(self):
        if self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=50)
    payment_gateway = models.CharField(max_length=50, default='stripe')  # stripe, razorpay, etc.
    gateway_payment_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment #{self.id} - {self.amount} {self.currency}"

# class UserPlanFeature(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plan_features')
#     feature_name = models.CharField(max_length=100)
#     feature_value = models.JSONField(default=dict)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         unique_together = ['user', 'feature_name']

#     def __str__(self):
#         return f"{self.user.username} - {self.feature_name}"