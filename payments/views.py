from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
import json
from django.db import transaction

from plans.models import Payment, UserPlan, Plan
from accounts.models import User
from .serializers import PaymentSerializer, PaymentDetailSerializer
from dashboard.views import logger


class PaymentsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class GetPaymentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            if not request.user.is_staff:
                return Response(
                    {'error': 'Unauthorized access'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get query parameters
            date_range = request.query_params.get('dateRange', '30d')
            status_filter = request.query_params.get('status', 'all')
            payment_method_filter = request.query_params.get('paymentMethod', 'all')
            search_term = request.query_params.get('search', '')
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 10))

            # Calculate date range
            end_date = timezone.now()
            if date_range == '7d':
                start_date = end_date - timedelta(days=7)
            elif date_range == '30d':
                start_date = end_date - timedelta(days=30)
            elif date_range == '90d':
                start_date = end_date - timedelta(days=90)
            elif date_range == '1y':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = None  # all time

            # Base queryset
            queryset = Payment.objects.select_related('user', 'plan').order_by('-created_at')

            # Apply date filter
            if start_date:
                queryset = queryset.filter(created_at__range=[start_date, end_date])

            # Apply status filter
            if status_filter != 'all':
                queryset = queryset.filter(status=status_filter)

            # Apply payment method filter
            if payment_method_filter != 'all':
                queryset = queryset.filter(payment_gateway=payment_method_filter)

            # Apply search filter
            if search_term:
                queryset = queryset.filter(
                    Q(user__username__icontains=search_term) |
                    Q(user__email__icontains=search_term) |
                    Q(gateway_order_id__icontains=search_term) |
                    Q(gateway_payment_id__icontains=search_term) |
                    Q(plan__name__icontains=search_term)
                )

            # Calculate total count before pagination
            total_count = queryset.count()

            # Apply pagination
            paginator = PaymentsPagination()
            paginator.page_size = limit
            paginated_payments = paginator.paginate_queryset(queryset, request)

            # Serialize data
            serializer = PaymentSerializer(paginated_payments, many=True)

            # Calculate summary statistics
            stats = self.calculate_statistics(queryset)

            return Response({
                'payments': serializer.data,
                'total_count': total_count,
                'current_page': page,
                'page_size': limit,
                'stats': stats
            })

        except Exception as e:
            logger.error(f"Get payments error: {str(e)}")
            return Response(
                {'error': 'Failed to fetch payments'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def calculate_statistics(self, queryset):
        """Calculate payment statistics"""
        try:
            # Get all payments for stats calculation
            all_payments = queryset
            
            # Total amount
            total_amount = all_payments.aggregate(
                total=Sum('amount')
            )['total'] or 0

            # Completed payments
            completed_payments = all_payments.filter(status='completed')
            total_completed = completed_payments.aggregate(
                total=Sum('amount')
            )['total'] or 0

            # Counts by status
            completed_count = completed_payments.count()
            pending_count = all_payments.filter(status='pending').count()
            failed_count = all_payments.filter(status='failed').count()
            processing_count = all_payments.filter(status='processing').count()
            refunded_count = all_payments.filter(status='refunded').count()

            # Success rate
            success_rate = 0
            if all_payments.count() > 0:
                success_rate = (completed_count / all_payments.count()) * 100

            # Average transaction value
            avg_transaction = 0
            if all_payments.count() > 0:
                avg_transaction = total_amount / all_payments.count()

            # Get highest and lowest completed transactions
            highest_transaction = completed_payments.order_by('-amount').first()
            lowest_transaction = completed_payments.order_by('amount').first()

            return {
                'total_amount': float(total_amount),
                'total_completed': float(total_completed),
                'total_transactions': all_payments.count(),
                'completed_count': completed_count,
                'pending_count': pending_count,
                'failed_count': failed_count,
                'processing_count': processing_count,
                'refunded_count': refunded_count,
                'success_rate': round(success_rate, 1),
                'avg_transaction': float(avg_transaction),
                'highest_transaction': float(highest_transaction.amount) if highest_transaction else 0,
                'lowest_transaction': float(lowest_transaction.amount) if lowest_transaction else 0
            }
        except Exception as e:
            logger.error(f"Statistics calculation error: {str(e)}")
            return {}


class GetPaymentDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, payment_id):
        try:
            if not request.user.is_staff:
                return Response(
                    {'error': 'Unauthorized access'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            payment = Payment.objects.select_related('user', 'plan').get(id=payment_id)
            serializer = PaymentDetailSerializer(payment)
            return Response(serializer.data)

        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Get payment details error: {str(e)}")
            return Response(
                {'error': 'Failed to fetch payment details'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdatePaymentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        try:
            if not request.user.is_staff:
                return Response(
                    {'error': 'Unauthorized access'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            action = request.data.get('action')
            payment = Payment.objects.select_related('user', 'plan').get(id=payment_id)

            with transaction.atomic():
                if action == 'approve':
                    return self.approve_payment(payment)
                elif action == 'refund':
                    return self.refund_payment(payment, request.data.get('reason', ''))
                elif action == 'mark_failed':
                    return self.mark_failed(payment, request.data.get('reason', ''))
                else:
                    return Response(
                        {'error': 'Invalid action'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Update payment status error: {str(e)}")
            return Response(
                {'error': 'Failed to update payment status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def approve_payment(self, payment):
        """Approve a pending payment"""
        if payment.status != 'pending':
            return Response(
                {'error': 'Only pending payments can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.status = 'completed'
        payment.save()

        # Update user's premium status
        payment.user.is_premium = True
        payment.user.plan_type = payment.plan.plan_type if payment.plan else 'free'
        payment.user.save()

        # Create or update UserPlan
        user_plan, created = UserPlan.objects.get_or_create(
            user=payment.user,
            defaults={
                "plan": payment.plan,
                "is_active": True,
                "start_date": timezone.now(),
            }
        )
        if not created:
            user_plan.plan = payment.plan
            user_plan.is_active = True
            user_plan.start_date = timezone.now()
        user_plan.end_date = payment.end_date
        user_plan.save()

        return Response({
            'message': 'Payment approved successfully',
            'payment': PaymentSerializer(payment).data
        })

    def refund_payment(self, payment, reason):
        """Refund a completed payment"""
        if payment.status != 'completed':
            return Response(
                {'error': 'Only completed payments can be refunded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Here you would integrate with your payment gateway's refund API
        # For example, with Razorpay:
        # try:
        #     client.payment.refund(payment.gateway_payment_id, {
        #         "amount": int(payment.amount * 100),
        #         "speed": "normal",
        #         "notes": {
        #             "reason": reason,
        #             "refunded_by": self.request.user.email
        #         }
        #     })
        # except Exception as e:
        #     return Response({'error': f'Refund failed: {str(e)}'}, status=400)

        # For now, we'll just update the status
        payment.status = 'refunded'
        payment.save()

        # Update user's premium status if needed
        # Check if user has any other active payments
        active_payments = Payment.objects.filter(
            user=payment.user,
            status='completed'
        ).exclude(id=payment.id).exists()

        if not active_payments:
            payment.user.is_premium = False
            payment.user.plan_type = 'free'
            payment.user.save()

            # Deactivate UserPlan
            UserPlan.objects.filter(user=payment.user).update(is_active=False)

        return Response({
            'message': 'Payment refunded successfully',
            'payment': PaymentSerializer(payment).data
        })

    def mark_failed(self, payment, reason):
        """Mark a payment as failed"""
        if payment.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Only pending or processing payments can be marked as failed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.status = 'failed'
        payment.save()

        return Response({
            'message': 'Payment marked as failed',
            'payment': PaymentSerializer(payment).data
        })


class ExportPaymentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            if not request.user.is_staff:
                return Response(
                    {'error': 'Unauthorized access'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get filters from query params
            date_range = request.query_params.get('dateRange', '30d')
            status_filter = request.query_params.get('status', 'all')
            payment_method_filter = request.query_params.get('paymentMethod', 'all')
            search_term = request.query_params.get('search', '')

            # Calculate date range
            end_date = timezone.now()
            if date_range == '7d':
                start_date = end_date - timedelta(days=7)
            elif date_range == '30d':
                start_date = end_date - timedelta(days=30)
            elif date_range == '90d':
                start_date = end_date - timedelta(days=90)
            elif date_range == '1y':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = None

            # Base queryset
            queryset = Payment.objects.select_related('user', 'plan').order_by('-created_at')

            # Apply filters
            if start_date:
                queryset = queryset.filter(created_at__range=[start_date, end_date])
            if status_filter != 'all':
                queryset = queryset.filter(status=status_filter)
            if payment_method_filter != 'all':
                queryset = queryset.filter(payment_gateway=payment_method_filter)
            if search_term:
                queryset = queryset.filter(
                    Q(user__username__icontains=search_term) |
                    Q(user__email__icontains=search_term) |
                    Q(gateway_order_id__icontains=search_term) |
                    Q(plan__name__icontains=search_term)
                )

            # Serialize data
            serializer = PaymentSerializer(queryset, many=True)

            # Format for CSV/Excel
            export_data = []
            for payment in serializer.data:
                export_data.append({
                    'Transaction ID': payment.get('gateway_order_id', ''),
                    'User': payment.get('user', {}).get('username', ''),
                    'Email': payment.get('user', {}).get('email', ''),
                    'Plan': payment.get('plan', {}).get('name', ''),
                    'Amount': payment.get('amount', 0),
                    'Currency': payment.get('currency', 'INR'),
                    'Payment Method': payment.get('payment_gateway', ''),
                    'Status': payment.get('status', ''),
                    'Date': payment.get('created_at', ''),
                    'Gateway Payment ID': payment.get('gateway_payment_id', '')
                })

            return Response({
                'data': export_data,
                'total_records': len(export_data),
                'filters_applied': {
                    'date_range': date_range,
                    'status': status_filter,
                    'payment_method': payment_method_filter,
                    'search_term': search_term
                }
            })

        except Exception as e:
            logger.error(f"Export payments error: {str(e)}")
            return Response(
                {'error': 'Failed to export payments'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            if not request.user.is_staff:
                return Response(
                    {'error': 'Unauthorized access'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Time periods
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            year_ago = today - timedelta(days=365)

            # Total statistics
            total_payments = Payment.objects.all()
            completed_payments = total_payments.filter(status='completed')

            # Daily analytics (last 30 days)
            daily_data = completed_payments.filter(
                created_at__date__gte=month_ago
            ).extra({'date': "date(created_at)"}
            ).values('date').annotate(
                revenue=Sum('amount'),
                transactions=Count('id')
            ).order_by('date')

            # Monthly analytics (last 12 months)
            monthly_data = completed_payments.filter(
                created_at__date__gte=year_ago
            ).extra({'month': "strftime('%Y-%m', created_at)"}
            ).values('month').annotate(
                revenue=Sum('amount'),
                transactions=Count('id')
            ).order_by('month')

            # Payment method distribution
            method_distribution = completed_payments.values(
                'payment_gateway'
            ).annotate(
                count=Count('id'),
                revenue=Sum('amount')
            ).order_by('-revenue')

            # Plan distribution
            plan_distribution = completed_payments.filter(
                plan__isnull=False
            ).values(
                'plan__name'
            ).annotate(
                count=Count('id'),
                revenue=Sum('amount')
            ).order_by('-revenue')

            # Status distribution
            status_distribution = total_payments.values(
                'status'
            ).annotate(
                count=Count('id')
            )

            return Response({
                'daily_analytics': {
                    'labels': [item['date'].strftime('%Y-%m-%d') for item in daily_data],
                    'revenue': [float(item['revenue'] or 0) for item in daily_data],
                    'transactions': [item['transactions'] for item in daily_data]
                },
                'monthly_analytics': {
                    'labels': [item['month'] for item in monthly_data],
                    'revenue': [float(item['revenue'] or 0) for item in monthly_data],
                    'transactions': [item['transactions'] for item in monthly_data]
                },
                'method_distribution': [
                    {
                        'method': item['payment_gateway'],
                        'count': item['count'],
                        'revenue': float(item['revenue'] or 0),
                        'percentage': round((item['count'] / completed_payments.count()) * 100, 1) if completed_payments.count() > 0 else 0
                    }
                    for item in method_distribution
                ],
                'plan_distribution': [
                    {
                        'plan': item['plan__name'],
                        'count': item['count'],
                        'revenue': float(item['revenue'] or 0),
                        'percentage': round((item['count'] / completed_payments.count()) * 100, 1) if completed_payments.count() > 0 else 0
                    }
                    for item in plan_distribution
                ],
                'status_distribution': [
                    {
                        'status': item['status'],
                        'count': item['count'],
                        'percentage': round((item['count'] / total_payments.count()) * 100, 1) if total_payments.count() > 0 else 0
                    }
                    for item in status_distribution
                ]
            })

        except Exception as e:
            logger.error(f"Payment analytics error: {str(e)}")
            return Response(
                {'error': 'Failed to fetch payment analytics'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )