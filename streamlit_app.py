import streamlit as st
from groq import Groq
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import folium
from streamlit_folium import st_folium
from urllib.parse import quote
import math
import re
import hashlib
import json
import os

# ====================== CONFIG ======================
GROQ_API_KEY = None

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not GROQ_API_KEY:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    GROQ_API_KEY = "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"  # temporary

if not GROQ_API_KEY:
    st.error("❌ GROQ_API_KEY is missing. Please set it in `.streamlit/secrets.toml`")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

WHATSAPP_NUMBER = "919876543210"
PHONE_NUMBER = "+919876543210"

# ====================== SUPPORTED LANGUAGES ======================
SUPPORTED_LANGUAGES = {
    "English": {
        "code": "en",
        "whisper": "en",
        "tts": "en-IN",
        "speech_recognition": "en-IN",
        "name": "English"
    },
    "Hindi": {
        "code": "hi",
        "whisper": "hi",
        "tts": "hi-IN",
        "speech_recognition": "hi-IN",
        "name": "हिन्दी"
    },
    "Tamil": {
        "code": "ta",
        "whisper": "ta",
        "tts": "ta-IN",
        "speech_recognition": "ta-IN",
        "name": "தமிழ்"
    },
    "Telugu": {
        "code": "te",
        "whisper": "te",
        "tts": "te-IN",
        "speech_recognition": "te-IN",
        "name": "తెలుగు"
    },
    "Malayalam": {
        "code": "ml",
        "whisper": "ml",
        "tts": "ml-IN",
        "speech_recognition": "ml-IN",
        "name": "മലയാളം"
    },
    "Kannada": {
        "code": "kn",
        "whisper": "kn",
        "tts": "kn-IN",
        "speech_recognition": "kn-IN",
        "name": "ಕನ್ನಡ"
    },
    "Marathi": {
        "code": "mr",
        "whisper": "mr",
        "tts": "mr-IN",
        "speech_recognition": "mr-IN",
        "name": "मराठी"
    },
    "Gujarati": {
        "code": "gu",
        "whisper": "gu",
        "tts": "gu-IN",
        "speech_recognition": "gu-IN",
        "name": "ગુજરાતી"
    },
    "Bengali": {
        "code": "bn",
        "whisper": "bn",
        "tts": "bn-IN",
        "speech_recognition": "bn-IN",
        "name": "বাংলা"
    },
}

LOCATIONS = {
    "kochi": {"lat": 9.9312, "lon": 76.2673, "name": "Kochi", "harbour_name": "Cochin Fisheries Harbour", "harbour_lat": 9.9402, "harbour_lon": 76.2598, "coast": "west"},
    "cochin": {"lat": 9.9312, "lon": 76.2673, "name": "Kochi", "harbour_name": "Cochin Fisheries Harbour", "harbour_lat": 9.9402, "harbour_lon": 76.2598, "coast": "west"},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "name": "Mumbai", "harbour_name": "Sassoon Docks Harbour", "harbour_lat": 18.9167, "harbour_lon": 72.8258, "coast": "west"},
    "chennai": {"lat": 13.0827, "lon": 80.2707, "name": "Chennai", "harbour_name": "Kasimedu Fishing Harbour", "harbour_lat": 13.1250, "harbour_lon": 80.2985, "coast": "east"},
    "goa": {"lat": 15.2993, "lon": 74.1240, "name": "Goa", "harbour_name": "Mormugao / Betul Fishing Harbour", "harbour_lat": 15.4124, "harbour_lon": 73.8052, "coast": "west"},
    "visakhapatnam": {"lat": 17.6868, "lon": 83.2185, "name": "Visakhapatnam", "harbour_name": "Vizag Fishing Harbour", "harbour_lat": 17.6980, "harbour_lon": 83.2982, "coast": "east"},
    "mangalore": {"lat": 12.9141, "lon": 74.8560, "name": "Mangalore", "harbour_name": "Old Mangalore Bunder Port", "harbour_lat": 12.8584, "harbour_lon": 74.8351, "coast": "west"},
    "tuticorin": {"lat": 8.7642, "lon": 78.1348, "name": "Tuticorin", "harbour_name": "Thoothukudi Fishing Harbour", "harbour_lat": 8.8052, "harbour_lon": 78.1630, "coast": "east"},
    "pondicherry": {"lat": 11.9416, "lon": 79.8083, "name": "Pondicherry", "harbour_name": "Thengaithittu Fishing Harbour", "harbour_lat": 11.9168, "harbour_lon": 79.8251, "coast": "east"},
    "ratnagiri": {"lat": 16.9902, "lon": 73.3120, "name": "Ratnagiri", "harbour_name": "Mirkarwada Fishing Harbour", "harbour_lat": 16.9935, "harbour_lon": 73.2840, "coast": "west"},
}

COASTAL_LOCATIONS = ["Kochi", "Mumbai", "Chennai", "Mangalore", "Visakhapatnam"]
INLAND_MONITORED = ["Delhi", "Jaipur", "Hyderabad", "Bengaluru", "Kolkata", "Pune", "Ahmedabad"]
MONITORED_LOCATIONS = COASTAL_LOCATIONS.copy()

ROUTE_COLORS = {
    0: {"hex": "#00E5FF", "label": "Primary Route (Neon Cyan)"},
    1: {"hex": "#3B82F6", "label": "Secondary Route (Electric Blue)"},
    2: {"hex": "#F59E0B", "label": "Alternate Route (Amber Gold)"}
}

GEOFENCES = {
    "Kochi Harbour Zone": {"center": (9.9402, 76.2598), "radius_km": 8, "type": "harbour", "color": "#00E5FF", "description": "Cochin Fisheries Harbour operational zone"},
    "Mumbai Sassoon Zone": {"center": (18.9167, 72.8258), "radius_km": 7, "type": "harbour", "color": "#3B82F6", "description": "Sassoon Docks fishing harbour zone"},
    "Chennai Kasimedu Zone": {"center": (13.1250, 80.2985), "radius_km": 6, "type": "harbour", "color": "#10B981", "description": "Kasimedu Fishing Harbour zone"},
    "Mangalore Port Zone": {"center": (12.8584, 74.8351), "radius_km": 7, "type": "harbour", "color": "#F59E0B", "description": "Old Mangalore Bunder Port zone"},
    "Vizag Harbour Zone": {"center": (17.6980, 83.2982), "radius_km": 8, "type": "harbour", "color": "#A855F7", "description": "Vizag Fishing Harbour zone"},
    "Goa Mormugao Zone": {"center": (15.4124, 73.8052), "radius_km": 9, "type": "harbour", "color": "#EC4899", "description": "Mormugao / Betul Fishing Harbour zone"}
}

RE_GREETING = re.compile(r'\b(hi|hello|hey|heyy|greetings|namaste|namaskar|vanakkam|kem\s*cho|good\s*(morning|afternoon|evening|day)|kaise\s*ho|kya\s*haal|kese\s*ho|hi\s*there|hello\s*there)\b', re.IGNORECASE)
RE_IDENTITY = re.compile(r'\b(who are you|what is your name|kya ho tum|tum kaun ho|what can you do|your features|help me|what do you do|introduce yourself|tell me about yourself|how can you help)\b', re.IGNORECASE)
RE_GRATITUDE = re.compile(r'\b(thank\s*you|thanks|dhanyawad|shukriya|bye|goodbye|alvida|see you)\b', re.IGNORECASE)
RE_MARINE_CORE = re.compile(r'\b(sea|weather|wind|safe\w*|fish\w*|wave\w*|tide\w*|ocean|cyclon\w*|storm\w*|rain|boat|harbour|harbor|port|coast|pfz|navigation|direction\w*|route\w*|distance|samundar|mausam|hawa|machli|temperature|temp|humidity|geofence|geo\s*fence|zone)\b', re.IGNORECASE)
RE_ALERT = re.compile(r'\b(alert|alerts|warning|warnings|danger|dangerous|risk|risky|emergency|caution|advisory|advisories|chetaavani|chetavani|khatra|khatre)\b', re.IGNORECASE)

# ====================== LANGUAGE HELPERS ======================
def get_lang_instruction(language):
    instructions = {
        "English": "Reply only in clear, simple English.",
        "Hindi": "केवल स्पष्ट और सरल हिंदी में उत्तर दें।",
        "Tamil": "தெளிவான மற்றும் எளிய தமிழில் மட்டும் பதிலளிக்கவும்.",
        "Telugu": "స్పష్టమైన మరియు సాధారణ తెలుగులో మాత్రమే సమాధానం ఇవ్వండి.",
        "Malayalam": "വ്യക്തവും ലളിതവുമായ മലയാളത്തിൽ മാത്രം മറുപടി നൽകുക.",
        "Kannada": "ಸ್ಪಷ್ಟ ಮತ್ತು ಸರಳ ಕನ್ನಡದಲ್ಲಿ ಮಾತ್ರ ಉತ್ತರಿಸಿ.",
        "Marathi": "फक्त स्पष्ट आणि साध्या मराठीत उत्तर द्या.",
        "Gujarati": "ફક્ત સ્પષ્ટ અને સરળ ગુજરાતીમાં જવાબ આપો.",
        "Bengali": "শুধুমাত্র স্পষ্ট এবং সহজ বাংলায় উত্তর দিন।"
    }
    return instructions.get(language, instructions["English"])

