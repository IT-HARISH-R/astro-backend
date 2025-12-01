from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Plan, Subscription, Payment, UserPlanFeature
from .serializers import (
    PlanSerializer, SubscriptionSerializer, CreateSubscriptionSerializer,
    PaymentSerializer, UserPlanFeatureSerializer, UserSubscriptionSummarySerializer
)

logger = logging.getLogger(__name__)

class PlanListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            plans = Plan.objects.filter(is_active=True)
            serializer = PlanSerializer(plans, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching plans: {str(e)}")
            return Response(
                {'error': 'Failed to fetch plans'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = CreateSubscriptionSerializer(
                data=request.data, 
                context={'request': request}
            )
            
            if serializer.is_valid():
                plan = serializer.validated_data['plan']
                
                # Create subscription
                subscription = Subscription.objects.create(
                    user=request.user,
                    plan=plan,
                    amount_paid=plan.price,
                    payment_method=serializer.validated_data.get('payment_method', 'card'),
                    status='pending'
                )
                
                # For demo purposes, auto-activate the subscription
                # In production, this would happen after successful payment
                subscription.status = 'active'
                subscription.save()
                
                # Create initial payment record
                Payment.objects.create(
                    subscription=subscription,
                    amount=plan.price,
                    payment_method=serializer.validated_data.get('payment_method', 'card'),
                    status='completed'
                )
                
                # Add plan features to user
                self._add_plan_features(request.user, plan)
                
                return Response(
                    SubscriptionSerializer(subscription).data,
                    status=status.HTTP_201_CREATED
                )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Subscription error: {str(e)}")
            return Response(
                {'error': 'Failed to create subscription'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _add_plan_features(self, user, plan):
        """Add plan-specific features to user"""
        features_map = {
            'basic': [
                {'name': 'daily_horoscope', 'value': {'limit': 1, 'used': 0}},
                {'name': 'basic_predictions', 'value': {'limit': 5, 'used': 0}},
            ],
            'premium': [
                {'name': 'daily_horoscope', 'value': {'limit': 3, 'used': 0}},
                {'name': 'future_predictions', 'value': {'limit': 20, 'used': 0}},
                {'name': 'kundli_analysis', 'value': {'limit': 5, 'used': 0}},
            ],
            'enterprise': [
                {'name': 'daily_horoscope', 'value': {'limit': 10, 'used': 0}},
                {'name': 'future_predictions', 'value': {'limit': 100, 'used': 0}},
                {'name': 'kundli_analysis', 'value': {'limit': 20, 'used': 0}},
                {'name': 'priority_support', 'value': {'enabled': True}},
            ]
        }
        
        # Remove existing features
        UserPlanFeature.objects.filter(user=user).delete()
        
        # Add new features based on plan
        features = features_map.get(plan.plan_type, [])
        for feature in features:
            UserPlanFeature.objects.create(
                user=user,
                feature_name=feature['name'],
                feature_value=feature['value']
            )

class UserSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            serializer = UserSubscriptionSummarySerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching user subscription: {str(e)}")
            return Response(
                {'error': 'Failed to fetch subscription details'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, subscription_id):
        try:
            subscription = Subscription.objects.get(
                id=subscription_id, 
                user=request.user
            )
            
            if subscription.status == 'active':
                subscription.status = 'canceled'
                subscription.auto_renew = False
                subscription.save()
                
                # Remove plan features
                UserPlanFeature.objects.filter(user=request.user).delete()
                
                return Response(
                    {'message': 'Subscription canceled successfully'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Subscription is not active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'Subscription not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Cancel subscription error: {str(e)}")
            return Response(
                {'error': 'Failed to cancel subscription'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Admin Views
class SubscriptionListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            subscriptions = Subscription.objects.all()
            serializer = SubscriptionSerializer(subscriptions, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching subscriptions: {str(e)}")
            return Response(
                {'error': 'Failed to fetch subscriptions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PaymentListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            payments = Payment.objects.all()
            serializer = PaymentSerializer(payments, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching payments: {str(e)}")
            return Response(
                {'error': 'Failed to fetch payments'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PlanManagementView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = PlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, plan_id):
        try:
            plan = Plan.objects.get(id=plan_id)
            serializer = PlanSerializer(plan, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Plan.DoesNotExist:
            return Response(
                {'error': 'Plan not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )