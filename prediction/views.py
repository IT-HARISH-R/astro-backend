from django.conf import settings
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import swisseph as swe
from ai.serializers import GenerateTextSerializer
from google import genai

# Sidereal mode (Lahiri)
swe.set_sid_mode(swe.SIDM_LAHIRI)

def get_sidereal_longitude(jd_ut, planet):
    """Return sidereal longitude of a planet"""
    result, flags = swe.calc_ut(
        jd_ut,
        planet,
        swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    )
    return result[0]  # longitude

logger = logging.getLogger(__name__)

class AstroThanglishAPIView(APIView):
    permission_classes = [AllowAny]  # Public route

    def post(self, request, *args, **kwargs):


        try:
            # ---- Username comes from middleware ----
            username = getattr(request, "username", None)
            if username is None:
                return Response({"message": "No username found in request"}, status=401)
            

            # --- Input parsing ---
            data = request.data
            year = int(data.get("year"))
            month = int(data.get("month"))
            day = int(data.get("day"))
            hour = int(data.get("hour"))
            minute = int(data.get("minute"))
            model = data.get("model") or "gemini-2.5-flash"

            jd_ut = swe.julday(year, month, day, hour + minute/60.0)
            sun_long = get_sidereal_longitude(jd_ut, swe.SUN)
            moon_long = get_sidereal_longitude(jd_ut, swe.MOON)

            astrology_data = {
                "julian_day": jd_ut,
                "sun_longitude": sun_long,
                "moon_longitude": moon_long
            }



            # ---- Gemini prompt ----
            prompt = (
                f"IMPORTANT: Address the user by their name '{username}' in the astrology prediction. "
                "Give ONLY the astrology prediction in Thanglish. NO greetings, NO explanations, "
                "NO extra text, NO questions, NO suggestions. ONLY the pure prediction content.\n\n"
                "Astrology Data:\n"
                f"Julian Day: {astrology_data['julian_day']}\n"
                f"Sun Longitude: {astrology_data['sun_longitude']}\n"
                f"Moon Longitude: {astrology_data['moon_longitude']}\n\n"
                "Based on this data, provide ONLY the astrology prediction in Thanglish (Tamil+English mix). "
                "Keep it concise (8-10 lines maximum). Start directly with the prediction, addressing the user by name."
            )

            serializer = GenerateTextSerializer(data={"prompt": prompt, "model": model})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            validated_prompt = serializer.validated_data["prompt"]

            api_key = settings.GEMINI_API_KEY
            if not api_key:
                return Response({"error": "GEMINI_API_KEY not set in settings or environment"}, status=500)

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=model, contents=validated_prompt)

            # Extract text_output
            text_output = getattr(response, "text", None)
            if not text_output:
                try:
                    cand = response.get("candidates", [])
                    if cand and isinstance(cand, list):
                        text_output = cand[0].get("content") or cand[0].get("output") or str(cand[0])
                except Exception:
                    text_output = str(response)

            return Response(
                {
                    "username": username,
                    "astrology_data": astrology_data,
                    "thanglish_explanation": text_output
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