def get_natural_greeting(language="English"):
    greetings = {
        "English": "👋 **Hello! Welcome to the Marine Intelligence Platform.**\n\nI support voice input in 9 languages. Just speak or type!",
        "Hindi": "👋 **नमस्ते! मरीन इंटेलिजेंस प्लेटफ़ॉर्म में आपका स्वागत है।**\n\nमैं 9 भाषाओं में वॉइस इनपुट सपोर्ट करता हूँ।",
        "Tamil": "👋 **வணக்கம்! மெரைன் இன்டெலிஜென்ஸ் பிளாட்ஃபார்மிற்கு வரவேற்கிறோம்.**\n\nநான் 9 மொழிகளில் குரல் உள்ளீட்டை ஆதரிக்கிறேன்.",
        "Telugu": "👋 **నమస్కారం! మెరైన్ ఇంటెలిజెన్స్ ప్లాట్‌ఫామ్‌కు స్వాగతం.**\n\nనేను 9 భాషలలో వాయిస్ ఇన్‌పుట్‌ను సపోర్ట్ చేస్తాను.",
        "Malayalam": "👋 **നമസ്കാരം! മറൈൻ ഇന്റലിജൻസ് പ്ലാറ്റ്ഫോമിലേക്ക് സ്വാഗതം.**\n\nഞാൻ 9 ഭാഷകളിൽ വോയ്സ് ഇൻപുട്ട് പിന്തുണയ്ക്കുന്നു.",
        "Kannada": "👋 **ನಮಸ್ಕಾರ! ಮೆರೈನ್ ಇಂಟೆಲಿಜೆನ್ಸ್ ಪ್ಲಾಟ್‌ಫಾರ್ಮ್‌ಗೆ ಸ್ವಾಗತ.**\n\nನಾನು 9 ಭಾಷೆಗಳಲ್ಲಿ ವಾಯ್ಸ್ ಇನ್‌ಪುಟ್ ಅನ್ನು ಬೆಂಬಲಿಸುತ್ತೇನೆ.",
        "Marathi": "👋 **नमस्कार! मरीन इंटेलिजन्स प्लॅटफॉर्ममध्ये आपले स्वागत आहे.**\n\nमी 9 भाषांमध्ये व्हॉइस इनपुट सपोर्ट करतो.",
        "Gujarati": "👋 **નમસ્તે! મરીન ઇન્ટેલિજન્સ પ્લેટફોર્મમાં આપનું સ્વાગત છે.**\n\nહું 9 ભાષાઓમાં વૉઇસ ઇનપુટ સપોર્ટ કરું છું.",
        "Bengali": "👋 **নমস্কার! মেরিন ইন্টেলিজেন্স প্ল্যাটফর্মে আপনাকে স্বাগতম।**\n\nআমি 9টি ভাষায় ভয়েস ইনপুট সমর্থন করি।"
    }
    return greetings.get(language, greetings["English"])

def get_natural_identity(language="English"):
    identities = {
        "English": "🤖 **I am the Marine Intelligence Assistant.**\n\nI support multi-language voice input and replies in English, Hindi, Tamil, Telugu, Malayalam, Kannada, Marathi, Gujarati and Bengali.",
        "Hindi": "🤖 **मैं मरीन इंटेलिजेंस असिस्टेंट हूँ।**\n\nमैं बहुभाषी वॉइस इनपुट और उत्तर का समर्थन करता हूँ।",
        "Tamil": "🤖 **நான் மெரைன் இன்டெலிஜென்ஸ் அசிஸ்டண்ட்.**\n\nநான் பன்மொழி குரல் உள்ளீடு மற்றும் பதில்களை ஆதரிக்கிறேன்.",
        "Telugu": "🤖 **నేను మెరైన్ ఇంటెలిజెన్స్ అసిస్టెంట్.**\n\nనేను బహుభాషా వాయిస్ ఇన్‌పుట్ మరియు సమాధానాలను సపోర్ట్ చేస్తాను.",
        "Malayalam": "🤖 **ഞാൻ മറൈൻ ഇന്റലിജൻസ് അസിസ്റ്റന്റ് ആണ്.**\n\nഞാൻ ബഹുഭാഷാ വോയ്സ് ഇൻപുട്ടും മറുപടികളും പിന്തുണയ്ക്കുന്നു.",
        "Kannada": "🤖 **ನಾನು ಮೆರೈನ್ ಇಂಟೆಲಿಜೆನ್ಸ್ ಅಸಿಸ್ಟೆಂಟ್.**\n\nನಾನು ಬಹುಭಾಷಾ ವಾಯ್ಸ್ ಇನ್‌ಪುಟ್ ಮತ್ತು ಉತ್ತರಗಳನ್ನು ಬೆಂಬಲಿಸುತ್ತೇನೆ.",
        "Marathi": "🤖 **मी मरीन इंटेलिजन्स असिस्टंट आहे.**\n\nमी बहुभाषिक व्हॉइस इनपुट आणि उत्तरे सपोर्ट करतो.",
        "Gujarati": "🤖 **હું મરીન ઇન્ટેલિજન્સ અસિસ્ટન્ટ છું.**\n\nહું બહુભાષી વૉઇસ ઇનપુટ અને જવાબો સપોર્ટ કરું છું.",
        "Bengali": "🤖 **আমি মেরিন ইন্টেলিজেন্স অ্যাসিস্ট্যান্ট।**\n\nআমি বহুভাষিক ভয়েস ইনপুট এবং উত্তর সমর্থন করি।"
    }
    return identities.get(language, identities["English"])

# ====================== GEOCODING ======================
@st.cache_data(ttl=3600, show_spinner=False)
def geocode_location(place_name: str):
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": place_name, "count": 5, "language": "en", "format": "json", "countryCode": "IN"}
        r = requests.get(url, params=params, timeout=6)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                best = results[0]
                return {
                    "name": best.get("name"),
                    "lat": best.get("latitude"),
                    "lon": best.get("longitude"),
                    "admin1": best.get("admin1"),
                    "country": best.get("country"),
                    "is_coastal": False
                }
    except Exception:
        pass
    return None

