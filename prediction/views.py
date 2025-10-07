from django.conf import settings
import jwt 
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
    permission_classes = [AllowAny]  # keep as-is if route should still be public

    def _get_token_from_header(self, request):
        auth = request.headers.get("Authorization", "") or request.META.get("HTTP_AUTHORIZATION", "")
        if auth.startswith("Bearer "):
            return auth.split(" ", 1)[1].strip()
        return None

    def _username_from_request_user(self, request):
        try:
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                return getattr(user, "username", None) or getattr(user, "email", None)
        except Exception:
            pass
        return None

    def _decode_jwt_hs256(self, token):
        try:
            # Verify signature using your Django SECRET_KEY (only if token signed by you)
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            # Common claims: 'username', 'sub', 'email', 'preferred_username'
            return payload.get("username") or payload.get("preferred_username") or payload.get("email") or payload.get("sub")
        except jwt.InvalidTokenError:
            return None

    def _unsafe_read_jwt(self, token):
        # Use only as last-resort for logging/display. Do NOT use for auth decisions.
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("username") or payload.get("preferred_username") or payload.get("email") or payload.get("sub")
        except Exception:
            return None

    def post(self, request, *args, **kwargs):
        try:
            # --- your existing input parsing and calculations here ---
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

            # ---- NEW: get username from different sources ----
            username = self._username_from_request_user(request)  # best if DRF auth used

            if not username:
                token = self._get_token_from_header(request)
                if token:
                    # try verify with HS256 and SECRET_KEY (if token issued by your server)
                    username = self._decode_jwt_hs256(token)

                if not username and token:
                    # last resort: read payload without verifying signature (for display only)
                    username = self._unsafe_read_jwt(token)
                    if username:
                        logger.warning("Using unsafe token read (no signature verification) to extract username.")

            if username:
                logger.info(f"Username extracted for request: {username}")
            else:
                logger.info("No username found in request or token.")

            # ---- rest of your prompt + Gemini call as before ----
            prompt = (
                "IMPORTANT: Give ONLY the astrology prediction in Thanglish. NO greetings, NO explanations, "
                "NO extra text, NO questions, NO suggestions. ONLY the pure prediction content.\n\n"
                "Astrology Data:\n"
                f"Julian Day: {astrology_data['julian_day']}\n"
                f"Sun Longitude: {astrology_data['sun_longitude']}\n"
                f"Moon Longitude: {astrology_data['moon_longitude']}\n\n"
                "Based on this data, provide ONLY the astrology prediction in Thanglish (Tamil+English mix). "
                "Keep it concise (8-10 lines maximum). Start directly with the prediction, no introductions."
            )

            # serializer validation and Gemini call (same as your code)...
            serializer = GenerateTextSerializer(data={"prompt": prompt, "model": model})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            validated_prompt = serializer.validated_data["prompt"]

            api_key = settings.GEMINI_API_KEY
            if not api_key:
                return Response({"error": "GEMINI_API_KEY not set in settings or environment"}, status=500)

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=model, contents=validated_prompt)

            # extract text_output same as before
            text_output = getattr(response, "text", None)
            if not text_output:
                try:
                    cand = response.get("candidates", [])
                    if cand and isinstance(cand, list):
                        text_output = cand[0].get("content") or cand[0].get("output") or str(cand[0])
                except Exception:
                    text_output = str(response)

            # Return username (if any) for debugging / display
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