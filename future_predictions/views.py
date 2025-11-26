# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import google.generativeai as genai
import swisseph as swe
from django.utils import timezone
from datetime import timedelta

from .models import FuturePrediction

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


class FuturePredictionView(APIView):

    def post(self, request):
        try:
            user = request.user

            # -------------------------------------
            # 1. CHECK IF OLD PREDICTION EXISTS
            # -------------------------------------
            old_prediction = FuturePrediction.objects.filter(user=user).order_by('-created_at').first()

            if old_prediction and old_prediction.is_valid():
                return Response({
                    "name": user.username,
                    "future_prediction": old_prediction.prediction_text,
                    "planetary_data": old_prediction.planetary_data,
                    "birth_details": old_prediction.birth_details,
                    "generated_at": old_prediction.created_at.isoformat(),
                    "status": "old_cached_data"
                })

            # -------------------------------------
            # VALIDATE USER BIRTH DETAILS
            # -------------------------------------
            if not all([
                user.birth_year,
                user.birth_month,
                user.birth_day,
                user.birth_hour is not None,
                user.birth_minute is not None,
                user.birth_place
            ]):
                return Response({
                    "error": "User birth details are incomplete. Please update your profile."
                }, status=400)

            # -------------------------------------
            # BIRTH DETAILS
            # -------------------------------------
            name = user.username
            year = user.birth_year
            month = user.birth_month
            day = user.birth_day
            hour = user.birth_hour
            minute = user.birth_minute
            place = user.birth_place

            # -------------------------------------
            # ASTRO DATA
            # -------------------------------------
            jd = swe.julday(year, month, day, hour + minute / 60)
            planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
            astro_data = {}

            for i in range(0, 7):
                result = swe.calc_ut(jd, i)
                lon = float(result[0][0])
                astro_data[planets[i]] = round(lon, 6)

            # -------------------------------------
            # PROMPT
            # -------------------------------------
            dob_formatted = f"{year}-{month}-{day}"
            time_formatted = f"{hour}:{minute}"

            prompt = f"""
            You are an expert Vedic astrologer AI. Using the precise planetary longitudes calculated from 
            the user's birth details, create a comprehensive and accurate future prediction for the next 1 year.

            ### User Birth Details:
            - Name: {name}
            - Birth Date: {dob_formatted } 
            - Birth Time: {time_formatted}
            - Birth Place: {place}

            ### Planetary Longitudes:
            {astro_data}

            ### Required Structure:

            **Career & Professional Life**
            (Detailed analysis with timing)

            **Relationships & Personal Life**
            (Detailed analysis with timing)

            **Finance & Wealth**
            (Income, expenses, investments, wealth growth)

            **Health & Wellbeing**
            (Physical, emotional, mental)

            **Key Opportunities**
            - Opportunity with timing
            - Opportunity with timing
            - Opportunity with timing

            **Important Considerations**
            - Key note 1
            - Key note 2
            - Key note 3

            **3 Actionable Suggestions**
            1. Practical and specific suggestion
            2. Practical and specific suggestion
            3. Practical and specific suggestion

            ### Guidelines:
            - Positive but realistic tone
            - Include timing (months/quarters)
            - Use Vedic astrology principles
            - Provide practical, actionable advice
            - Cover challenges + opportunities
            """
            response = model.generate_content(prompt)
            ai_text = response.text

            # -------------------------------------
            # 3. SAVE NEW PREDICTION IN DATABASE
            # -------------------------------------
            new_record = FuturePrediction.objects.create(
                user=user,
                prediction_text=ai_text,
                planetary_data=astro_data,
                birth_details={
                    "date": dob_formatted,
                    "time": time_formatted,
                    "place": place
                }
            )

            return Response({
                "name": name,
                "future_prediction": ai_text,
                "planetary_data": astro_data,
                "birth_details": new_record.birth_details,
                "generated_at": new_record.created_at.isoformat(),
                "status": "new_generated"
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)