# ====================== VOICE TO TEXT (MULTI-LANGUAGE) ======================
def get_audio_filename_and_mime(audio_bytes, original_name=None, mime_type=None):
    if not audio_bytes or len(audio_bytes) < 4:
        return "voice_input.wav", "audio/wav"
    header = audio_bytes[:12]
    if header.startswith(b"\x1aE\xdf\xa3") or b"webm" in audio_bytes[:64].lower():
        return "voice_input.webm", "audio/webm"
    if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WAVE":
        return "voice_input.wav", "audio/wav"
    if header.startswith(b"OggS"):
        return "voice_input.ogg", "audio/ogg"
    if header.startswith(b"ID3") or header[:2] in [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"]:
        return "voice_input.mp3", "audio/mpeg"
    if len(header) >= 8 and header[4:8] == b"ftyp":
        return "voice_input.mp4", "audio/mp4"
    if original_name and "." in original_name:
        ext = original_name.rsplit(".", 1)[-1].lower()
        if ext in ["webm", "wav", "mp3", "ogg", "mp4", "m4a"]:
            return f"voice_input.{ext}", mime_type or f"audio/{ext}"
    return "voice_input.webm", "audio/webm"

def transcribe_voice_query(audio_bytes, language="English"):
    """
    High-accuracy multi-language voice-to-text using Groq Whisper.
    Supports: en, hi, ta, te, ml, kn, mr, gu, bn
    """
    if not audio_bytes or len(audio_bytes) < 100:
        return None

    filename, mime_type = get_audio_filename_and_mime(audio_bytes)
    lang_code = SUPPORTED_LANGUAGES.get(language, {}).get("whisper", "en")

    for model_name in ["whisper-large-v3-turbo", "whisper-large-v3"]:
        try:
            transcription = client.audio.transcriptions.create(
                file=(filename, audio_bytes, mime_type),
                model=model_name,
                language=lang_code,
                temperature=0.0,
                response_format="text"
            )
            # Handle both string and object response
            if isinstance(transcription, str):
                text = transcription.strip()
            else:
                text = getattr(transcription, "text", str(transcription)).strip()

            if text:
                return text
        except Exception:
            try:
                # Fallback without forcing language
                transcription = client.audio.transcriptions.create(
                    file=(filename, audio_bytes, mime_type),
                    model=model_name,
                    temperature=0.0
                )
                if isinstance(transcription, str):
                    text = transcription.strip()
                else:
                    text = getattr(transcription, "text", str(transcription)).strip()
                if text:
                    return text
            except Exception:
                continue
    return None

# ====================== WEATHER + OCEANOGRAPHIC AGENT ======================
@st.cache_data(ttl=180, show_spinner=False)
def weather_agent(lat, lon):
    try:
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": ",".join([
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "precipitation", "rain", "weather_code", "cloud_cover",
                "pressure_msl", "surface_pressure",
                "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "visibility"
            ]),
            "timezone": "Asia/Kolkata"
        }
        weather_resp = requests.get(weather_url, params=weather_params, timeout=10)
        if weather_resp.status_code != 200:
            return {"status": "error", "message": f"Weather API Error: {weather_resp.status_code}"}

        current = weather_resp.json().get("current", {})
        if not current:
            return {"status": "error", "message": "No weather data received"}

        marine_url = "https://marine-api.open-meteo.com/v1/marine"
        marine_params = {
            "latitude": lat,
            "longitude": lon,
            "current": ",".join([
                "sea_surface_temperature", "wave_height", "wave_direction", "wave_period",
                "wind_wave_height", "wind_wave_direction", "wind_wave_period",
                "swell_wave_height", "swell_wave_direction", "swell_wave_period",
                "ocean_current_velocity", "ocean_current_direction"
            ]),
            "timezone": "Asia/Kolkata"
        }
        marine_resp = requests.get(marine_url, params=marine_params, timeout=8)
        mdata = marine_resp.json().get("current", {}) if marine_resp.status_code == 200 else {}

        wind_speed = current.get("wind_speed_10m", 0) or 0
        wave_height = mdata.get("wave_height")
        sst = mdata.get("sea_surface_temperature")

        if wind_speed < 15 and (wave_height is None or wave_height < 1.5):
            safety_status, safety_color = "Safe", "green"
            safety_message = "Conditions appear favourable."
        elif wind_speed < 25 and (wave_height is None or wave_height < 2.5):
            safety_status, safety_color = "Moderately Safe", "orange"
            safety_message = "Exercise caution. Moderate wind / waves."
        else:
            safety_status, safety_color = "Not Safe", "red"
            safety_message = "High wind or rough sea conditions. Stay safe."

        weather_code = current.get("weather_code", 0)
        weather_desc = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }.get(weather_code, "Unknown")

        return {
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "precipitation": current.get("precipitation"),
            "rain": current.get("rain"),
            "cloud_cover": current.get("cloud_cover"),
            "pressure_msl": current.get("pressure_msl"),
            "surface_pressure": current.get("surface_pressure"),
            "wind_speed": round(wind_speed, 1),
            "wind_direction": current.get("wind_direction_10m"),
            "wind_gusts": current.get("wind_gusts_10m"),
            "visibility": current.get("visibility"),
            "weather_code": weather_code,
            "weather_desc": weather_desc,
            "sea_surface_temperature": round(sst, 1) if sst is not None else None,
            "wave_height": round(wave_height, 2) if wave_height is not None else None,
            "wave_direction": mdata.get("wave_direction"),
            "wave_period": round(mdata.get("wave_period"), 1) if mdata.get("wave_period") is not None else None,
            "wind_wave_height": mdata.get("wind_wave_height"),
            "swell_wave_height": mdata.get("swell_wave_height"),
            "ocean_current_velocity": round(mdata.get("ocean_current_velocity"), 2) if mdata.get("ocean_current_velocity") is not None else None,
            "ocean_current_direction": mdata.get("ocean_current_direction"),
            "safety_status": safety_status,
            "safety_color": safety_color,
            "safety_message": safety_message,
            "prediction": safety_message,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@st.cache_data(ttl=90, show_spinner=False)
def cached_continuous_monitor():
    results = []
    for name in MONITORED_LOCATIONS:
        loc = next((val for val in LOCATIONS.values() if val["name"] == name), None)
        if not loc:
            continue
        try:
            weather = weather_agent(loc["lat"], loc["lon"])
            if weather.get("status") == "success":
                results.append({
                    "name": name,
                    "safety_status": weather["safety_status"],
                    "safety_color": weather["safety_color"],
                    "wind_speed": weather["wind_speed"],
                    "temperature": weather["temperature"],
                    "sst": weather.get("sea_surface_temperature"),
                    "wave_height": weather.get("wave_height"),
                    "prediction": weather.get("prediction", "No prediction"),
                    "lat": loc["lat"],
                    "lon": loc["lon"],
                    "is_coastal": True,
                    "priority": 0
                })
        except Exception:
            continue
    return results

def _resolve_location_coords(name: str):
    loc = next((val for val in LOCATIONS.values() if val["name"] == name), None)
    if loc:
        return {
            "name": name,
            "lat": loc["lat"],
            "lon": loc["lon"],
            "is_coastal": True,
            "harbour_name": loc.get("harbour_name", name),
            "harbour_lat": loc.get("harbour_lat", loc["lat"]),
            "harbour_lon": loc.get("harbour_lon", loc["lon"]),
            "coast": loc.get("coast", "unknown")
        }
    geo = geocode_location(name)
    if geo:
        return {
            "name": geo["name"] or name,
            "lat": geo["lat"],
            "lon": geo["lon"],
            "is_coastal": False,
            "harbour_name": name,
            "harbour_lat": geo["lat"],
            "harbour_lon": geo["lon"],
            "coast": "inland",
            "state": geo.get("admin1")
        }
    return None

# ====================== ALERT AGENT ======================
def alert_agent(weather_info, location_name, language="English", is_coastal=True):
    if not weather_info or weather_info.get("status") != "success":
        return {
            "status": "error", "level": "UNKNOWN", "title": "Alert Unavailable",
            "message": "Could not retrieve weather data.", "color": "#64748b",
            "icon": "❓", "action": "Please try again later.", "whatsapp_text": "",
            "is_coastal": is_coastal, "priority_group": "coastal" if is_coastal else "inland"
        }

    wind = weather_info.get("wind_speed", 0)
    wave = weather_info.get("wave_height")
    safety = weather_info.get("safety_status", "Safe")
    temp = weather_info.get("temperature", "--")
    sst = weather_info.get("sea_surface_temperature")

    if wind >= 30 or safety == "Not Safe" or (wave is not None and wave >= 3.0):
        level, color, icon = "CRITICAL", "#DC2626", "🚨"
        title = f"CRITICAL ALERT — {location_name}"
        message = f"High wind **{wind} km/h**" + (f" & waves **{wave} m**" if wave else "") + ". **Stay safe.**"
        action = "Avoid outdoor activities if possible."
    elif wind >= 20 or safety == "Moderately Safe" or (wave is not None and wave >= 1.8):
        level, color, icon = "WARNING", "#F59E0B", "⚠️"
        title = f"WARNING — {location_name}"
        message = f"Moderate winds **{wind} km/h**" + (f" | Waves: **{wave} m**" if wave else "") + ". Exercise caution."
        action = "Stay alert and carry necessary precautions."
    elif wind >= 12:
        level, color, icon = "ADVISORY", "#3B82F6", "ℹ️"
        title = f"ADVISORY — {location_name}"
        message = f"Wind **{wind} km/h**" + (f" | SST: **{sst}°C**" if sst else "") + ". Conditions manageable."
        action = "Monitor conditions."
    else:
        level, color, icon = "CLEAR", "#10B981", "✅"
        title = f"ALL CLEAR — {location_name}"
        message = f"Favourable conditions. Wind **{wind} km/h**" + (f" | SST: **{sst}°C**" if sst else "") + "."
        action = "Have a safe day!"

    whatsapp_text = (
        f"🌊 ALERT — {location_name}\nLevel: {level}\n"
        f"Priority: {'COASTAL (First)' if is_coastal else 'INLAND'}\n"
        f"Wind: {wind} km/h | Temp: {temp}°C"
        + (f" | SST: {sst}°C" if sst else "")
        + (f" | Wave: {wave} m" if wave else "")
        + f"\n{message.replace('**','')}\nAction: {action}\n"
        f"Time: {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %b %Y, %I:%M %p')}"
    )

    return {
        "status": "success", "level": level, "title": title, "message": message,
        "color": color, "icon": icon, "action": action,
        "wind_speed": wind, "temperature": temp,
        "sea_surface_temperature": sst, "wave_height": wave,
        "safety_status": safety, "location": location_name,
        "whatsapp_text": whatsapp_text,
        "timestamp": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p"),
        "is_coastal": is_coastal,
        "priority_group": "coastal" if is_coastal else "inland"
    }

def generate_active_alerts(language="English", include_inland=True):
    active = []
    level_priority = {"CRITICAL": 0, "WARNING": 1, "ADVISORY": 2}

    for name in COASTAL_LOCATIONS:
        loc = next((val for val in LOCATIONS.values() if val["name"] == name), None)
        if not loc:
            continue
        weather = weather_agent(loc["lat"], loc["lon"])
        if weather.get("status") == "success":
            alert = alert_agent(weather, name, language, is_coastal=True)
            if alert["level"] in ["CRITICAL", "WARNING", "ADVISORY"]:
                active.append(alert)

    if include_inland:
        for name in INLAND_MONITORED:
            loc_info = _resolve_location_coords(name)
            if not loc_info:
                continue
            weather = weather_agent(loc_info["lat"], loc_info["lon"])
            if weather.get("status") == "success":
                alert = alert_agent(weather, loc_info["name"], language, is_coastal=False)
                if alert["level"] in ["CRITICAL", "WARNING", "ADVISORY"]:
                    active.append(alert)

    active.sort(key=lambda x: (0 if x.get("is_coastal", False) else 1, level_priority.get(x["level"], 99)))
    return active

@st.cache_data(ttl=90, show_spinner=False)
def real_time_alert_agent(language="English"):
    return generate_active_alerts(language=language, include_inland=True)

def render_alert_banner(alert_data):
    if not alert_data or alert_data.get("status") != "success":
        return
    level = alert_data["level"]
    color = alert_data["color"]
    icon = alert_data["icon"]

    if level == "CRITICAL":
        border, bg, pulse = f"3px solid {color}", "linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%)", "animation: pulse 1.5s infinite;"
    elif level == "WARNING":
        border, bg, pulse = f"2px solid {color}", "linear-gradient(135deg, #78350f 0%, #451a03 100%)", ""
    elif level == "ADVISORY":
        border, bg, pulse = f"2px solid {color}", "linear-gradient(135deg, #1e3a8a 0%, #1e293b 100%)", ""
    else:
        border, bg, pulse = f"2px solid {color}", "linear-gradient(135deg, #064e3b 0%, #022c22 100%)", ""

    priority_badge = ""
    if alert_data.get("is_coastal"):
        priority_badge = '<span style="background:#0ea5e9;color:#000;font-weight:700;font-size:0.65rem;padding:2px 8px;border-radius:10px;margin-left:8px;">🌊 COASTAL PRIORITY</span>'
    else:
        priority_badge = '<span style="background:#64748b;color:#fff;font-weight:600;font-size:0.65rem;padding:2px 8px;border-radius:10px;margin-left:8px;">🏙 INLAND</span>'

    html = f"""
    <style>
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }}
        70% {{ box-shadow: 0 0 0 12px rgba(220, 38, 38, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }}
    }}
    </style>
    <div style="background: {bg}; border: {border}; border-radius: 16px; padding: 18px 20px; color: white; margin: 12px 0 18px; {pulse}">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <div style="font-size:1.15rem; font-weight:700;">{icon} {alert_data['title']} {priority_badge}</div>
            <div style="background:{color}; color:#000; font-weight:800; font-size:0.75rem; padding:3px 10px; border-radius:20px;">{level}</div>
        </div>
        <div style="font-size:0.95rem; line-height:1.45; margin-bottom:10px;">{alert_data['message']}</div>
        <div style="font-size:0.85rem; opacity:0.9; margin-bottom:6px;"><b>Recommended Action:</b> {alert_data['action']}</div>
        <div style="font-size:0.75rem; opacity:0.7;">
            💨 Wind: {alert_data['wind_speed']} km/h &nbsp;|&nbsp; 🌡️ {alert_data['temperature']}°C
            {f"&nbsp;|&nbsp; 🌊 SST: {alert_data.get('sea_surface_temperature')}°C" if alert_data.get('sea_surface_temperature') is not None else ""}
            {f"&nbsp;|&nbsp; 🌊 Wave: {alert_data.get('wave_height')} m" if alert_data.get('wave_height') is not None else ""}
            &nbsp;|&nbsp; 🕒 {alert_data['timestamp']}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_active_alerts_panel(language="English"):
    active = real_time_alert_agent(language)
    coastal_alerts = [a for a in active if a.get("is_coastal")]
    inland_alerts = [a for a in active if not a.get("is_coastal")]

    if not active:
        st.success("✅ **No active alerts** — all monitored locations are clear.")
        return

    st.markdown(f"### 🚨 Real-Time Alert Agent — {len(active)} Active")
    st.caption("Coastal locations are prioritised first.")

    if coastal_alerts:
        st.markdown("#### 🌊 Coastal Priority Alerts")
        for alert in coastal_alerts:
            render_alert_banner(alert)
            wa_text = quote(alert["whatsapp_text"])
            st.link_button(f"📤 Share {alert['location']} Alert", f"https://wa.me/?text={wa_text}")
            st.markdown("<br>", unsafe_allow_html=True)

    if inland_alerts:
        st.markdown("#### 🏙 Inland Alerts")
        for alert in inland_alerts:
            render_alert_banner(alert)
            wa_text = quote(alert["whatsapp_text"])
            st.link_button(f"📤 Share {alert['location']} Alert", f"https://wa.me/?text={wa_text}")
            st.markdown("<br>", unsafe_allow_html=True)

# ====================== NAVIGATION ======================
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 2)

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
    return round((math.degrees(math.atan2(x, y)) + 360) % 360, 1)

def bearing_to_compass(bearing):
    points = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return points[round(bearing / 22.5) % 16]

def generate_marine_route(origin_lat, origin_lon, dest_lat, dest_lon, harbour_name, dest_name, boat_speed_knots=10):
    dist_km = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
    dist_nm = round(dist_km / 1.852, 1)
    bearing = calculate_bearing(origin_lat, origin_lon, dest_lat, dest_lon)
    compass_dir = bearing_to_compass(bearing)
    speed_kmh = boat_speed_knots * 1.852
    travel_hours = dist_km / speed_kmh
    hours = int(travel_hours)
    minutes = int((travel_hours - hours) * 60)
    fuel_est_liters = round(dist_nm * 1.5, 1)

    wp1 = [origin_lat, origin_lon]
    wp2 = [round(origin_lat + (dest_lat-origin_lat)*0.25 + (0.01 if dest_lat>origin_lat else -0.01),4),
           round(origin_lon + (dest_lon-origin_lon)*0.25,4)]
    wp3 = [round(origin_lat + (dest_lat-origin_lat)*0.65,4),
           round(origin_lon + (dest_lon-origin_lon)*0.65,4)]
    wp4 = [dest_lat, dest_lon]

    gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_lat},{origin_lon}&destination={dest_lat},{dest_lon}&travelmode=driving"

    return {
        "distance_km": dist_km, "distance_nm": dist_nm, "bearing": bearing,
        "compass_dir": compass_dir, "eta": f"{hours}h {minutes}m",
        "fuel_l": fuel_est_liters, "waypoints": [wp1,wp2,wp3,wp4],
        "gmaps_url": gmaps_url
    }

# ====================== GEOFENCING ======================
def is_inside_geofence(lat, lon, fence):
    center_lat, center_lon = fence["center"]
    distance = haversine_distance(lat, lon, center_lat, center_lon)
    return distance <= fence["radius_km"], distance

def check_geofences(lat, lon):
    results = []
    for name, fence in GEOFENCES.items():
        inside, distance = is_inside_geofence(lat, lon, fence)
        results.append({
            "name": name,
            "inside": inside,
            "distance_km": round(distance, 2),
            "type": fence["type"],
            "color": fence["color"],
            "description": fence["description"],
            "radius_km": fence["radius_km"]
        })
    results.sort(key=lambda x: (not x["inside"], x["distance_km"]))
    return results

def render_geofence_status(lat, lon, location_name):
    fences = check_geofences(lat, lon)
    inside_fences = [f for f in fences if f["inside"]]
    nearby_fences = [f for f in fences if not f["inside"] and f["distance_km"] < 25]

    st.markdown("### 🛡️ Geofencing Status")

    if inside_fences:
        for f in inside_fences:
            st.markdown(f"""
            <div style="background:rgba(16,185,129,0.15); border:1px solid #10B981; border-radius:14px; padding:14px; margin-bottom:10px; color:white;">
                <div style="font-weight:700; font-size:1.05rem;">✅ Inside: {f['name']}</div>
                <div style="font-size:0.88rem; opacity:0.9; margin-top:4px;">{f['description']}</div>
                <div style="font-size:0.82rem; margin-top:6px;">Distance from center: <b>{f['distance_km']} km</b> | Radius: {f['radius_km']} km</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"📍 **{location_name}** is currently **outside** all defined harbour geofences.")

    if nearby_fences:
        st.markdown("#### 📍 Nearby Geofences")
        for f in nearby_fences[:3]:
            st.markdown(f"""
            <div style="background:rgba(59,130,246,0.12); border:1px solid rgba(59,130,246,0.4); border-radius:12px; padding:12px; margin-bottom:8px; color:white;">
                <b>{f['name']}</b> — {f['distance_km']} km away
                <div style="font-size:0.8rem; opacity:0.85;">{f['description']}</div>
            </div>
            """, unsafe_allow_html=True)

