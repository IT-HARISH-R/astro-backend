from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date
from .models import ZodiacPrediction
from .serializers import ZodiacPredictionSerializer ,LoveCalculatorSerializer , LoveResult , LoveResultSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny

class TodayPredictions(APIView):
    """
    GET => returns predictions for today's date (if exist). 
    If some signs missing, returns those as empty list (client can call regenerate).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        today = date.today()
        preds = ZodiacPrediction.objects.filter(date=today)
        serializer = ZodiacPredictionSerializer(preds, many=True)
        return Response({"date": str(today), "predictions": serializer.data})
 
class RegeneratePrediction(APIView):
    """
    POST with optional JSON: {"sign": "aries"} to regenerate single sign,
    or {"all": true} to regenerate all signs for today.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        today = date.today()
        sign = request.data.get("sign")
        regenerate_all = request.data.get("all", False)

        if sign:
            from .utils import generate_and_store_for_sign
            pred = generate_and_store_for_sign(sign, date_value=today, force=True)
            serializer = ZodiacPredictionSerializer(pred)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif regenerate_all:
            from .utils import generate_daily_predictions
            results = generate_daily_predictions(date_value=today, force=True)
            ser = ZodiacPredictionSerializer(results, many=True)
            return Response({"created": len(results), "predictions": ser.data}, status=status.HTTP_201_CREATED)
        else:
            return Response({"detail":"provide 'sign' or {'all':true}"}, status=status.HTTP_400_BAD_REQUEST)


class LoveCalculatorView(APIView):
    def post(self, request):
        serializer = LoveCalculatorSerializer(data=request.data)

        if serializer.is_valid():
            name1 = serializer.validated_data['name1'].strip().lower()
            name2 = serializer.validated_data['name2'].strip().lower()

            # Simple Love Calculation Logic 😄
            combined = name1 + name2
            score = (len(set(combined)) * 7) % 101

            if score > 80:
                msg = "Perfect Match 💞"
            elif score > 60:
                msg = "Good Compatibility 💕"
            elif score > 40:
                msg = "Average Match 💬"
            else:
                msg = "Needs more understanding 💔"

            # ✅ Save to Database
            love_result = LoveResult.objects.create(
                name1=name1.title(),
                name2=name2.title(),
                love_score=score,
                message=msg
            )

            result_serializer = LoveResultSerializer(love_result)

            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)