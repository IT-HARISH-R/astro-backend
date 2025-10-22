from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
import razorpay
from django.conf import settings
from accounts.models import User
from .models import Payment

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount = 1000 * 100  # 1000 INR in paise
        order = client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})
        
        Payment.objects.create(
            user=request.user,
            razorpay_order_id=order['id'],
            amount=amount,
        )
        return Response({'order_id': order['id'], 'amount': amount})

class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        razorpay_order_id = data.get('order_id')
        razorpay_payment_id = data.get('payment_id')
        razorpay_signature = data.get('signature')

        # Verify signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        try:
            client.utility.verify_payment_signature(params_dict)
            # Update user
            user = request.user
            user.is_premium = True
            user.plan_type = 'premium'
            user.save()

            # Update payment record
            payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = 'paid'
            payment.save()

            return Response({'status': 'Payment successful', 'plan': user.plan_type})
        except:
            return Response({'status': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
