from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
import razorpay
from django.utils import timezone


from .models import Plan, UserPlan, Payment
from .serializers import PlanSerializer

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# -----------------------------
# 1. Get all plans / Create Plan
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
# 2. Plan Detail CRUD
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
        plan = self.get_object(pk)
        serializer = PlanSerializer(plan, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        plan = self.get_object(pk)
        serializer = PlanSerializer(plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        plan = self.get_object(pk)
        plan.delete()
        return Response({"detail": "Plan deleted"}, status=status.HTTP_204_NO_CONTENT)


# -----------------------------
# 3. Create Razorpay Order
# -----------------------------
class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")

        try:
            plan = Plan.objects.get(id=plan_id)
            amount = int(plan.price * 100)

            # Create Razorpay Order
            order = client.order.create({"amount": amount, "currency": "INR", "payment_capture": 1})

            # Save Payment Object
            payment = Payment.objects.create(
                user=request.user,
                plan=plan,
                amount=plan.price,
                currency="INR",
                gateway_order_id=order["id"],
                status="pending"
            )

            return Response({
                "key": settings.RAZORPAY_KEY_ID,
                "order_id": order["id"],
                "amount": amount,
                "plan_id": plan.id
            })

        except Plan.DoesNotExist:
            return Response({"error": "Invalid plan"}, status=404)


# -----------------------------
# 4. Verify Razorpay Payment
# -----------------------------
class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data

        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": data["order_id"],
                "razorpay_payment_id": data["payment_id"],
                "razorpay_signature": data["signature"]
            })

            plan = Plan.objects.get(id=data["plan_id"])
            payment = Payment.objects.get(gateway_order_id=data["order_id"])

            # Update payment entry
            payment.gateway_payment_id = data["payment_id"]
            payment.gateway_signature = data["signature"]
            payment.status = "completed"
            payment.save()

            # Create/Update UserPlan
            user_plan, created = UserPlan.objects.get_or_create(user=request.user)
            user_plan.plan = plan
            user_plan.is_active = True
            user_plan.start_date = timezone.now()
            user_plan.set_end_date()
            user_plan.save()

            # User Flags
            user = request.user
            user.is_premium = True
            user.plan_type = plan.plan_type
            user.save()

            return Response({"status": "Payment successful", "plan": plan.name})

        except razorpay.errors.SignatureVerificationError:
            return Response({"status": "Payment verification failed"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
