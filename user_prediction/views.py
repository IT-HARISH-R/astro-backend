import io
from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from groq import Groq
from rest_framework.response import Response
import swisseph as swe
from .services import get_sidereal_longitude
import google.generativeai as genai
from django.conf import settings

from gtts import gTTS
import uuid
import os
import time

from .models import ChatRoom, ChatMessage


client = Groq(api_key=settings.GROQ_API_KEY)


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

from rest_framework.generics import ListAPIView
from .models import ChatRoom, ChatMessage
from .serializers import ChatRoomSerializer, ChatMessageSerializer

class ChatListView(ListAPIView):
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        return ChatRoom.objects.filter(user=self.request.user).order_by('-created_at')


class ChatMessageListView(ListAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        return ChatMessage.objects.filter(chat__id=chat_id, chat__user=self.request.user).order_by('created_at')
    

from rest_framework.generics import DestroyAPIView

class ChatDeleteView(DestroyAPIView):
    def get_queryset(self):
        return ChatRoom.objects.filter(user=self.request.user)

class VoiceAIView(APIView):

    def post(self, request):
        user = request.user
        birth_place = user.birth_place

        # Optional birthplace string
        birth_place_text = f"- Birth Place: {birth_place}\n" if birth_place else ""


        audio_file = request.FILES.get('audio')
        text_input = request.data.get('text')
        print(request.data)
        # ---------------------------
        # CASE 1: TEXT INPUT
        # ---------------------------
        if text_input:
            user_text = text_input
            print("User typed:", user_text)

        # ---------------------------
        # CASE 2: AUDIO INPUT
        # ---------------------------
        elif audio_file:
            try:
                audio_bytes = audio_file.read()

                transcript = client.audio.transcriptions.create(
                    file=("audio.webm", audio_bytes),
                    model="whisper-large-v3",
                    language="ta"
                )
                user_text = transcript.text
                print("User said:", user_text)

            except Exception as e:
                return JsonResponse({"error": f"STT Error: {str(e)}"}, status=500)

        else:
            return JsonResponse({"error": "No text or audio provided"}, status=400)

        # --------------------------------------
        # STEP 2: Astrology Calculation
        # --------------------------------------
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

        # --------------------------------------
        # STEP 3: Gemini AI Prompt
        # --------------------------------------
        # IMPORTANT: Address the user as '{user.username}'.
        prompt = f"""
            Return astrology prediction in Tamil.

            User asked: "{user_text}"

            User Details:
            - Birth: {birth_day}/{birth_month}/{birth_year} {birth_hour}:{birth_minute}
            - Moon Rasi: {moon_rasi}
            {birth_place_text}
            Make the prediction simple, short, clear.
            Give only 6–10 lines, no intro, no ending lines.
        """

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        ai_text = response.text

        # --------------------------------------
        # STEP 4: TTS
        # --------------------------------------
        tts_folder = os.path.join("media", "tts")
        os.makedirs(tts_folder, exist_ok=True)

        delete_old_tts_files(tts_folder, seconds=600)

        tts_filename = f"tts_{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(tts_folder, tts_filename)

        tts = gTTS(text=ai_text, lang='ta')
        tts.save(file_path)

        tts_url = request.build_absolute_uri("/media/tts/" + tts_filename)

        # --------------------------------------
        # STEP 5: CHAT HISTORY
        # --------------------------------------
        chat_id = request.data.get("chat_id")

        if chat_id:
            try:
                chat_room = ChatRoom.objects.get(id=chat_id, user=user)
            except ChatRoom.DoesNotExist:
                chat_room = ChatRoom.objects.create(user=user, title="New Chat")
        else:
            chat_room = ChatRoom.objects.create(user=user, title="New Astrology Chat")

        ChatMessage.objects.create(
            chat=chat_room,
            user_text=user_text,
            ai_text=ai_text,
            tts_url=tts_url
        )

        return Response({
            "chat_id": chat_room.id,
            "message": user_text,
            "prediction": ai_text,
            "tts_audio_url": tts_url,
            "dev testing":prompt
        })
