import requests
from django.conf import settings
import swisseph as swe

# Sarvam AI
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_API_KEY = settings.SARVAM_API_KEY


# ---------------------------------------------------
# 1️⃣ Speech-to-Text (Voice → Text)
# ---------------------------------------------------
def process_stt(audio_file):
    print("stt")

    url = "https://api.sarvam.ai/speech-to-text"

    headers = {
        "X-API-Key": settings.SARVAM_API_KEY
    }

    files = {
        "audio_file": ("audio.webm", audio_file, "audio/webm")   # ✅ correct name
    }

    print("stt sending...")

    res = requests.post(url, headers=headers, files=files)

    print("STT STATUS:", res.status_code)
    print("STT RESPONSE:", res.text)

    if res.status_code != 200:
        raise Exception("Sarvam STT Failed: " + res.text)

    return res.json().get("text")





# ---------------------------------------------------
# 2️⃣ Text → Voice (TTS)
# ---------------------------------------------------
def process_tts(text):
    url = "https://api.sarvam.ai/text-to-speech"

    headers = {
        "X-API-Key": settings.SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": text,
        "voice": "meera",
        "format": "mp3"
    }

    res = requests.post(url, headers=headers, json=payload)

    if res.status_code != 200:
        raise Exception("TTS Failed: " + res.text)

    return res.content




# ---------------------------------------------------
# 3️⃣ Astrology: Sidereal Longitude Calculator
# ---------------------------------------------------
def get_sidereal_longitude(jd_ut, planet):
    pos, ret = swe.calc_ut(jd_ut, planet)
    lon = pos[0]
    return lon