# ====================== NLP ======================
def advanced_nlp_agent(user_query):
    query = user_query.lower().strip()

    detected_location = None
    is_coastal = False
    for key, value in LOCATIONS.items():
        if re.search(r'\b' + re.escape(key) + r'\b', query):
            detected_location = value
            is_coastal = True
            break

    if not detected_location:
        place_match = re.search(r'\b(?:in|at|for|near|of)\s+([a-zA-Z\s]{3,25})\b', query)
        if place_match:
            place_candidate = place_match.group(1).strip()
        else:
            words = re.findall(r'[a-zA-Z]{3,}', query)
            place_candidate = " ".join(words[-2:]) if len(words) >= 2 else (words[-1] if words else None)

        if place_candidate and place_candidate not in ["weather", "temperature", "wind", "safe", "fishing", "alert", "geofence", "zone"]:
            geo = geocode_location(place_candidate)
            if geo:
                detected_location = {
                    "name": geo["name"],
                    "lat": geo["lat"],
                    "lon": geo["lon"],
                    "harbour_name": geo["name"],
                    "harbour_lat": geo["lat"],
                    "harbour_lon": geo["lon"],
                    "coast": "unknown",
                    "is_coastal": False,
                    "state": geo.get("admin1")
                }
                is_coastal = False

    has_greeting = bool(RE_GREETING.search(query))
    has_identity = bool(RE_IDENTITY.search(query))
    has_gratitude = bool(RE_GRATITUDE.search(query))
    has_marine = bool(RE_MARINE_CORE.search(query))
    has_alert = bool(RE_ALERT.search(query))

    if has_alert and not detected_location:
        intent = "SHOW_ALERTS"
    elif has_alert and detected_location:
        intent = "LOCATION_ALERT"
    elif detected_location and (has_marine or not has_greeting):
        intent = "MARINE_LOCATION" if is_coastal else "GENERAL_WEATHER"
    elif detected_location and has_greeting:
        intent = "MARINE_LOCATION" if is_coastal else "GENERAL_WEATHER"
    elif not detected_location and has_marine:
        intent = "LOCATION_AMBIGUOUS"
    elif has_identity:
        intent = "BOT_IDENTITY"
    elif has_gratitude:
        intent = "GRATITUDE"
    elif has_greeting:
        intent = "GREETING"
    else:
        intent = "NORMAL_CHAT"

    return {
        "intent": intent,
        "location": detected_location,
        "is_coastal": is_coastal,
        "has_greeting": has_greeting,
        "needs_weather": intent in ["MARINE_LOCATION", "LOCATION_ALERT", "GENERAL_WEATHER"],
        "needs_pfz": intent == "MARINE_LOCATION" and is_coastal,
        "needs_alert": intent in ["SHOW_ALERTS", "LOCATION_ALERT", "MARINE_LOCATION", "GENERAL_WEATHER"],
        "original_query": user_query
    }

# ====================== PFZ ======================
@st.cache_data(ttl=300, show_spinner=False)
def fetch_sst(lat, lon):
    try:
        url = "https://marine-api.open-meteo.com/v1/marine"
        params = {"latitude": lat, "longitude": lon, "current": "sea_surface_temperature", "timezone": "Asia/Kolkata"}
        r = requests.get(url, params=params, timeout=6)
        if r.status_code == 200:
            return r.json().get("current", {}).get("sea_surface_temperature")
    except Exception:
        pass
    return None

