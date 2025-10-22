from django.db import models
from accounts.models import User

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.IntegerField()
    status = models.CharField(max_length=20, default='created')  # created, paid, failed
    created_at = models.DateTimeField(auto_now_add=True)
