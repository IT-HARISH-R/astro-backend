import os
from datetime import date, datetime
import swisseph as swe
from django.conf import settings
from .models import ZodiacPrediction

# ZODIAC SIGNS (keys)
ZODIAC_SIGNS = [
    "aries","taurus","gemini","cancer","leo","virgo",
    "libra","scorpio","sagittarius","capricorn","aquarius","pisces"
]

# Map to nice names
ZODIAC_DISPLAY = {
    "aries":"Aries","taurus":"Taurus","gemini":"Gemini","cancer":"Cancer","leo":"Leo",
    "virgo":"Virgo","libra":"Libra","scorpio":"Scorpio","sagittarius":"Sagittarius",
    "capricorn":"Capricorn","aquarius":"Aquarius","pisces":"Pisces"
}


def _get_basic_astronomy_info(target_date=None):
    """Compute Sun/Moon positions and moon phase angle using Swiss Ephemeris."""
    if target_date is None:
        target_date = date.today()

    dt = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)
    sun = swe.calc_ut(jd, swe.SUN)
    moon = swe.calc_ut(jd, swe.MOON)
    sun_long = float(sun[0][0]) if sun and sun[0] else None
    moon_long = float(moon[0][0]) if moon and moon[0] else None

    phase_angle = None
    if sun_long is not None and moon_long is not None:
        phase_angle = abs(moon_long - sun_long) % 360

    return {
        "jd": jd,
        "sun_longitude": sun_long,
        "moon_longitude": moon_long,
        "moon_phase_angle": phase_angle
    }

def call_ai_for_prediction(sign_display_name, sign_key, source_data):
    import google.generativeai as genai
    import os
    from django.conf import settings

    model_name = "gemini-2.5-flash"
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY env var.")

    genai.configure(api_key=api_key)


    prompt = f"""
    Act as a professional astrology writer. 
    Write today's horoscope for the zodiac sign **{sign_display_name}** (date: {source_data.get('date')}).
    Follow these exact rules carefully:

    1. Write ONLY the prediction content — do NOT explain, translate, or add any system or AI text.
    2. Write naturally like a daily horoscope column (maximum 15 lines).
    3. Start directly with the theme of the day. Do not start with "Here is your horoscope" or any greeting.
    4. Include these parts naturally within the horoscope:
    - A clear overall theme or mood for the day.
    - One short hint about love, work, or money.
    - One practical tip or advice for the sign.
    5. The tone should be warm, positive, and easy to understand for everyone.
    6. Do not repeat sentences or use generic filler lines.
    7. Avoid mentioning planets, sun, or moon data directly.
    8. Output only the horoscope text (no quotes, no labels, no bullet points).

    Astrological context (for your internal reference only):
    Sun longitude: {source_data.get('sun_longitude')}
    Moon phase angle: {source_data.get('moon_phase_angle')}
    """


    try:
        # ✅ Correct modern method
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        # get output text safely
        text = response.text.strip() if hasattr(response, "text") else str(response)
        return text, prompt

    except Exception as e:
        raise RuntimeError(f"AI generation failed: {e}")


def generate_and_store_for_sign(sign_key, date_value=None, force=False):
    """Generate and store prediction for one zodiac sign."""
    if date_value is None:
        date_value = date.today()

    existing = ZodiacPrediction.objects.filter(sign=sign_key, date=date_value).first()
    if existing and not force:
        return existing

    astro = _get_basic_astronomy_info(target_date=date_value)
    astro["date"] = str(date_value)

    sign_display = ZODIAC_DISPLAY.get(sign_key, sign_key.title())

    pred_text, prompt = call_ai_for_prediction(sign_display, sign_key, astro)

    obj, created = ZodiacPrediction.objects.update_or_create(
        sign=sign_key,
        date=date_value,
        defaults={
            "prediction_text": pred_text,
            "ai_prompt": prompt,
            "source_data": astro,
        }
    )
    return obj


def generate_daily_predictions(date_value=None, force=False):
    """Generate and store predictions for all 12 signs."""
    if date_value is None:
        date_value = date.today()

    results = []
    import logging
    for s in ZODIAC_SIGNS:
        try:
            obj = generate_and_store_for_sign(s, date_value=date_value, force=force)
            results.append(obj)
        except Exception as e:
            logging.exception("Failed for sign %s: %s", s, e)
            continue

    return results