def pfz_agent(location_info, weather_info=None):
    location_name = location_info["name"]
    base_lat = location_info.get("harbour_lat", location_info["lat"])
    base_lon = location_info.get("harbour_lon", location_info["lon"])
    coast = location_info.get("coast", "west")

    sst = fetch_sst(base_lat, base_lon)
    if sst is None and weather_info:
        sst = weather_info.get("sea_surface_temperature")
    if sst is None:
        sst = 28.5

    wind_speed = weather_info.get("wind_speed", 12) if weather_info else 14
    wave_height = weather_info.get("wave_height") if weather_info else None

    sst_score = 100 if 28.0 <= sst <= 29.5 else 75 if 27.0 <= sst <= 30.5 else 50
    chlorophyll_proxy = round(0.9 + (abs(sst - 28.7) * 0.35), 2)
    chl_score = min(100, int(chlorophyll_proxy * 55))
    wind_score = 100 if wind_speed < 15 else 60 if wind_speed < 25 else 20
    if wave_height is not None:
        if wave_height < 1.2: wind_score = min(100, wind_score + 10)
        elif wave_height > 2.5: wind_score = max(10, wind_score - 30)

    total_score = int((sst_score * 0.40) + (chl_score * 0.35) + (wind_score * 0.25))
    lon_dir = -1 if coast == "west" else 1

    offsets = [(0.05, lon_dir*0.18), (0.11, lon_dir*0.26), (-0.06, lon_dir*0.22)]
    base_zones = []
    types = ["Primary", "Secondary", "Alternate"]

    for i, (lat_off, lon_off) in enumerate(offsets):
        zone_lat = round(base_lat + lat_off, 4)
        zone_lon = round(base_lon + lon_off, 4)
        zone_sst = fetch_sst(zone_lat, zone_lon) or sst
        zone_sst_score = 100 if 28.0 <= zone_sst <= 29.5 else 70 if 27.2 <= zone_sst <= 30.2 else 45
        dist_km = haversine_distance(base_lat, base_lon, zone_lat, zone_lon)
        dist_nm = round(dist_km / 1.852, 1)
        zone_score = max(40, int((zone_sst_score*0.45 + chl_score*0.30 + wind_score*0.25) - i*6))

        base_zones.append({
            "name": f"{types[i]} PFZ - {location_name}",
            "type": types[i],
            "distance_km": dist_km, "distance_nm": dist_nm,
            "distance": f"{dist_km} km ({dist_nm} NM)",
            "score": zone_score, "lat": zone_lat, "lon": zone_lon,
            "sst": round(zone_sst, 1), "chlorophyll": chlorophyll_proxy,
            "color_hex": ROUTE_COLORS[i]["hex"]
        })

    best_zone = max(base_zones, key=lambda z: z["score"])
    recommendation = "Highly Recommended" if best_zone["score"] >= 75 else "Moderately Recommended"

    return {
        "status": "success", "best_zone": best_zone, "all_zones": base_zones,
        "overall_score": total_score, "recommendation": recommendation,
        "sst": round(sst, 1), "chlorophyll": chlorophyll_proxy,
        "harbour_name": location_info.get("harbour_name", f"{location_name} Port"),
        "harbour_lat": base_lat, "harbour_lon": base_lon,
        "note": "Real-time SST + wind driven PFZ estimate (Open-Meteo). Official INCOIS: incois.gov.in"
    }

def call_groq_llm(messages, max_tokens=400, temperature=0.3):
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
    for model_name in models:
        try:
            completion = client.chat.completions.create(
                messages=messages, model=model_name,
                max_tokens=max_tokens, temperature=temperature
            )
            raw = completion.choices[0].message.content or ""
            clean = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            if clean: return clean
        except Exception:
            continue
    return None

def response_agent(user_query, nlp_plan, weather_info=None, pfz_info=None, alert_info=None, language="English"):
    intent = nlp_plan.get("intent", "NORMAL_CHAT")
    lang_inst = get_lang_instruction(language)

    if intent == "GREETING":
        return get_natural_greeting(language)
    elif intent == "BOT_IDENTITY":
        return get_natural_identity(language)
    elif intent == "GRATITUDE":
        thanks = {
            "English": "🙏 **You're very welcome! Stay safe!** 🌊",
            "Hindi": "🙏 **आपका बहुत धन्यवाद! सुरक्षित रहें!** 🌊",
            "Tamil": "🙏 **நன்றி! பாதுகாப்பாக இருங்கள்!** 🌊",
            "Telugu": "🙏 **ధన్యవాదాలు! సురక్షితంగా ఉండండి!** 🌊",
            "Malayalam": "🙏 **നന്ദി! സുരക്ഷിതരായിരിക്കൂ!** 🌊",
            "Kannada": "🙏 **ಧನ್ಯವಾದಗಳು! ಸುರಕ್ಷಿತವಾಗಿರಿ!** 🌊",
            "Marathi": "🙏 **धन्यवाद! सुरक्षित राहा!** 🌊",
            "Gujarati": "🙏 **આભાર! સુરક્ષિત રહો!** 🌊",
            "Bengali": "🙏 **ধন্যবাদ! নিরাপদ থাকুন!** 🌊"
        }
        return thanks.get(language, thanks["English"])
    elif intent == "LOCATION_AMBIGUOUS":
        return get_natural_greeting(language)
    elif intent == "SHOW_ALERTS":
        return "🚨 **Real-Time Alert Agent activated.**" if language == "English" else "🚨 **रीयल-टाइम अलर्ट एजेंट सक्रिय।**"

    loc = nlp_plan.get("location")
    if loc and weather_info:
        loc_name = loc.get("name", "Location")
        state = loc.get("state", "")
        full_name = f"{loc_name}, {state}" if state else loc_name

        context = f"""
Location: {full_name}
Temperature: {weather_info.get('temperature')}°C
Feels like: {weather_info.get('feels_like')}°C
Wind: {weather_info.get('wind_speed')} km/h
Humidity: {weather_info.get('humidity')}%
Safety Status: {weather_info.get('safety_status')}
SST: {weather_info.get('sea_surface_temperature')}°C
Wave Height: {weather_info.get('wave_height')} m
"""
        if pfz_info:
            context += f"\nBest PFZ: {pfz_info['best_zone']['name']} ({pfz_info['best_zone']['distance']})"

        system_prompt = f"""You are a helpful marine and weather assistant for India.
{lang_inst}
Give a clear, concise and useful summary of the weather and ocean conditions.
Mention the safety status clearly.
If PFZ data is available, recommend the best fishing zone.
Keep the response short and practical."""

        response = call_groq_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query + "\n\nData:\n" + context}
        ])
        if response:
            return response

        return f"📍 **{full_name}**\nTemperature: {weather_info.get('temperature')}°C | Wind: {weather_info.get('wind_speed')} km/h | Status: {weather_info.get('safety_status')}"

    response = call_groq_llm([
        {"role": "system", "content": f"You are a helpful marine weather assistant for India. {lang_inst}"},
        {"role": "user", "content": user_query}
    ])
    return response or get_natural_greeting(language)

