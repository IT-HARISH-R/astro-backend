from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Plan, UserPlan
from .serializers import PlanSerializer
from accounts.models import User
import razorpay
from django.conf import settings

# Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# -----------------------------
# 1. Get all plans
# -----------------------------
class PlanListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        plans = Plan.objects.all()
        serializer = PlanSerializer(plans, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 # -----------------------------
# 2. Plan Detail View
# -----------------------------   

class PlanDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_object(self, pk):
        try:
            return Plan.objects.get(pk=pk)
        except Plan.DoesNotExist:
            return None

    def get(self, request, pk):
        plan = self.get_object(pk)
        if not plan:
            return Response({"detail": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PlanSerializer(plan)
        return Response(serializer.data)

    def put(self, request, pk):
        """Full update"""
        plan = self.get_object(pk)
        if not plan:
            return Response({"detail": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PlanSerializer(plan, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Partial update"""
        plan = self.get_object(pk)
        if not plan:
            return Response({"detail": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PlanSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        plan = self.get_object(pk)
        if not plan:
            return Response({"detail": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)
        plan.delete()
        return Response({"detail": "Plan deleted"}, status=status.HTTP_204_NO_CONTENT)
    
    
# -----------------------------
# 3. Create Razorpay order
# -----------------------------
class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        if not plan_id:
            return Response({"error": "plan_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = Plan.objects.get(id=plan_id)
            amount = int(plan.price * 100)  # Convert to paise

            order = client.order.create({
                "amount": amount,
                "currency": "INR",
                "payment_capture": 1
            })

            # Return Razorpay key and order details to frontend
            return Response({
                "key": settings.RAZORPAY_KEY_ID,
                "order_id": order["id"],
                "amount": amount,
                "plan_id": plan_id
            }, status=status.HTTP_200_OK)

        except Plan.DoesNotExist:
            return Response({"error": "Invalid plan"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -----------------------------
# 4. Verify Razorpay payment
# -----------------------------
class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        razorpay_order_id = data.get("order_id")
        razorpay_payment_id = data.get("payment_id")
        razorpay_signature = data.get("signature")
        plan_id = data.get("plan_id")

        try:
            # Verify payment signature
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })

            # Save plan to user
            plan = Plan.objects.get(id=plan_id)
            user_plan, _ = UserPlan.objects.get_or_create(user=request.user)
            user_plan.plan = plan
            user_plan.is_active = True
            user_plan.save()

            # Update user premium flags
            user = request.user
            user.is_premium = plan.name.lower() == "premium"
            user.plan_type = plan.name
            user.save()

            return Response({"status": "Payment successful", "plan": plan.name}, status=status.HTTP_200_OK)

        except razorpay.errors.SignatureVerificationError:
            return Response({"status": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
