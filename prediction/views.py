from django.conf import settings
from .models import Prediction
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import swisseph as swe
from ai.serializers import GenerateTextSerializer
import google.generativeai as genai

# Set Lahiri Ayanamsa (Sidereal mode)
swe.set_sid_mode(swe.SIDM_LAHIRI)

logger = logging.getLogger(__name__)

def get_sidereal_longitude(jd_ut, planet):
    """Return sidereal longitude of a planet"""
    result, flags = swe.calc_ut(
        jd_ut,
        planet,
        swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    )
    return result[0]  # longitude

 
class AstroThanglishAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            # ---- Username from middleware ----
            username = getattr(request, "username", None)
            if username is None:
                return Response({"message": "No username found in request"}, status=401)

            # ---- Input data ----
            data = request.data
            year = int(data.get("year"))
            month = int(data.get("month"))
            day = int(data.get("day"))
            hour = int(data.get("hour"))
            minute = int(data.get("minute"))
            model_name = data.get("model") or "gemini-2.5-flash"

            # ---- Swiss Ephemeris calculation ----
            jd_ut = swe.julday(year, month, day, hour + minute / 60.0)
            sun_long = get_sidereal_longitude(jd_ut, swe.SUN)
            moon_long = get_sidereal_longitude(jd_ut, swe.MOON)

            # ---- Rasi calculation based on Moon longitude ----
            rasi_names = [
                "Mesham", "Rishabam", "Mithunam", "Kadagam", "Simmam", "Kanni",
                "Thulam", "Viruchigam", "Dhanusu", "Magaram", "Kumbam", "Meenam"
            ]
            rasi_index = int(moon_long // 30)
            moon_rasi = rasi_names[rasi_index]

            astrology_data = {
                "julian_day": jd_ut,
                "sun_longitude": sun_long,
                "moon_longitude": moon_long,
                "rasi": moon_rasi
            }

            # ---- Prompt (Rasi included) ----
            prompt = (
                f"IMPORTANT: Address the user by their name '{username}' in the astrology prediction. "
                "Generate ONLY the astrology prediction in Thanglish (Tamil + English mix). "
                "DO NOT include greetings, explanations, zodiac sign names, extra text, questions, or suggestions. "
                "ONLY provide the pure prediction content.\n\n"
                f"User Rasi: {moon_rasi}\n"
                "Astrology Data:\n"
                f"Julian Day: {astrology_data['julian_day']}\n"
                f"Sun Longitude: {astrology_data['sun_longitude']}\n"
                f"Moon Longitude: {astrology_data['moon_longitude']}\n\n"
                "Based on this data and the user's Rasi, provide ONLY the astrology prediction in Thanglish (Tamil + English mix). "
                "Keep it short and clear (maximum 8–10 lines). "
                "Start directly with the prediction, addressing the user by their name."
            )

            # ---- Serializer validation ----
            serializer = GenerateTextSerializer(data={"prompt": prompt, "model": model_name})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_prompt = serializer.validated_data["prompt"]

            # ---- Gemini setup ----
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                return Response({"error": "GEMINI_API_KEY not set in settings or environment"}, status=500)

            genai.configure(api_key=api_key)

            # ---- Generate content ----
            model_instance = genai.GenerativeModel(model_name)
            response = model_instance.generate_content(validated_prompt)

            # ---- Extract Gemini output ----
            text_output = getattr(response, "text", None)
            if not text_output:
                try:
                    candidates = getattr(response, "candidates", [])
                    if candidates and hasattr(candidates[0], "content"):
                        text_output = candidates[0].content.parts[0].text
                except Exception:
                    text_output = str(response)

            # ---- Validate user ----
            user = getattr(request, "user", None)
            if not user:
                return Response({"message": "User not found or unauthorized"}, status=401)

            # ---- Save prediction ----
            prediction = Prediction.objects.create(
                user=user,
                birth_year=year,
                birth_month=month,
                birth_day=day,
                birth_hour=hour,
                birth_minute=minute,
                julian_day=jd_ut,
                sun_longitude=sun_long,
                moon_longitude=moon_long,
                thanglish_explanation=text_output or "No output"
            )

            # ---- Response ----
            return Response(
                {
                    "username": username,
                    "astrology_data": astrology_data,
                    "thanglish_explanation": text_output or "No output"
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception("Error in AstroThanglishAPIView")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        #  prompt = (
        #         f"Based on the astrology data {astrology_data}, generate a 10-line prediction in Thanglish. "
        #         f"Return only the prediction text, no extra explanations or text. "
        #         f"Make it simple, readable, and focused on daily horoscope insights."
        #     )

        #  prompt = (
        #         "IMPORTANT: Give ONLY the astrology prediction in Thanglish. NO greetings, NO explanations, "
        #         "NO extra text, NO questions, NO suggestions. ONLY the pure prediction content.\n\n"
        #         "Astrology Data:\n"
        #         f"Julian Day: {astrology_data['julian_day']}\n"
        #         f"Sun Longitude: {astrology_data['sun_longitude']}\n"
        #         f"Moon Longitude: {astrology_data['moon_longitude']}\n\n"
        #         "Based on this data, provide ONLY the astrology prediction in Thanglish (Tamil+English mix). "
        #         "Keep it concise (8-10 lines maximum). Start directly with the prediction, no introductions."
        #     )

        #     prompt = f"""

        # Astrology calculation result: {astrology_data}
        
        # Generate exactly 8 to 10 short lines in Thanglish.
        # - Output la prediction lines mattum irukkanum. 
        # - No intro like "Here is your prediction" or "Sure". 
        # - No closing lines like "Thank you" or "Hope you like it". 
        # - Just the prediction lines only. 
        # - Each line should be simple, conversational, and easy to read.
        # """

        #     prompt = (
        #     f"Analyze the following sidereal planetary data for a birth moment: {astrology_data}. "
        #     f"You are a professional Vedic astrologer. "
        #     f"Provide a daily horoscope prediction/insight that is concise (maximum 10 lines of text). "
        #     f"The entire output must be written **strictly in Thanglish** (Tamil mixed with English). "
        #     f"**CRITICAL RULE:** The response MUST contain **ONLY** the prediction text. "
        #     f"Do NOT include any greetings, titles (e.g., 'Prediction:'), introduction, or concluding remarks."
        # )