# ====================== RENDER HELPERS ======================
def clean_text_for_tts(text):
    if not text: return ""
    t = re.sub(r"```[\s\S]*?```", "", text)
    t = re.sub(r"`.*?`", "", t)
    t = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", t)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"[\U00010000-\U0010ffff]", "", t)
    t = re.sub(r"[*_~#|>]", " ", t)
    t = re.sub(r"^\s*[-+•]\s+", " ", t, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", t).strip()

def render_tts_button(text_to_speak, language="English", auto_play=False, msg_id=None):
    speech_text = clean_text_for_tts(text_to_speak)
    if not speech_text: return
    text_json = json.dumps(speech_text, ensure_ascii=False)
    lang_code = SUPPORTED_LANGUAGES.get(language, {}).get("tts", "en-IN")
    uid = f"tts_{abs(hash(speech_text[:40]))}" if not msg_id else f"tts_{msg_id}"
    auto_trigger = f"setTimeout(function(){{ playTTS_{uid}(); }}, 300);" if auto_play else ""

    html = f"""
    <div style="margin-top:8px; display:flex; align-items:center; gap:8px;">
        <button id="btn_play_{uid}" onclick="playTTS_{uid}();" style="background:linear-gradient(135deg,#0284c7,#0369a1); color:white; border:none; border-radius:8px; padding:6px 14px; font-size:0.82rem; font-weight:600; cursor:pointer;">
            🔊 Listen
        </button>
        <button id="btn_stop_{uid}" onclick="stopTTS_{uid}();" style="display:none; background:#334155; color:#cbd5e1; border:none; border-radius:8px; padding:6px 12px; cursor:pointer;">⏹️ Stop</button>
    </div>
    <script>
    (function() {{
        var text = {text_json};
        var lang = '{lang_code}';
        var uid = '{uid}';
        window['playTTS_'+uid] = function() {{
            if (!('speechSynthesis' in window)) return;
            window.speechSynthesis.cancel();
            var u = new SpeechSynthesisUtterance(text);
            u.lang = lang; u.rate = 1.0;
            var voices = window.speechSynthesis.getVoices();
            if (voices.length) {{
                var preferred = voices.find(v => v.lang && v.lang.toLowerCase().startsWith(lang.toLowerCase().slice(0,2)));
                if (preferred) u.voice = preferred;
            }}
            var playBtn = document.getElementById('btn_play_'+uid);
            var stopBtn = document.getElementById('btn_stop_'+uid);
            u.onstart = function() {{ if(playBtn) playBtn.style.background='#15803d'; if(stopBtn) stopBtn.style.display='inline-flex'; }};
            u.onend = u.onerror = function() {{ if(playBtn) playBtn.style.background='linear-gradient(135deg,#0284c7,#0369a1)'; if(stopBtn) stopBtn.style.display='none'; }};
            window.speechSynthesis.speak(u);
        }};
        window['stopTTS_'+uid] = function() {{ window.speechSynthesis.cancel(); }};
        {auto_trigger}
    }})();
    </script>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_monitoring_dashboard(monitor_data):
    if not monitor_data:
        return

    color_map = {"Safe": "#10B981", "Moderately Safe": "#F59E0B", "Not Safe": "#EF4444"}

    cols = st.columns(5)
    for idx, data in enumerate(monitor_data[:5]):
        with cols[idx]:
            badge_color = color_map.get(data["safety_status"], "#3B82F6")
            sst = data.get("sst")
            wave = data.get("wave_height")
            temp = data.get("temperature")
            wind = data.get("wind_speed")

            st.markdown(f"""
            <div style="
                background: rgba(15, 40, 70, 0.75);
                backdrop-filter: blur(14px);
                border: 1px solid rgba(255,255,255,0.18);
                border-radius: 18px;
                padding: 14px 10px;
                text-align: center;
                color: white;
                box-shadow: 0 8px 32px rgba(0,0,0,0.25);
                min-height: 185px;
            ">
                <div style="font-size:1.05rem; font-weight:700; margin-bottom:6px;">{data['name']}</div>
                <div style="
                    display:inline-block;
                    background:{badge_color};
                    color:white;
                    font-size:0.7rem;
                    font-weight:700;
                    padding:3px 10px;
                    border-radius:20px;
                    margin-bottom:10px;
                ">{data['safety_status']}</div>
                <div style="font-size:0.88rem; margin:3px 0;">💨 {wind} km/h</div>
                <div style="font-size:0.82rem; opacity:0.9;">🌡️ Air {temp}°C</div>
                <div style="font-size:0.82rem; opacity:0.9;">
                    {f"🌊 Wave {wave} m" if wave is not None else "🌊 Wave —"}
                </div>
                <div style="font-size:0.82rem; opacity:0.9;">
                    {f"🌊 SST {sst}°C" if sst is not None else "🌊 SST —"}
                </div>
            </div>
            """, unsafe_allow_html=True)

def deg_to_compass(deg):
    if deg is None:
        return "—"
    points = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return points[round(deg / 22.5) % 16]

def render_full_ocean_meteo_card(weather_data, location_name):
    if not weather_data or weather_data.get("status") != "success":
        return

    safety_color_map = {"green": "#10B981", "orange": "#F59E0B", "red": "#EF4444"}
    accent = safety_color_map.get(weather_data.get("safety_color", "green"), "#3B82F6")

    has_ocean_data = any([
        weather_data.get("sea_surface_temperature") is not None,
        weather_data.get("wave_height") is not None,
        weather_data.get("wave_period") is not None,
        weather_data.get("ocean_current_velocity") is not None,
        weather_data.get("swell_wave_height") is not None,
        weather_data.get("wind_wave_height") is not None
    ])

    if has_ocean_data:
        ocean_section = f"""
        <div style="font-size:0.9rem; font-weight:600; margin:8px 0 8px; color:#67e8f9;">🌊 Oceanographic Data</div>
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px;">
            <div style="background:rgba(14, 165, 233, 0.15); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.8;">SST</div>
                <div style="font-weight:700; font-size:1.15rem;">{weather_data.get('sea_surface_temperature') if weather_data.get('sea_surface_temperature') is not None else '—'}</div>
                <div style="font-size:0.7rem;">°C</div>
            </div>
            <div style="background:rgba(14, 165, 233, 0.15); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.8;">WAVE HT</div>
                <div style="font-weight:700; font-size:1.15rem;">{weather_data.get('wave_height') if weather_data.get('wave_height') is not None else '—'}</div>
                <div style="font-size:0.7rem;">m</div>
            </div>
            <div style="background:rgba(14, 165, 233, 0.15); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.8;">WAVE PERIOD</div>
                <div style="font-weight:700; font-size:1.15rem;">{weather_data.get('wave_period') if weather_data.get('wave_period') is not None else '—'}</div>
                <div style="font-size:0.7rem;">s</div>
            </div>
            <div style="background:rgba(14, 165, 233, 0.15); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.8;">WAVE DIR</div>
                <div style="font-weight:700; font-size:1.05rem;">{deg_to_compass(weather_data.get('wave_direction'))}</div>
            </div>
            <div style="background:rgba(14, 165, 233, 0.15); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.8;">CURRENT</div>
                <div style="font-weight:700; font-size:1.15rem;">{weather_data.get('ocean_current_velocity') if weather_data.get('ocean_current_velocity') is not None else '—'}</div>
                <div style="font-size:0.7rem;">m/s</div>
            </div>
            <div style="background:rgba(14, 165, 233, 0.15); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.8;">CURRENT DIR</div>
                <div style="font-weight:700; font-size:1.05rem;">{deg_to_compass(weather_data.get('ocean_current_direction'))}</div>
            </div>
            <div style="background:rgba(14, 165, 233, 0.15); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.8;">SWELL HT</div>
                <div style="font-weight:700; font-size:1.15rem;">{weather_data.get('swell_wave_height') if weather_data.get('swell_wave_height') is not None else '—'}</div>
                <div style="font-size:0.7rem;">m</div>
            </div>
            <div style="background:rgba(14, 165, 233, 0.15); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.8;">WIND WAVE</div>
                <div style="font-weight:700; font-size:1.15rem;">{weather_data.get('wind_wave_height') if weather_data.get('wind_wave_height') is not None else '—'}</div>
                <div style="font-size:0.7rem;">m</div>
            </div>
        </div>
        """
    else:
        ocean_section = """
        <div style="margin-top:16px; padding:12px; background:rgba(14,165,233,0.12); border-radius:12px; text-align:center; font-size:0.88rem; color:#7dd3fc;">
            🌊 Oceanographic data is only available for <b>coastal locations</b>.
        </div>
        """

    html = f"""
    <div style="
        background: rgba(10, 30, 55, 0.82);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 20px;
        padding: 22px;
        color: white;
        margin: 12px 0 20px;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
            <div style="font-size:1.25rem; font-weight:700;">📍 {location_name}</div>
            <div style="background:{accent}; color:white; padding:5px 14px; border-radius:50px; font-size:0.8rem; font-weight:700;">
                {weather_data.get('safety_status')}
            </div>
        </div>

        <div style="text-align:center; margin-bottom:12px;">
            <span style="font-size:3.4rem; font-weight:300;">{weather_data.get('temperature', '--')}</span>
            <span style="font-size:1.5rem; opacity:0.7;">°C</span>
            <div style="font-size:0.95rem; opacity:0.85; margin-top:2px;">
                Feels like {weather_data.get('feels_like', '--')}°C • {weather_data.get('weather_desc', '')}
            </div>
        </div>

        <div style="font-size:0.9rem; font-weight:600; margin:14px 0 8px; color:#7dd3fc;">🌤 Meteorological Data</div>
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; margin-bottom:16px;">
            <div style="background:rgba(255,255,255,0.07); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.7;">WIND</div>
                <div style="font-weight:700; font-size:1.1rem;">{weather_data.get('wind_speed', '--')}</div>
                <div style="font-size:0.7rem;">km/h</div>
            </div>
            <div style="background:rgba(255,255,255,0.07); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.7;">DIRECTION</div>
                <div style="font-weight:700; font-size:1.05rem;">{deg_to_compass(weather_data.get('wind_direction'))}</div>
                <div style="font-size:0.7rem;">{weather_data.get('wind_direction', '--')}°</div>
            </div>
            <div style="background:rgba(255,255,255,0.07); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.7;">GUSTS</div>
                <div style="font-weight:700; font-size:1.1rem;">{weather_data.get('wind_gusts') or '—'}</div>
                <div style="font-size:0.7rem;">km/h</div>
            </div>
            <div style="background:rgba(255,255,255,0.07); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.7;">HUMIDITY</div>
                <div style="font-weight:700; font-size:1.1rem;">{weather_data.get('humidity', '--')}%</div>
            </div>
            <div style="background:rgba(255,255,255,0.07); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.7;">PRESSURE</div>
                <div style="font-weight:700; font-size:1.05rem;">{round(weather_data.get('pressure_msl') or 0)}</div>
                <div style="font-size:0.7rem;">hPa</div>
            </div>
            <div style="background:rgba(255,255,255,0.07); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.7;">CLOUD</div>
                <div style="font-weight:700; font-size:1.1rem;">{weather_data.get('cloud_cover', '--')}%</div>
            </div>
            <div style="background:rgba(255,255,255,0.07); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.7;">VISIBILITY</div>
                <div style="font-weight:700; font-size:1.05rem;">
                    {round((weather_data.get('visibility') or 0)/1000, 1) if weather_data.get('visibility') else '—'}
                </div>
                <div style="font-size:0.7rem;">km</div>
            </div>
            <div style="background:rgba(255,255,255,0.07); border-radius:12px; padding:10px; text-align:center;">
                <div style="font-size:0.7rem; opacity:0.7;">RAIN</div>
                <div style="font-weight:700; font-size:1.1rem;">{weather_data.get('precipitation') or 0}</div>
                <div style="font-size:0.7rem;">mm</div>
            </div>
        </div>

        {ocean_section}

        <div style="margin-top:14px; font-size:0.85rem; opacity:0.85; text-align:center;">
            {weather_data.get('safety_message', '')}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_pfz_section(pfz_data):
    if not pfz_data or pfz_data.get("status") != "success":
        return
    best = pfz_data["best_zone"]
    c1, c2 = st.columns([2, 1])
    with c1:
        st.success(f"🎯 **Best PFZ:** {best['name']} ({best['distance']}) | SST: {best['sst']}°C")
        st.caption(f"⚓ Port: {pfz_data.get('harbour_name')}")
    with c2:
        st.metric("PFZ Score", f"{best['score']}/100", pfz_data["recommendation"])
    st.caption(f"🌡️ Harbour SST: {pfz_data['sst']}°C | 🟢 Chlorophyll proxy: {pfz_data['chlorophyll']}")
    st.info(pfz_data.get("note", ""))

# ====================== UI ======================
st.set_page_config(
    page_title="Marine Intelligence Platform",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {
    background-image: linear-gradient(rgba(0, 40, 80, 0.35), rgba(0, 30, 60, 0.45)),
                      url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-repeat: no-repeat;
}
.main .block-container {
    background: transparent !important;
    padding-top: 1.5rem !important;
}
[data-testid="stSidebar"] {
    background: rgba(8, 30, 55, 0.88) !important;
    backdrop-filter: blur(18px);
    border-right: 1px solid rgba(255,255,255,0.12);
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
h1, h2, h3, h4 {
    color: white !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.4);
}
.st-key-chat_dock_container {
    position: fixed !important;
    bottom: 18px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(920px, 94vw) !important;
    z-index: 999999 !important;
    background: rgba(10, 30, 55, 0.92) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(56, 189, 248, 0.45) !important;
    border-radius: 22px !important;
    padding: 10px 16px !important;
    box-shadow: 0 -10px 40px rgba(0,0,0,0.5) !important;
}
.bottom-scroll-spacer { height: 130px; }
.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

if "language" not in st.session_state: st.session_state.language = "English"
if "messages" not in st.session_state: st.session_state.messages = []
if "map_location" not in st.session_state: st.session_state.map_location = None
if "pfz_data" not in st.session_state: st.session_state.pfz_data = None
if "selected_zone_index" not in st.session_state: st.session_state.selected_zone_index = 0
if "boat_speed_knots" not in st.session_state: st.session_state.boat_speed_knots = 10
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None
if "pending_prompt" not in st.session_state: st.session_state.pending_prompt = None
if "auto_speak" not in st.session_state: st.session_state.auto_speak = True
if "voice_mode_triggered" not in st.session_state: st.session_state.voice_mode_triggered = False
if "show_alerts_panel" not in st.session_state: st.session_state.show_alerts_panel = False

now = datetime.now(ZoneInfo("Asia/Kolkata"))

st.markdown(f"""
<div style="
    background: rgba(15, 40, 70, 0.75);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 18px;
    padding: 16px 24px;
    margin-bottom: 18px;
    color: white;
">
    <div style="font-size:1.1rem; font-weight:600;">
        📅 {now.strftime('%d %B %Y')} &nbsp;&nbsp;|&nbsp;&nbsp; 🕒 {now.strftime('%I:%M %p')}
    </div>
    <div style="font-size:0.88rem; opacity:0.9; margin-top:4px;">
        Multi-language Voice-to-Text Marine Intelligence Platform • 9 Languages Supported • Real-time Ocean + Weather + Geofencing
    </div>
</div>
""", unsafe_allow_html=True)

# Live Coastal Monitoring
st.markdown("""
<div style="
    background: rgba(15, 40, 70, 0.72);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 18px;
    padding: 18px 20px 22px;
    margin-bottom: 16px;
">
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
        <span style="font-size:1.35rem;">📡</span>
        <span style="font-size:1.25rem; font-weight:700; color:white;">Live Coastal Monitoring</span>
    </div>
    <div style="font-size:0.85rem; color:#94a3b8;">SST + Waves + Wind from Open-Meteo | Auto-refreshes every ~2 mins</div>
</div>
""", unsafe_allow_html=True)

col_a1, col_a2, col_a3 = st.columns([1.3, 1.1, 1.6])
with col_a1:
    if st.button("🚨 View Active Alerts", use_container_width=True, type="primary"):
        st.session_state.show_alerts_panel = True
with col_a2:
    if st.button("🔄 Refresh Monitoring", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with col_a3:
    st.caption(f"Monitoring {len(COASTAL_LOCATIONS)} coastal locations")

monitor_data = cached_continuous_monitor()
if not monitor_data:
    st.warning("⚠️ Monitoring temporarily unavailable. Click **Refresh Monitoring**.")
else:
    render_monitoring_dashboard(monitor_data)

if st.session_state.show_alerts_panel:
    st.markdown("---")
    render_active_alerts_panel(st.session_state.language)
    if st.button("Close Alerts Panel"):
        st.session_state.show_alerts_panel = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ====================== SIDEBAR ======================
with st.sidebar:
    st.markdown("### 🌐 Language / भाषा")
    language_options = list(SUPPORTED_LANGUAGES.keys())
    language = st.selectbox(
        "Select Language",
        language_options,
        index=language_options.index(st.session_state.language) if st.session_state.language in language_options else 0,
        format_func=lambda x: f"{SUPPORTED_LANGUAGES[x]['name']} ({x})"
    )
    st.session_state.language = language

    current_lang_info = SUPPORTED_LANGUAGES[language]
    st.caption(f"Voice language: **{current_lang_info['name']}** (`{current_lang_info['speech_recognition']}`)")

    st.markdown("---")
    st.markdown("### 🔊 Voice & Speech")
    st.session_state.auto_speak = st.toggle("Auto-Speak Responses", value=st.session_state.auto_speak)

    st.markdown("---")
    st.markdown("### 🚤 Vessel Speed")
    speed_option = st.selectbox(
        "Boat Type",
        ["Motorized Boat (8 knots)", "Mechanized Trawler (10 knots)", "Fiber Speedboat (16 knots)"],
        index=1
    )
    st.session_state.boat_speed_knots = 8 if "8 knots" in speed_option else 16 if "16 knots" in speed_option else 10

    st.markdown("---")
    st.markdown("### 🛡️ Geofencing")
    st.caption("Circular zones around major harbours")
    for name in GEOFENCES:
        st.markdown(f"- {name}")

    st.markdown("---")
    st.markdown("### 🆘 24×7 Helpline")
    st.link_button("💬 WhatsApp", f"https://wa.me/{WHATSAPP_NUMBER}?text={quote('Hello, I need marine help.')}", use_container_width=True)
    st.markdown(f'<a href="tel:{PHONE_NUMBER}"><button style="width:100%;padding:10px;background:#25D366;color:white;border:none;border-radius:10px;cursor:pointer;font-weight:600;">📞 Call</button></a>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💡 Try Asking")
    st.markdown("""
    - Weather in Delhi  
    - Is it safe in Goa?  
    - Best PFZ near Kochi  
    - Geofence in Mumbai  
    - Show active alerts  
    """)

# Chat history
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg.get("weather_data"):
            render_full_ocean_meteo_card(msg["weather_data"], msg.get("location_name", "Location"))
        if msg.get("alert_data"):
            render_alert_banner(msg["alert_data"])
        if msg.get("pfz_data"):
            render_pfz_section(msg["pfz_data"])
        if msg.get("show_geofence") and msg.get("lat") and msg.get("lon"):
            render_geofence_status(msg["lat"], msg["lon"], msg.get("location_name", "Location"))
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_tts_button(msg["content"], st.session_state.language, auto_play=False, msg_id=f"hist_{idx}")
        if msg.get("agent_log"):
            st.caption(f"🧠 **Agents:** {' → '.join(msg['agent_log'])}")

# Map + Geofences
if st.session_state.map_location and st.session_state.map_location.get("is_coastal", True):
    loc = st.session_state.map_location
    harbour_name = loc.get("harbour_name", f"{loc['name']} Harbour")
    origin_lat = loc.get("harbour_lat", loc["lat"])
    origin_lon = loc.get("harbour_lon", loc["lon"])

    st.markdown("---")
    st.subheader(f"🛰️ Satellite Map + Geofences — {loc['name']}")

    has_pfz = st.session_state.pfz_data and st.session_state.pfz_data.get("status") == "success"
    all_routes = []

    if has_pfz:
        zones = st.session_state.pfz_data["all_zones"]
        for i, zone in enumerate(zones):
            r = generate_marine_route(origin_lat, origin_lon, zone["lat"], zone["lon"],
                                      harbour_name, zone["name"], st.session_state.boat_speed_knots)
            r["zone"] = zone
            r["color"] = ROUTE_COLORS[i]["hex"]
            r["label"] = ROUTE_COLORS[i]["label"]
            all_routes.append(r)

        st.markdown("#### 🧭 Routes Comparison")
        cols = st.columns(3)
        for i, r in enumerate(all_routes):
            z = r["zone"]
            is_active = (i == st.session_state.selected_zone_index)
            border_color = r["color"] if is_active else "rgba(255,255,255,0.12)"
            with cols[i]:
                st.markdown(f"""
                    <div style="background:rgba(30,41,59,0.85); border-radius:14px; padding:15px; color:white; border:2px solid {border_color};">
                        <div style="display:flex; justify-content:space-between;">
                            <span style="background:{r['color']}; color:#000; font-weight:800; font-size:0.75rem; padding:2px 8px; border-radius:10px;">{r['label']}</span>
                            <span style="font-size:0.85rem;">Score: <b>{z['score']}/100</b></span>
                        </div>
                        <div style="font-size:1.05rem; font-weight:700; margin:8px 0 4px;">{z['name']}</div>
                        <div style="font-size:0.85rem;">📍 {r['distance_km']} km ({r['distance_nm']} NM)</div>
                        <div style="font-size:0.85rem;">⏱️ {r['eta']}</div>
                        <div style="font-size:0.85rem;">🧭 {r['bearing']}° ({r['compass_dir']})</div>
                    </div>
                """, unsafe_allow_html=True)
                st.link_button(f"📍 Open in Google Maps", r["gmaps_url"], use_container_width=True)

        active_zone_type = st.radio("Select Active Route:", ["🟢 Primary", "🔵 Secondary", "🟠 Alternate"],
                                    index=st.session_state.selected_zone_index, horizontal=True)
        st.session_state.selected_zone_index = 0 if "Primary" in active_zone_type else 1 if "Secondary" in active_zone_type else 2

    m = folium.Map(location=[origin_lat, origin_lon], zoom_start=10, tiles=None)
    folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri", name="Satellite").add_to(m)
    folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", attr="Esri", name="Labels", overlay=True).add_to(m)
    folium.Marker([origin_lat, origin_lon], popup=f"<b>{harbour_name}</b>", tooltip=harbour_name, icon=folium.Icon(color="red", icon="info-sign")).add_to(m)

    for name, fence in GEOFENCES.items():
        center = fence["center"]
        folium.Circle(
            location=center,
            radius=fence["radius_km"] * 1000,
            color=fence["color"],
            fill=True,
            fill_color=fence["color"],
            fill_opacity=0.15,
            weight=2,
            popup=f"<b>{name}</b><br>{fence['description']}<br>Radius: {fence['radius_km']} km",
            tooltip=name
        ).add_to(m)
        folium.CircleMarker(location=center, radius=6, color=fence["color"], fill=True, fill_color=fence["color"], fill_opacity=0.9, popup=name).add_to(m)

    if has_pfz:
        for i, r in enumerate(all_routes):
            z = r["zone"]
            is_active = (i == st.session_state.selected_zone_index)
            folium.PolyLine(locations=r["waypoints"], color=r["color"], weight=6 if is_active else 3.5,
                            opacity=1.0 if is_active else 0.7, dash_array=None if is_active else "7,9").add_to(m)
            folium.Marker([z["lat"], z["lon"]], popup=f"<b>{z['name']}</b><br>Score: {z['score']}",
                          tooltip=f"🎯 {z['name']}", icon=folium.Icon(color="green" if i==0 else "blue" if i==1 else "orange")).add_to(m)

        all_lats = [origin_lat] + [r["zone"]["lat"] for r in all_routes]
        all_lons = [origin_lon] + [r["zone"]["lon"] for r in all_routes]
        m.fit_bounds([[min(all_lats)-0.03, min(all_lons)-0.03], [max(all_lats)+0.03, max(all_lons)+0.03]])

    folium.LayerControl().add_to(m)
    st_folium(m, width=900, height=480, returned_objects=[], key=f"map_{loc['name']}_{st.session_state.selected_zone_index}")

st.markdown("<div class='bottom-scroll-spacer'></div>", unsafe_allow_html=True)

# ====================== CHAT DOCK WITH MULTI-LANGUAGE VOICE ======================
def submit_text():
    text = st.session_state.get("user_typed_input", "").strip()
    if text:
        st.session_state.pending_prompt = text
        st.session_state.user_typed_input = ""

current_lang = st.session_state.language
lang_info = SUPPORTED_LANGUAGES[current_lang]
speech_lang = lang_info["speech_recognition"]
whisper_lang = lang_info["whisper"]

with st.container(key="chat_dock_container"):
    # Language indicator
    st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
            <span style="font-size:0.75rem; color:#38bdf8; font-weight:600;">Voice Language:</span>
            <span style="background:rgba(56,189,248,0.2); border:1px solid rgba(56,189,248,0.4); color:#e2e8f0; border-radius:12px; font-size:0.72rem; padding:2px 10px;">
                {lang_info['name']} ({speech_lang})
            </span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="display:flex; gap:8px; margin-bottom:8px; overflow-x:auto; padding-bottom:4px;">
            <span style="font-size:0.75rem; color:#38bdf8; font-weight:600; align-self:center;">Quick:</span>
            <button onclick="window.submitMarinePrompt && window.submitMarinePrompt('Is it safe to fish in Goa?', false)" 
                style="background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.4); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:3px 12px; cursor:pointer;">🌊 Goa Safety</button>
            <button onclick="window.submitMarinePrompt && window.submitMarinePrompt('Show active alerts', false)" 
                style="background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.4); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:3px 12px; cursor:pointer;">🚨 Alerts</button>
            <button onclick="window.submitMarinePrompt && window.submitMarinePrompt('Best PFZ near Kochi', false)" 
                style="background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.4); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:3px 12px; cursor:pointer;">🎯 Kochi PFZ</button>
            <button onclick="window.submitMarinePrompt && window.submitMarinePrompt('Geofence status in Mumbai', false)" 
                style="background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.4); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:3px 12px; cursor:pointer;">🛡️ Geofence</button>
        </div>
        <script>
        window.submitMarinePrompt = function(text, isVoice) {
            if (!text || !text.trim()) return;
            var u = new URL(window.location.href);
            u.searchParams.set('v_prompt', text.trim());
            if (isVoice) u.searchParams.set('from_voice', '1');
            window.location.href = u.toString();
        };
        </script>
    """, unsafe_allow_html=True)

    input_col, mic_col, send_col = st.columns([5.0, 1.8, 1.0])
    with input_col:
        st.text_input(
            "Ask anything...",
            placeholder=f"Type or speak in {lang_info['name']}... (Weather in Delhi, गोवा में मौसम, etc.)",
            key="user_typed_input",
            on_change=submit_text,
            label_visibility="collapsed"
        )
    with mic_col:
        # Multi-language Live Speak button
        st.markdown(f"""
            <button onclick="
                var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SR) {{ 
                    alert('Please use Chrome or Edge browser for Live Speak.\\nFor best accuracy use High-Accuracy Voice (Whisper) below.'); 
                    return; 
                }}
                var b = this; 
                b.style.background='#dc2626'; 
                b.innerHTML='🔴 Listening...';
                var r = new SR(); 
                r.lang = '{speech_lang}'; 
                r.interimResults = true;
                r.continuous = false;
                r.onresult = function(e) {{
                    if (e.results[0].isFinal) {{
                        b.style.background='#16a34a'; 
                        b.innerHTML='✅ Done';
                        window.submitMarinePrompt(e.results[0][0].transcript, true);
                    }}
                }};
                r.onerror = function(e) {{
                    console.log('Speech error:', e.error);
                    b.style.background='#0284c7'; 
                    b.innerHTML='🎙️ Live Speak';
                    if(e.error === 'not-allowed') alert('Microphone permission denied');
                    else if(e.error === 'no-speech') alert('No speech detected. Please try again.');
                }};
                r.onend = function() {{ 
                    setTimeout(function(){{
                        b.style.background='#0284c7'; 
                        b.innerHTML='🎙️ Live Speak';
                    }}, 1500); 
                }};
                r.start();
            " style="width:100%; height:42px; background:#0284c7; color:white; border:none; border-radius:12px; font-weight:700; cursor:pointer;">
                🎙️ Live Speak
            </button>
        """, unsafe_allow_html=True)
    with send_col:
        st.button("Send ➤", on_click=submit_text, use_container_width=True, type="primary")

    # High-Accuracy Multi-Language Whisper
    with st.expander(f"🎙️ High-Accuracy Voice (Whisper) — {lang_info['name']}", expanded=False):
        st.caption(f"Best accuracy for **{lang_info['name']}**. Record your voice below.")
        audio_file = st.audio_input(
            f"Record in {lang_info['name']}",
            label_visibility="collapsed",
            key="dock_mic_input"
        )

# Handle Live Speak query params
if "v_prompt" in st.query_params:
    voice_text = str(st.query_params.get("v_prompt", "")).strip()
    is_from_voice = str(st.query_params.get("from_voice", "1")) == "1"
    try:
        del st.query_params["v_prompt"]
        if "from_voice" in st.query_params: del st.query_params["from_voice"]
    except: pass
    if voice_text:
        st.session_state.pending_prompt = voice_text
        if is_from_voice: st.session_state.voice_mode_triggered = True
        st.toast(f"🗣️ Heard ({lang_info['name']}): {voice_text}", icon="🎙️")

# Handle High-Accuracy Whisper
if audio_file is not None:
    try:
        audio_bytes = audio_file.getvalue()
    except:
        audio_bytes = audio_file.read()

    if audio_bytes and len(audio_bytes) > 200:
        audio_hash = hashlib.md5(audio_bytes).hexdigest()
        if st.session_state.last_audio_hash != audio_hash:
            st.session_state.last_audio_hash = audio_hash
            with st.spinner(f"🎧 Transcribing in {lang_info['name']}..."):
                transcribed = transcribe_voice_query(audio_bytes, st.session_state.language)
                if transcribed:
                    st.session_state.pending_prompt = transcribed
                    st.session_state.voice_mode_triggered = True
                    st.toast(f"🗣️ {lang_info['name']}: {transcribed}", icon="🎙️")
                else:
                    st.toast("Could not detect speech clearly. Please try again.", icon="⚠️")

# Main Orchestration
active_prompt = None
if st.session_state.pending_prompt:
    active_prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if active_prompt:
    st.session_state.messages.append({"role": "user", "content": active_prompt})

    with st.chat_message("user"):
        st.markdown(active_prompt)

    with st.chat_message("assistant"):
        nlp_plan = advanced_nlp_agent(active_prompt)
        weather_data = pfz_data = alert_data = location_name = None
        show_geofence = False
        lat = lon = None
        agent_log = [f"NLP ({nlp_plan['intent']})"]

        if nlp_plan["intent"] in ["GREETING", "BOT_IDENTITY", "GRATITUDE", "NORMAL_CHAT"]:
            st.session_state.map_location = None
            st.session_state.pfz_data = None

        if nlp_plan["intent"] == "SHOW_ALERTS":
            agent_log.append("Real-Time Alert Agent")
            st.session_state.show_alerts_panel = True
            render_active_alerts_panel(st.session_state.language)

        if nlp_plan["needs_weather"] and nlp_plan.get("location"):
            loc = nlp_plan["location"]
            location_name = loc["name"]
            if loc.get("state"):
                location_name = f"{loc['name']}, {loc['state']}"

            weather_data = weather_agent(loc["lat"], loc["lon"])
            agent_log.append("Weather + Ocean Agent")
            render_full_ocean_meteo_card(weather_data, location_name)

            show_geofence = True
            lat = loc["lat"]
            lon = loc["lon"]
            agent_log.append("Geofencing Agent")
            render_geofence_status(lat, lon, location_name)

            is_coastal = nlp_plan.get("is_coastal", False)
            alert_data = alert_agent(weather_data, location_name, st.session_state.language, is_coastal=is_coastal)
            agent_log.append(f"Alert ({alert_data['level']})")
            render_alert_banner(alert_data)

            if nlp_plan.get("is_coastal") and nlp_plan.get("needs_pfz"):
                st.session_state.map_location = loc
                st.session_state.map_location["is_coastal"] = True
                pfz_data = pfz_agent(loc, weather_data)
                st.session_state.pfz_data = pfz_data
                st.session_state.selected_zone_index = 0
                agent_log.append("PFZ + Navigation + Geofences")
                render_pfz_section(pfz_data)
            else:
                st.session_state.map_location = None
                st.session_state.pfz_data = None

        agent_log.append(f"Response Agent ({st.session_state.language})")
        final_answer = response_agent(active_prompt, nlp_plan, weather_data, pfz_data, alert_data, st.session_state.language)
        st.markdown(final_answer)

        should_speak = st.session_state.get("voice_mode_triggered", False) or st.session_state.get("auto_speak", False)
        render_tts_button(final_answer, st.session_state.language, auto_play=should_speak, msg_id="latest")
        st.session_state.voice_mode_triggered = False
        st.caption(f"🧠 **Agents:** {' → '.join(agent_log)} | Language: **{st.session_state.language}**")

    st.session_state.messages.append({
        "role": "assistant",
        "content": final_answer,
        "weather_data": weather_data,
        "pfz_data": pfz_data,
        "alert_data": alert_data,
        "location_name": location_name,
        "show_geofence": show_geofence,
        "lat": lat,
        "lon": lon,
        "agent_log": agent_log
    })
    st.rerun()
