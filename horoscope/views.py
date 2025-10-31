from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import swisseph as swe
from datetime import datetime

class BirthChartView(APIView):
    """
    API endpoint to generate a birth (natal) chart using Swiss Ephemeris.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # 🧩 Extract user input
            name = request.data.get("name")
            date_of_birth = request.data.get("date_of_birth")  # YYYY-MM-DD
            time_of_birth = request.data.get("time_of_birth")  # HH:MM
            birthplace = request.data.get("birthplace")
            lat = float(request.data.get("latitude"))
            lon = float(request.data.get("longitude"))
            timezone_str = request.data.get("timezone", "+5:30")

            # 🕒 Handle timezone (convert to UTC)
            sign = 1 if timezone_str.startswith('+') else -1
            hours_offset = int(timezone_str[1:].split(':')[0])
            minutes_offset = int(timezone_str[1:].split(':')[1])
            total_offset = sign * (hours_offset + (minutes_offset / 60))

            dt_local = datetime.strptime(f"{date_of_birth} {time_of_birth}", "%Y-%m-%d %H:%M")
            jd_ut = swe.julday(dt_local.year, dt_local.month, dt_local.day, dt_local.hour - total_offset)

            # ♈ Zodiac signs
            zodiac_signs = [
                "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
            ]

            # ☉ Planet names
            planet_names = {
                swe.SUN: "Sun", swe.MOON: "Moon", swe.MERCURY: "Mercury", swe.VENUS: "Venus",
                swe.MARS: "Mars", swe.JUPITER: "Jupiter", swe.SATURN: "Saturn",
                swe.URANUS: "Uranus", swe.NEPTUNE: "Neptune", swe.PLUTO: "Pluto",
                swe.TRUE_NODE: "True Node"
            }

            # 🪐 Calculate planetary positions
            planets_data = []
            for pl_code, pl_name in planet_names.items():
                # ✅ Correct way to unpack Swiss Ephemeris result
                result, ret = swe.calc_ut(jd_ut, pl_code)
                lon_p = result[0]
                speed_lon = result[3]
                sign_index = int(lon_p / 30) % 12  # prevents index out of range

                planets_data.append({
                    "planet": pl_name,
                    "longitude": round(lon_p, 2),
                    "sign": zodiac_signs[sign_index],
                    "motion": "Retrograde" if speed_lon < 0 else "Direct"
                })

            # 🏠 Houses (Placidus)
            try:
                ascmc, cusps = swe.houses(jd_ut, lat, lon, b'P')
                houses = {f"House_{i+1}": round(cusps[i], 2) for i in range(12)}
                ascendant_degree = round(ascmc[0], 2)
                ascendant_sign = zodiac_signs[int(ascmc[0] / 30) % 12]
            except Exception as e:
                houses = {}
                ascendant_degree = None
                ascendant_sign = None

            # 🌞 Summary & simple interpretation
            summary = {
                "sun_sign": next((p["sign"] for p in planets_data if p["planet"] == "Sun"), None),
                "moon_sign": next((p["sign"] for p in planets_data if p["planet"] == "Moon"), None),
                "ascendant": ascendant_sign,
                "ascendant_degree": ascendant_degree,
                "interpretation": {
                    "personality": "Diplomatic and intuitive.",
                    "career": "Strong leadership and creativity.",
                    "love": "Emotionally expressive and loyal.",
                    "money": "Driven and confident in financial pursuits."
                }
            }

            # ✅ Success response
            return Response({
                "status": "success",
                "engine": "Swiss Ephemeris 2.10",
                "chart_type": "Natal Chart",
                "input_data": {
                    "name": name,
                    "date_of_birth": date_of_birth,
                    "time_of_birth": time_of_birth,
                    "birthplace": birthplace,
                    "latitude": lat,
                    "longitude": lon,
                    "timezone": timezone_str
                },
                "planetary_positions": planets_data,
                "house_cusps": houses,
                "summary": summary
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
