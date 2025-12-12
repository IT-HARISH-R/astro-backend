from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class DashboardStatsView(APIView):
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # Calculate time ranges
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)

            # User statistics
            total_users = User.objects.count()
            new_users_today = User.objects.filter(date_joined__date=today).count()
            new_users_week = User.objects.filter(date_joined__date__gte=week_ago).count()
            active_users = User.objects.filter(is_active=True).count()

            # Try to get subscription data
            try:
                from plans.models import Subscription
                active_subscriptions = UserPlan.objects.filter(is_active=True).count()
                active_subscriptions = Subscription.objects.filter(
                    is_active=True
                ).count()

                total_revenue = Subscription.objects.aggregate(
                    total=Sum('amount_paid')
                )['total'] or 0

                revenue_today = Subscription.objects.filter(
                    created_at__date=today
                ).aggregate(total=Sum('amount_paid'))['total'] or 0

                revenue_week = Subscription.objects.filter(
                    created_at__date__gte=week_ago
                ).aggregate(total=Sum('amount_paid'))['total'] or 0

            except ImportError:
                active_subscriptions = 0
                total_revenue = 0
                revenue_today = 0
                revenue_week = 0

            # Prediction data (combine from 2 models)
            total_predictions = 0
            predictions_today = 0
            predictions_week = 0

            # 1️⃣ ChatMessage model (user_prediction app)
            try:
                from user_prediction.models import ChatMessage

                total_predictions += ChatMessage.objects.count()
                predictions_today += ChatMessage.objects.filter(
                    created_at__date=today
                ).count()
                predictions_week += ChatMessage.objects.filter(
                    created_at__date__gte=week_ago
                ).count()

            except ImportError:
                pass  # If this model doesn't exist, skip

            # 2️⃣ Prediction model (prediction app)
            try:
                from prediction.models import Prediction

                total_predictions += Prediction.objects.count()
                predictions_today += Prediction.objects.filter(
                    created_at__date=today
                ).count()
                predictions_week += Prediction.objects.filter(
                    created_at__date__gte=week_ago
                ).count()

            except ImportError:
                pass  # If this model doesn't exist, skip


            stats = {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'new_today': new_users_today,
                    'new_week': new_users_week,
                    'growth_rate': self.calculate_growth_rate(new_users_week, total_users)
                },
                'revenue': {
                    'total': float(total_revenue),
                    'today': float(revenue_today),
                    'week': float(revenue_week),
                    'growth_rate': self.calculate_growth_rate(revenue_week, total_revenue) if total_revenue > 0 else 0
                },
                'predictions': {
                    'total': total_predictions,
                    'today': predictions_today,
                    'week': predictions_week,
                    'growth_rate': self.calculate_growth_rate(predictions_week, total_predictions) if total_predictions > 0 else 0
                },
                'subscriptions': {
                    'active': active_subscriptions,
                    'growth_rate': 0
                },
                'user_role': 'admin'
            }  # ← FIXED: Missing closing brace

            return Response(stats)

        except Exception as e:
            logger.error(f"Dashboard stats error: {str(e)}")
            return Response({'error': 'Failed to fetch dashboard statistics'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def calculate_growth_rate(self, recent_value, total_value):
        if total_value == 0:
            return 0
        return round((recent_value / total_value) * 100, 2)

class RecentActivityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            activities = []
            user = request.user

            # Admin: show all recent activities
            print(user)
            print(user.is_staff)
            if user.is_staff:
                # 1. Recent user registrations
                recent_users = User.objects.order_by('-date_joined')[:5]
                for u in recent_users:
                    activities.append({
                        'type': 'user registration',
                        'user': u.username,
                        'description': f'New user registered : {u.username}',
                        'timestamp': u.date_joined,
                        'avatar': self.get_avatar_initials(u.username),
                        'status': 'completed'
                    })

                # 2. Subscriptions
                try:
                    from plans.models import Payment

                    recent_subscriptions = (
                        Payment.objects
                        .select_related('user', 'plan')
                        .filter(status="completed")
                        .order_by('-created_at')[:5]
                    )

                    for s in recent_subscriptions:
                        activities.append({
                            'type': 'subscription',
                            'user': s.user.username,
                            'description': f"Subscription : {s.plan.plan_type}",
                            'timestamp': s.created_at,
                            'amount': float(s.amount or 0),
                            'status': s.status,  # completed / pending / failed
                            'avatar': self.get_avatar_initials(s.user.username)
                        })

                except ImportError:
                    pass


                # 3. Future Prediction Activities
                try:
                    from future_predictions.models import FuturePrediction
                    recent_predictions = (
                        FuturePrediction.objects
                        .select_related('user')
                        .order_by('-created_at')[:5]
                    )
                    for p in recent_predictions:
                        activities.append({
                            'type': 'prediction',
                            'user': p.user.username,
                            'description': "Future prediction generated",
                            'timestamp': p.created_at,
                            'service': "Future Prediction",
                            'avatar': self.get_avatar_initials(p.user.username),
                            'status': 'completed'
                        })
                except ImportError:
                    pass

                # 4. Birth Chart Activities
                try:
                    from prediction.models import Prediction
                    recent_predictions = (
                        Prediction.objects
                        .select_related('user')
                        .order_by('-created_at')[:5]
                    )
                    for p in recent_predictions:
                        activities.append({
                            'type': 'prediction',
                            'user': p.user.username,
                            'description': "Birth Chart generated",
                            'timestamp': p.created_at,
                            'service': "Birth Chart Prediction",
                            'avatar': self.get_avatar_initials(p.user.username),
                            'status': 'completed'
                        })
                except ImportError:
                    pass

                # 5. Chat Prediction Activities
                try:
                    from user_prediction.models import ChatRoom
                    recent_predictions = (
                        ChatRoom.objects
                        .select_related('user')
                        .order_by('-created_at')[:5]
                    )
                    for p in recent_predictions:
                        activities.append({
                            'type': 'prediction',
                            'user': p.user.username,
                            'description': "New Chat Prediction",
                            'timestamp': p.created_at,
                            'service': "Chat Prediction",
                            'avatar': self.get_avatar_initials(p.user.username),
                            'status': 'completed'
                        })
                except ImportError:
                    pass
              

            else:
                # NORMAL USER: only show their activities
                activities = []

                # User's predictions
                try:
                    from prediction.models import Prediction
                    user_predictions = (
                        Prediction.objects
                        .filter(user=user)
                        .order_by('-created_at')[:5]
                    )
                    for p in user_predictions:
                        activities.append({
                            'type': 'prediction',
                            'user': user.username,
                            'description': "Future prediction generated",
                            'timestamp': p.created_at,
                            'service': "Future Prediction",
                            'avatar': self.get_avatar_initials(user.username),
                            'status': 'completed'
                        })
                except ImportError:
                    pass

                # User's subscriptions
                try:
                    from plans.models import Subscription
                    user_subscriptions = (
                        Subscription.objects
                        .filter(user=user)
                        .order_by('-created_at')[:3]
                    )
                    for s in user_subscriptions:
                        activities.append({
                            'type': 'subscription',
                            'user': user.username,
                            'description': f"Subscription: {s.plan.name}",
                            'timestamp': s.created_at,
                            'amount': float(s.amount_paid) if s.amount_paid else 0,
                            'status': 'completed' if getattr(s, 'is_active', False) else 'pending',
                            'avatar': self.get_avatar_initials(user.username)
                        })
                except ImportError:
                    pass

            # ✅ FIXED: sort using datetime, not string
            activities.sort(key=lambda x: x['timestamp'], reverse=True)

            return Response(activities[:10])

        except Exception as e:
            logger.error(f"Recent activity error: {str(e)}")
            return Response(
                {'error': 'Failed to fetch recent activities'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_avatar_initials(self, username):
        if not username:
            return "U"
        name = username.strip().split()
        return (name[0][0] + (name[1][0] if len(name) > 1 else "")).upper()


class RevenueAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if not request.user.is_staff:
                return Response({
                    'labels': [],
                    'revenue': [],
                    'subscriptions': [],
                    'message': 'Revenue analytics available for admin users only'
                })

            from plans.models import Payment, UserPlan

            today = timezone.now().date()

            # ----------------------------
            # 📌 Month Start (1st day of month)
            # ----------------------------
            month_start = today.replace(day=1)

            # ----------------------------
            # 📌 Week Start (Monday)
            # ----------------------------
            week_start = today - timedelta(days=today.weekday())

            # ----------------------------
            # 📌 30 Days Chart Range
            # ----------------------------
            start_date = today - timedelta(days=30)

            # ----------------------------
            # 📌 Daily Chart Data (Last 30 days)
            # ----------------------------
            daily_data = Payment.objects.filter(
                created_at__date__range=[start_date, today],
                status="completed"
            ).extra({'date': "date(created_at)"}
            ).values('date').annotate(
                total_revenue=Sum('amount'),
                subs_count=Count('id')
            ).order_by('date')

            chart = {
                "labels": [],
                "revenue": [],
                "subscriptions": [],
            }

            for item in daily_data:
                chart["labels"].append(item["date"].strftime('%Y-%m-%d'))
                chart["revenue"].append(float(item["total_revenue"] or 0))
                chart["subscriptions"].append(item["subs_count"])

            # ----------------------------
            # 📌 Monthly Revenue (1st → today)
            # ----------------------------
            monthly_revenue = Payment.objects.filter(
                status="completed",
                created_at__date__range=[month_start, today]
            ).aggregate(total=Sum("amount"))["total"] or 0

            # ----------------------------
            # 📌 Weekly Revenue (Mon → today)
            # ----------------------------
            weekly_revenue = Payment.objects.filter(
                status="completed",
                created_at__date__range=[week_start, today]
            ).aggregate(total=Sum("amount"))["total"] or 0

            # ----------------------------
            # 📌 Total Revenue (30 days)
            # ----------------------------
            total_revenue = Payment.objects.filter(
                status="completed",
                created_at__date__range=[start_date, today]
            ).aggregate(total=Sum("amount"))["total"] or 0

            # ----------------------------
            # 📌 Active Subscriptions
            # ----------------------------
            active_subs = UserPlan.objects.filter(is_active=True).count()

            # ----------------------------
            # 📌 Today's Revenue
            # ----------------------------
            todays_revenue = Payment.objects.filter(
                status="completed",
                created_at__date=today
            ).aggregate(total=Sum("amount"))["total"] or 0

            # ----------------------------
            # 📌 Revenue Growth %
            # ----------------------------
            prev_30_start = start_date - timedelta(days=30)
            prev_30_end = start_date

            prev_revenue = Payment.objects.filter(
                status="completed",
                created_at__date__range=[prev_30_start, prev_30_end]
            ).aggregate(total=Sum("amount"))["total"] or 0

            if prev_revenue == 0:
                revenue_growth = "+0%"
            else:
                growth = ((total_revenue - prev_revenue) / prev_revenue) * 100
                revenue_growth = f"{growth:.2f}%"

            # =======================================================
            # 📌 SUBSCRIPTION GROWTH (%)
            # =======================================================

            # Current month subscriptions
            current_month_subs = UserPlan.objects.filter(
                start_date__date__range=[month_start, today]
            ).count()

            # Previous month range
            prev_month_end = month_start - timedelta(days=1)
            prev_month_start = prev_month_end.replace(day=1)

            previous_month_subs = UserPlan.objects.filter(
                start_date__date__range=[prev_month_start, prev_month_end]
            ).count()

            if previous_month_subs == 0:
                subscription_growth = "+0%"
            else:
                subs_g = ((current_month_subs - previous_month_subs) / previous_month_subs) * 100
                subscription_growth = f"{subs_g:.2f}%"

            # =======================================================

            # ----------------------------
            # 📌 FINAL RESPONSE
            # ----------------------------
            return Response({
                "chart": chart,
                "metrics": {
                    "total_revenue": float(total_revenue),
                    "monthly_revenue": float(monthly_revenue),
                    "weekly_revenue": float(weekly_revenue),
                    "todays_revenue": float(todays_revenue),
                    "active_subscriptions": active_subs,
                    "revenue_growth": revenue_growth,

                    # 🔥 NEW METRICS ADDED
                    "monthly_subscriptions": current_month_subs,
                    "subscription_growth": subscription_growth,

                    "week_start": week_start.strftime("%Y-%m-%d"),
                    "month_start": month_start.strftime("%Y-%m-%d")
                }
            })

        except Exception as e:
            logger.error(f"Revenue analytics error: {str(e)}")
            return Response(
                {'error': 'Failed to fetch revenue analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
