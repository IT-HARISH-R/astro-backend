from django.utils import timezone
from .models import UserPlan

def deactivate_expired_plans():
    expired_plans = UserPlan.objects.filter(
        is_active=True,
        end_date__lt=timezone.now()
    )

    for plan in expired_plans:
        plan.is_active = False
        plan.save()

        user = plan.user
        user.is_premium = False
        user.plan_type = "free"
        user.save()
