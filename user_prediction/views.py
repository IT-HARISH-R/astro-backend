import io
from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from groq import Groq
from rest_framework.response import Response
import swisseph as swe
from .services import process_stt, process_tts, get_sidereal_longitude
import google.generativeai as genai
from django.conf import settings

from gtts import gTTS
import uuid
import os
import time

client = Groq(api_key=settings.GROQ_API_KEY)  # put your key here
# api_key = settings.GROQ_API_KEY




def delete_old_tts_files(folder, seconds=86400):
    """Delete TTS files older than given seconds (default: 24 hours)."""
    now = time.time()

    if not os.path.exists(folder):
        return

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)

        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > seconds:
                os.remove(file_path)
                print("🗑️ Deleted old TTS file:", filename)


class VoiceAIView(APIView):

    def post(self, request):
        user = request.user
        print(request.FILES)
        print(request.data)
        audio_file = request.FILES.get('audio')

        if not audio_file:
            return JsonResponse({"error": "No audio provided"}, status=400)

        audio_bytes = audio_file.read()

        try:
            # ------------------ STEP 1: STT -----------------
            transcript = client.audio.transcriptions.create(
                file=("audio.webm", audio_bytes),
                model="whisper-large-v3",
                language="ta"
            )
            user_text = transcript.text
            print("Test<<", user_text)

            # ------------------ STEP 2: Astrology -------------
            birth_year = user.birth_year
            birth_month = user.birth_month
            birth_day = user.birth_day
            birth_hour = user.birth_hour
            birth_minute = user.birth_minute

            jd_ut = swe.julday(
                birth_year, birth_month, birth_day,
                birth_hour + birth_minute / 60
            )

            sun_long = get_sidereal_longitude(jd_ut, swe.SUN)
            moon_long = get_sidereal_longitude(jd_ut, swe.MOON)

            rasi_names = [
                "Mesham", "Rishabam", "Mithunam", "Kadagam", "Simmam", "Kanni",
                "Thulam", "Viruchigam", "Dhanusu", "Magaram", "Kumbam", "Meenam"
            ]
            moon_rasi = rasi_names[int(moon_long // 30)]

            # ------------------ STEP 3: Gemini Prompt -------------
            prompt = f"""
                IMPORTANT: Address the user as '{user.username}'.
                Return astrology prediction in tamil.

                User asked: "{user_text}"

                User Details:
                - Birth: {birth_day}/{birth_month}/{birth_year} {birth_hour}:{birth_minute}
                - Moon Rasi: {moon_rasi}

                Make prediction simple, short, clear.
                Give only 6–10 lines, no intro, no ending lines.
            """

            api_key = settings.GEMINI_API_KEY
            genai.configure(api_key=api_key)

            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            ai_text = response.text

            # ------------------ STEP 4: TTS (gTTS) -------------
            tts_folder = os.path.join("media", "tts")
            os.makedirs(tts_folder, exist_ok=True)

            # 🔥 Auto delete old TTS files (older than 24 hours)
            delete_old_tts_files(tts_folder, seconds=600)

            tts_filename = f"tts_{uuid.uuid4().hex}.mp3"
            file_path = os.path.join(tts_folder, tts_filename)

            tts = gTTS(text=ai_text, lang='ta')
            tts.save(file_path)

            # ------------------ RESPONSE ------------------------
            return Response({
                "message": user_text,
                "prediction": ai_text,
                "tts_audio_url": request.build_absolute_uri("/media/tts/" + tts_filename)
            })

        except Exception as e:
            return JsonResponse({"error": f"STT Error: {str(e)}"}, status=500)