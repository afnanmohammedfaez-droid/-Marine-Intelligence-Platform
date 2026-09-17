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

# ====================== SOS / EMERGENCY ======================
COAST_GUARD_TOLL_FREE = "1554"          # Official Indian Coast Guard MSAR helpline
NATIONAL_EMERGENCY = "112"              # India national emergency number
POLICE = "100"
AMBULANCE = "108"
FIRE = "101"

# Regional MRCC / Coast Guard quick contacts (useful for WhatsApp/voice)
EMERGENCY_CONTACTS = {
    "Coast Guard (Toll-Free)": "1554",
    "National Emergency": "112",
    "MRCC Mumbai (West)": "+912224388065",
    "MRCC Chennai (East)": "+914425395018",
    "MRSC Kochi": "+914842218969",
    "MRSC Goa": "+918322521718",
    "MRSC Mangalore": "+918242405262",
    "MRSC Visakhapatnam": "+918912547266",
}

# Coastal locations
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

COASTAL_LOCATIONS = [
    "Kochi", "Mumbai", "Chennai", "Mangalore", "Visakhapatnam"
]

INLAND_MONITORED = ["Delhi", "Jaipur", "Hyderabad", "Bengaluru", "Kolkata", "Pune", "Ahmedabad"]
MONITORED_LOCATIONS = COASTAL_LOCATIONS.copy()

ROUTE_COLORS = {
    0: {"hex": "#00E5FF", "label": "Primary Route (Neon Cyan)"},
    1: {"hex": "#3B82F6", "label": "Secondary Route (Electric Blue)"},
    2: {"hex": "#F59E0B", "label": "Alternate Route (Amber Gold)"}
}

RE_GREETING = re.compile(r'\b(hi|hello|hey|heyy|greetings|namaste|namaskar|vanakkam|kem\s*cho|good\s*(morning|afternoon|evening|day)|kaise\s*ho|kya\s*haal|kese\s*ho|hi\s*there|hello\s*there)\b', re.IGNORECASE)
RE_IDENTITY = re.compile(r'\b(who are you|what is your name|kya ho tum|tum kaun ho|what can you do|your features|help me|what do you do|introduce yourself|tell me about yourself|how can you help)\b', re.IGNORECASE)
RE_GRATITUDE = re.compile(r'\b(thank\s*you|thanks|dhanyawad|shukriya|bye|goodbye|alvida|see you)\b', re.IGNORECASE)
RE_MARINE_CORE = re.compile(r'\b(sea|weather|wind|safe\w*|fish\w*|wave\w*|tide\w*|ocean|cyclon\w*|storm\w*|rain|boat|harbour|harbor|port|coast|pfz|navigation|direction\w*|route\w*|distance|samundar|mausam|hawa|machli|temperature|temp|humidity)\b', re.IGNORECASE)
RE_ALERT = re.compile(r'\b(alert|alerts|warning|warnings|danger|dangerous|risk|risky|emergency|caution|advisory|advisories|chetaavani|chetavani|khatra|khatre)\b', re.IGNORECASE)
RE_SOS = re.compile(r'\b(sos|s\.o\.s|mayday|distress|help\s*me|emergency\s*help|i\s*need\s*help|save\s*me|rescue|आपात|मदद|बचाओ|एसओएस|मेरे\s*को\s*मदद)\b', re.IGNORECASE)

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

# ====================== VOICE ======================
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
    if not audio_bytes or len(audio_bytes) < 100:
        return None
    filename, mime_type = get_audio_filename_and_mime(audio_bytes)
    lang_code = "en" if language == "English" else "hi"
    for model_name in ["whisper-large-v3-turbo", "whisper-large-v3"]:
        try:
            transcription = client.audio.transcriptions.create(
                file=(filename, audio_bytes, mime_type),
                model=model_name,
                language=lang_code,
                temperature=0.0
            )
            text = transcription.text.strip()
            if text:
                return text
        except Exception:
            try:
                transcription = client.audio.transcriptions.create(
                    file=(filename, audio_bytes, mime_type),
                    model=model_name,
                    temperature=0.0
                )
                text = transcription.text.strip()
                if text:
                    return text
            except Exception:
                continue
    return None

# ====================== WEATHER AGENT ======================
@st.cache_data(ttl=180, show_spinner=False)
def weather_agent(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weather_code,precipitation,cloud_cover",
            "timezone": "Asia/Kolkata"
        }
        response = requests.get(url, params=params, timeout=8)
        if response.status_code != 200:
            return {"status": "error", "message": f"Weather API Error: {response.status_code}"}

        data = response.json()
        current = data.get("current", {})
        if not current:
            return {"status": "error", "message": "No weather data received"}

        wind_speed = current.get("wind_speed_10m", 0) or 0

        marine_url = "https://marine-api.open-meteo.com/v1/marine"
        marine_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "sea_surface_temperature,wave_height,wave_direction,wave_period,ocean_current_velocity",
            "timezone": "Asia/Kolkata"
        }
        marine_resp = requests.get(marine_url, params=marine_params, timeout=6)
        sst = wave_height = wave_period = current_velocity = None
        if marine_resp.status_code == 200:
            mdata = marine_resp.json().get("current", {})
            sst = mdata.get("sea_surface_temperature")
            wave_height = mdata.get("wave_height")
            wave_period = mdata.get("wave_period")
            current_velocity = mdata.get("ocean_current_velocity")

        if wind_speed < 15 and (wave_height is None or wave_height < 1.5):
            safety_status = "Safe"
            safety_color = "green"
            safety_message = "Conditions appear favourable."
            prediction = "Favourable conditions expected."
        elif wind_speed < 25 and (wave_height is None or wave_height < 2.5):
            safety_status = "Moderately Safe"
            safety_color = "orange"
            safety_message = "Exercise caution. Wind is moderate."
            prediction = "Moderate conditions. Stay alert."
        else:
            safety_status = "Not Safe"
            safety_color = "red"
            safety_message = "High wind speed or rough conditions. Be careful."
            prediction = "Unfavourable conditions expected."

        return {
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": round(wind_speed, 1),
            "wind_direction": current.get("wind_direction_10m"),
            "precipitation": current.get("precipitation"),
            "cloud_cover": current.get("cloud_cover"),
            "sea_surface_temperature": round(sst, 1) if sst is not None else None,
            "wave_height": round(wave_height, 2) if wave_height is not None else None,
            "wave_period": round(wave_period, 1) if wave_period is not None else None,
            "ocean_current_velocity": round(current_velocity, 2) if current_velocity is not None else None,
            "safety_status": safety_status,
            "safety_color": safety_color,
            "safety_message": safety_message,
            "prediction": prediction,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ====================== OCEANOGRAPHIC + METEOROLOGICAL DATA (NEW FEATURE) ======================
@st.cache_data(ttl=180, show_spinner=False)
def fetch_ocean_met_data(lat, lon, location_name="Location"):
    """
    Isolated feature: richer oceanographic + meteorological snapshot.
    Does NOT modify weather_agent / PFZ / Alert / NLP agents.
    """
    try:
        # Meteorological (atmosphere)
        met_url = "https://api.open-meteo.com/v1/forecast"
        met_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility,cloud_cover,precipitation,weather_code",
            "timezone": "Asia/Kolkata"
        }
        met_resp = requests.get(met_url, params=met_params, timeout=8)
        met = {}
        if met_resp.status_code == 200:
            met = met_resp.json().get("current", {}) or {}

        # Oceanographic (marine)
        marine_url = "https://marine-api.open-meteo.com/v1/marine"
        marine_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "sea_surface_temperature,wave_height,wave_direction,wave_period,ocean_current_velocity,ocean_current_direction",
            "timezone": "Asia/Kolkata"
        }
        marine_resp = requests.get(marine_url, params=marine_params, timeout=6)
        ocean = {}
        if marine_resp.status_code == 200:
            ocean = marine_resp.json().get("current", {}) or {}

        def _r(v, nd=1):
            return round(v, nd) if v is not None else None

        return {
            "status": "success",
            "location": location_name,
            "timestamp": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p"),
            # Meteorological
            "temperature": _r(met.get("temperature_2m")),
            "apparent_temperature": _r(met.get("apparent_temperature")),
            "humidity": met.get("relative_humidity_2m"),
            "pressure_msl": _r(met.get("pressure_msl"), 1),
            "surface_pressure": _r(met.get("surface_pressure"), 1),
            "wind_speed": _r(met.get("wind_speed_10m")),
            "wind_direction": met.get("wind_direction_10m"),
            "wind_gusts": _r(met.get("wind_gusts_10m")),
            "visibility_m": met.get("visibility"),
            "cloud_cover": met.get("cloud_cover"),
            "precipitation": _r(met.get("precipitation"), 2),
            "weather_code": met.get("weather_code"),
            # Oceanographic
            "sst": _r(ocean.get("sea_surface_temperature")),
            "wave_height": _r(ocean.get("wave_height"), 2),
            "wave_direction": ocean.get("wave_direction"),
            "wave_period": _r(ocean.get("wave_period")),
            "current_velocity": _r(ocean.get("ocean_current_velocity"), 2),
            "current_direction": ocean.get("ocean_current_direction"),
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "location": location_name}


def render_ocean_met_panel(data):
    """Beautiful dual-panel UI for Oceanographic + Meteorological data (isolated)."""
    if not data or data.get("status") != "success":
        st.warning("Oceanographic & meteorological data temporarily unavailable.")
        return

    loc = data.get("location", "Location")
    ts = data.get("timestamp", "")

    def val(v, unit=""):
        return f"{v}{unit}" if v is not None else "—"

    def deg_arrow(d):
        if d is None:
            return "—"
        return f"{d}°"

    st.markdown(f"""
    <div style="
        background: rgba(15, 40, 70, 0.78);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 18px;
        padding: 18px 20px 10px;
        margin: 18px 0 12px;
        color: white;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:6px;">
            <div style="font-size:1.2rem; font-weight:700;">🌊 Oceanographic & ☁️ Meteorological Data — {loc}</div>
            <div style="font-size:0.78rem; opacity:0.8;">🕒 {ts} · Open-Meteo</div>
        </div>
        <div style="font-size:0.82rem; color:#94a3b8; margin-bottom:14px;">
            Real-time atmosphere + ocean parameters (isolated feature — does not alter agents)
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_met, col_ocean = st.columns(2)

    with col_met:
        st.markdown(f"""
        <div style="
            background: linear-gradient(160deg, rgba(30,58,138,0.55), rgba(15,23,42,0.7));
            border: 1px solid rgba(147,197,253,0.25);
            border-radius: 16px; padding: 16px; color: white; min-height: 280px;
        ">
            <div style="font-size:1.05rem; font-weight:700; margin-bottom:12px;">☁️ Meteorological</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.88rem;">
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">AIR TEMP</div>
                    <div style="font-weight:700; font-size:1.15rem;">{val(data.get('temperature'), '°C')}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">FEELS LIKE</div>
                    <div style="font-weight:700; font-size:1.15rem;">{val(data.get('apparent_temperature'), '°C')}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">HUMIDITY</div>
                    <div style="font-weight:700; font-size:1.15rem;">{val(data.get('humidity'), '%')}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">PRESSURE (MSL)</div>
                    <div style="font-weight:700; font-size:1.15rem;">{val(data.get('pressure_msl'), ' hPa')}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">WIND / GUSTS</div>
                    <div style="font-weight:700; font-size:1.05rem;">{val(data.get('wind_speed'), ' km/h')} / {val(data.get('wind_gusts'), '')}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">WIND DIR</div>
                    <div style="font-weight:700; font-size:1.15rem;">{deg_arrow(data.get('wind_direction'))}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">VISIBILITY</div>
                    <div style="font-weight:700; font-size:1.05rem;">{val(round(data.get('visibility_m')/1000, 1) if data.get('visibility_m') is not None else None, ' km')}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">CLOUD / RAIN</div>
                    <div style="font-weight:700; font-size:1.05rem;">{val(data.get('cloud_cover'), '%')} / {val(data.get('precipitation'), ' mm')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_ocean:
        st.markdown(f"""
        <div style="
            background: linear-gradient(160deg, rgba(6,78,59,0.55), rgba(15,23,42,0.7));
            border: 1px solid rgba(52,211,153,0.25);
            border-radius: 16px; padding: 16px; color: white; min-height: 280px;
        ">
            <div style="font-size:1.05rem; font-weight:700; margin-bottom:12px;">🌊 Oceanographic</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.88rem;">
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">SEA SURFACE TEMP</div>
                    <div style="font-weight:700; font-size:1.15rem;">{val(data.get('sst'), '°C')}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">WAVE HEIGHT</div>
                    <div style="font-weight:700; font-size:1.15rem;">{val(data.get('wave_height'), ' m')}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">WAVE PERIOD</div>
                    <div style="font-weight:700; font-size:1.15rem;">{val(data.get('wave_period'), ' s')}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">WAVE DIR</div>
                    <div style="font-weight:700; font-size:1.15rem;">{deg_arrow(data.get('wave_direction'))}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">CURRENT SPEED</div>
                    <div style="font-weight:700; font-size:1.15rem;">{val(data.get('current_velocity'), ' m/s')}</div>
                </div>
                <div style="background:rgba(255,255,255,0.07); border-radius:10px; padding:10px;">
                    <div style="opacity:0.7; font-size:0.7rem;">CURRENT DIR</div>
                    <div style="font-weight:700; font-size:1.15rem;">{deg_arrow(data.get('current_direction'))}</div>
                </div>
            </div>
            <div style="margin-top:12px; font-size:0.75rem; opacity:0.75; text-align:center;">
                Data source: Open-Meteo Marine + Forecast APIs
            </div>
        </div>
        """, unsafe_allow_html=True)


@st.cache_data(ttl=120, show_spinner=False)
def cached_continuous_monitor():
    results = []
    for name in MONITORED_LOCATIONS:
        loc = next((val for val in LOCATIONS.values() if val["name"] == name), None)
        if not loc:
            continue
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
        title = f"CRITICAL ALERT — {location_name}" if language == "English" else f"गंभीर चेतावनी — {location_name}"
        message = f"High wind **{wind} km/h**" + (f" & waves **{wave} m**" if wave else "") + ". **Stay safe.**"
        action = "Avoid outdoor activities if possible." if language == "English" else "यदि संभव हो तो बाहर न जाएं।"
    elif wind >= 20 or safety == "Moderately Safe" or (wave is not None and wave >= 1.8):
        level, color, icon = "WARNING", "#F59E0B", "⚠️"
        title = f"WARNING — {location_name}" if language == "English" else f"चेतावनी — {location_name}"
        message = f"Moderate winds **{wind} km/h**" + (f" | Waves: **{wave} m**" if wave else "") + ". Exercise caution."
        action = "Stay alert and carry necessary precautions." if language == "English" else "सावधान रहें।"
    elif wind >= 12:
        level, color, icon = "ADVISORY", "#3B82F6", "ℹ️"
        title = f"ADVISORY — {location_name}" if language == "English" else f"सलाह — {location_name}"
        message = f"Wind **{wind} km/h**" + (f" | SST: **{sst}°C**" if sst else "") + ". Conditions manageable."
        action = "Monitor conditions." if language == "English" else "स्थितियों पर नज़र रखें।"
    else:
        level, color, icon = "CLEAR", "#10B981", "✅"
        title = f"ALL CLEAR — {location_name}" if language == "English" else f"सभी ठीक — {location_name}"
        message = f"Favourable conditions. Wind **{wind} km/h**" + (f" | SST: **{sst}°C**" if sst else "") + "."
        action = "Have a safe day!" if language == "English" else "सुरक्षित रहें!"

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

    active.sort(key=lambda x: (
        0 if x.get("is_coastal", False) else 1,
        level_priority.get(x["level"], 99)
    ))
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
        st.success("✅ **No active alerts** — all monitored coastal & inland locations are clear.")
        return

    st.markdown(f"### 🚨 Real-Time Alert Agent — {len(active)} Active")
    st.caption("Coastal locations are always prioritised and shown first. Data refreshes every ~90 seconds.")

    if coastal_alerts:
        st.markdown("#### 🌊 Coastal Priority Alerts (shown first)")
        for alert in coastal_alerts:
            render_alert_banner(alert)
            wa_text = quote(alert["whatsapp_text"])
            st.link_button(f"📤 Share {alert['location']} Alert on WhatsApp", f"https://wa.me/?text={wa_text}")
            st.markdown("<br>", unsafe_allow_html=True)

    if inland_alerts:
        st.markdown("#### 🏙 Inland / Rest of India Alerts")
        for alert in inland_alerts:
            render_alert_banner(alert)
            wa_text = quote(alert["whatsapp_text"])
            st.link_button(f"📤 Share {alert['location']} Alert on WhatsApp", f"https://wa.me/?text={wa_text}")
            st.markdown("<br>", unsafe_allow_html=True)

# ====================== SOS / DISTRESS FEATURE ======================
def build_sos_whatsapp_message(location_name=None, lat=None, lon=None, weather_info=None, language="English"):
    """Build a ready-to-send SOS distress message."""
    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p")
    if language == "English":
        msg = "🚨 *SOS — MARINE DISTRESS*\n\n"
        msg += f"Time: {now} (IST)\n"
        if location_name:
            msg += f"Location: *{location_name}*\n"
        if lat is not None and lon is not None:
            msg += f"Coordinates: {lat:.4f}, {lon:.4f}\n"
            msg += f"Google Maps: https://www.google.com/maps?q={lat},{lon}\n"
        if weather_info and weather_info.get("status") == "success":
            msg += f"\nCurrent conditions:\n"
            msg += f"• Wind: {weather_info.get('wind_speed', '--')} km/h\n"
            msg += f"• Wave: {weather_info.get('wave_height', '--')} m\n"
            msg += f"• Safety: {weather_info.get('safety_status', '--')}\n"
        msg += "\n*I need immediate assistance. Please contact Indian Coast Guard / Rescue.*\n"
        msg += "Call Coast Guard: 1554 | National Emergency: 112"
    else:
        msg = "🚨 *एसओएस — समुद्री आपात*\n\n"
        msg += f"समय: {now} (IST)\n"
        if location_name:
            msg += f"स्थान: *{location_name}*\n"
        if lat is not None and lon is not None:
            msg += f"निर्देशांक: {lat:.4f}, {lon:.4f}\n"
            msg += f"Google Maps: https://www.google.com/maps?q={lat},{lon}\n"
        if weather_info and weather_info.get("status") == "success":
            msg += f"\nवर्तमान स्थिति:\n"
            msg += f"• हवा: {weather_info.get('wind_speed', '--')} km/h\n"
            msg += f"• लहर: {weather_info.get('wave_height', '--')} m\n"
            msg += f"• सुरक्षा: {weather_info.get('safety_status', '--')}\n"
        msg += "\n*मुझे तुरंत सहायता चाहिए। कृपया भारतीय तटरक्षक / बचाव दल से संपर्क करें।*\n"
        msg += "तटरक्षक: 1554 | राष्ट्रीय आपात: 112"
    return msg


def render_sos_panel(language="English"):
    """Full SOS Emergency panel with one-tap actions."""
    loc = st.session_state.get("map_location")
    location_name = None
    lat = lon = None
    weather_info = None

    if loc:
        location_name = loc.get("name") or loc.get("harbour_name")
        lat = loc.get("harbour_lat") or loc.get("lat")
        lon = loc.get("harbour_lon") or loc.get("lon")
        # Try to get latest weather for the SOS message
        try:
            weather_info = weather_agent(lat, lon)
        except Exception:
            pass

    sos_msg = build_sos_whatsapp_message(location_name, lat, lon, weather_info, language)
    sos_wa_url = f"https://wa.me/?text={quote(sos_msg)}"

    # Big red SOS header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%);
        border: 3px solid #DC2626;
        border-radius: 18px;
        padding: 20px 22px;
        color: white;
        margin: 12px 0 18px;
        box-shadow: 0 0 0 0 rgba(220,38,38,0.6);
        animation: sosPulse 1.8s infinite;
    ">
        <style>
        @keyframes sosPulse {
            0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }
            70% { box-shadow: 0 0 0 18px rgba(220, 38, 38, 0); }
            100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
        }
        </style>
        <div style="font-size:1.6rem; font-weight:800; text-align:center; margin-bottom:6px;">
            🆘 SOS — EMERGENCY DISTRESS
        </div>
        <div style="text-align:center; font-size:0.95rem; opacity:0.95;">
            Indian Coast Guard & National Emergency Contacts
        </div>
    </div>
    """, unsafe_allow_html=True)

    if language == "English":
        st.markdown("### 📞 Immediate Call Actions")
    else:
        st.markdown("### 📞 तुरंत कॉल करें")

    # Call buttons row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
            <a href="tel:{COAST_GUARD_TOLL_FREE}" style="text-decoration:none;">
                <button style="width:100%; padding:16px 8px; background:#DC2626; color:white; border:none; border-radius:14px; font-weight:800; font-size:1.05rem; cursor:pointer; box-shadow:0 4px 14px rgba(220,38,38,0.45);">
                    🚨 Coast Guard<br><span style="font-size:1.3rem;">1554</span>
                </button>
            </a>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <a href="tel:{NATIONAL_EMERGENCY}" style="text-decoration:none;">
                <button style="width:100%; padding:16px 8px; background:#B91C1C; color:white; border:none; border-radius:14px; font-weight:800; font-size:1.05rem; cursor:pointer;">
                    🆘 National<br><span style="font-size:1.3rem;">112</span>
                </button>
            </a>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <a href="tel:{AMBULANCE}" style="text-decoration:none;">
                <button style="width:100%; padding:16px 8px; background:#991B1B; color:white; border:none; border-radius:14px; font-weight:700; font-size:0.95rem; cursor:pointer;">
                    🚑 Ambulance<br><span style="font-size:1.15rem;">108</span>
                </button>
            </a>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # WhatsApp SOS
    st.link_button(
        "📤 Send SOS Message on WhatsApp (with location & conditions)",
        sos_wa_url,
        use_container_width=True,
        type="primary"
    )

    # Location info if available
    if lat is not None and lon is not None:
        st.info(f"📍 **Current context location:** {location_name or 'Selected port'}  \n"
                f"Coordinates: `{lat:.4f}, {lon:.4f}`  \n"
                f"[Open in Google Maps](https://www.google.com/maps?q={lat},{lon})")
    else:
        st.warning("ℹ️ No specific location selected yet. Open a coastal port (e.g. Kochi, Goa) first so the SOS message can include coordinates. You can still call 1554 / 112 immediately.")

    # Instructions
    with st.expander("📋 What to do in a real emergency (important)", expanded=True):
        if language == "English":
            st.markdown("""
**At sea:**
1. **Call 1554** (Indian Coast Guard MSAR toll-free) or **112**.
2. If you have VHF radio → switch to **Channel 16** and say:  
   *“MAYDAY MAYDAY MAYDAY … this is [boat name] … position … nature of distress …”*
3. Share exact position (GPS or approximate distance/bearing from harbour).
4. Stay with the boat if it is still afloat. Put on life jackets.
5. Use any available flares / torch / whistle.

**On land / near harbour:**
- Call **112** or local police (**100**).
- Inform harbour master / fisheries department.

**This app SOS feature** prepares a WhatsApp message with location + current weather so you can quickly notify family, friends or rescue contacts.
            """)
        else:
            st.markdown("""
**समुद्र में:**
1. **1554** (भारतीय तटरक्षक) या **112** पर कॉल करें।
2. यदि VHF रेडियो है → **Channel 16** पर जाएं और बोलें:  
   *“MAYDAY MAYDAY MAYDAY … यह [नाव का नाम] है … स्थिति … समस्या …”*
3. सही स्थान बताएं (GPS या बंदरगाह से दूरी)।
4. नाव के साथ रहें (यदि डूबी नहीं है) और लाइफ जैकेट पहनें।

**ज़मीन / बंदरगाह पर:**
- **112** या पुलिस **100** कॉल करें।

यह ऐप SOS फीचर स्थान + मौसम के साथ WhatsApp संदेश तैयार करता है ताकि आप परिवार/बचाव दल को जल्दी सूचित कर सकें।
            """)

    # Additional regional numbers
    with st.expander("📞 More Coast Guard / MRCC numbers"):
        for name, num in EMERGENCY_CONTACTS.items():
            st.markdown(f"- **{name}**: `{num}`  → [Call](tel:{num.replace('+', '')})")

    st.caption("⚠️ This is a digital assistance tool. In real distress always use official channels (1554 / 112 / VHF 16) first.")

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

    steps = [
        {"step":1, "title":f"Depart {harbour_name}", "coords":wp1,
         "instruction":f"Cast off. Steer {bearing}° ({compass_dir}).", "distance":f"{round(dist_km*0.25,1)} km"},
        {"step":2, "title":"Clear Harbor Fairway", "coords":wp2,
         "instruction":f"Exit breakwater. Maintain heading {compass_dir}.", "distance":f"{round(dist_km*0.40,1)} km"},
        {"step":3, "title":"Mid-Course Waypoint", "coords":wp3,
         "instruction":"Deep coastal shelf. Monitor instruments.", "distance":f"{round(dist_km*0.35,1)} km"},
        {"step":4, "title":f"Arrival: {dest_name}", "coords":wp4,
         "instruction":"Arrive at PFZ. Deploy gear.", "distance":"Destination Reached"}
    ]

    gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_lat},{origin_lon}&destination={dest_lat},{dest_lon}&travelmode=driving"

    return {
        "distance_km": dist_km, "distance_nm": dist_nm, "bearing": bearing,
        "compass_dir": compass_dir, "eta": f"{hours}h {minutes}m",
        "fuel_l": fuel_est_liters, "waypoints": [wp1,wp2,wp3,wp4],
        "steps": steps, "gmaps_url": gmaps_url
    }

# ====================== NLP ======================
def get_natural_greeting(language="English"):
    if language == "English":
        return (
            "👋 **Hello! Welcome to the Marine Intelligence Platform.**\n\n"
            "I can now give you **real-time weather for any place in India** + full marine features for coastal ports.\n\n"
            "### Examples:\n"
            "- *Weather in Delhi*\n"
            "- *Temperature in Jaipur*\n"
            "- *Is it safe to fish in Goa?*\n"
            "- *Show active alerts*\n"
            "- *Best PFZ near Kochi*\n\n"
            "Just type or speak!"
        )
    else:
        return (
            "👋 **नमस्ते! मरीन इंटेलिजेंस प्लेटफ़ॉर्म में आपका स्वागत है।**\n\n"
            "अब मैं **भारत के किसी भी स्थान** का रीयल-टाइम मौसम बता सकता हूँ + तटीय बंदरगाहों के लिए पूर्ण समुद्री सुविधाएं।\n\n"
            "उदाहरण:\n"
            "- *दिल्ली का मौसम*\n"
            "- *जयपुर में तापमान*\n"
            "- *गोवा में मछली पकड़ना सुरक्षित है?*\n"
            "- *सक्रिय अलर्ट दिखाएं*"
        )

def get_natural_identity(language="English"):
    if language == "English":
        return (
            "🤖 **I am the Marine Intelligence Assistant.**\n\n"
            "I can provide:\n"
            "1. Real-time weather for **any city/town in India**\n"
            "2. Full marine safety, PFZ & navigation for coastal ports\n"
            "3. **Real-Time Alert Agent** that prioritises **coastal locations first**, then inland\n"
            "4. Live satellite maps & voice assistance\n"
            "5. **SOS Emergency Panel** — one-tap call to Coast Guard **1554** / **112** + WhatsApp distress message\n\n"
            "Try asking about Delhi, Mumbai, Kochi… or *Show active alerts* or *SOS*!"
        )
    else:
        return (
            "🤖 **मैं मरीन इंटेलिजेंस असिस्टेंट हूँ।**\n\n"
            "मैं भारत के किसी भी शहर का मौसम + तटीय क्षेत्रों की पूरी जानकारी दे सकता हूँ।\n"
            "अलर्ट एजेंट पहले तटीय क्षेत्रों को प्राथमिकता देता है।\n"
            "एसओएस पैनल: तटरक्षक **1554** / **112** पर एक टैप कॉल + WhatsApp डिस्ट्रेस संदेश।"
        )

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

        if place_candidate and place_candidate not in ["weather", "temperature", "wind", "safe", "fishing", "alert"]:
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
    has_sos = bool(RE_SOS.search(query))

    # SOS has highest priority
    if has_sos:
        intent = "SOS_EMERGENCY"
    elif has_alert and not detected_location:
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

def call_groq_llm(messages, max_tokens=350, temperature=0.3):
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
    lang_inst = "Reply in clear English." if language == "English" else "Reply in clear Hindi."

    if intent == "GREETING":
        return get_natural_greeting(language)
    elif intent == "BOT_IDENTITY":
        return get_natural_identity(language)
    elif intent == "GRATITUDE":
        return "🙏 **You're very welcome! Stay safe!** 🌊" if language == "English" else "🙏 **आपका बहुत धन्यवाद! सुरक्षित रहें!**"
    elif intent == "LOCATION_AMBIGUOUS":
        return (
            "🌊 Please tell me the city or place name.\n\n"
            "Examples: *Weather in Delhi*, *Temperature in Jaipur*, *Is it safe in Goa?*"
            if language == "English" else
            "🌊 कृपया शहर या स्थान का नाम बताएं।\n\nउदाहरण: *दिल्ली का मौसम*, *जयपुर में तापमान*"
        )
    elif intent == "SHOW_ALERTS":
        return (
            "🚨 **Real-Time Alert Agent activated.**\n\n"
            "Scanning **coastal locations first** (fishermen & harbour priority), then inland cities.\n"
            "Critical & Warning alerts appear at the top."
            if language == "English" else
            "🚨 **रीयल-टाइम अलर्ट एजेंट सक्रिय।**\n\n"
            "पहले तटीय क्षेत्रों की जाँच (मछुआरों की प्राथमिकता), फिर अंतर्देशीय शहर।"
        )
    elif intent == "SOS_EMERGENCY":
        return (
            "🆘 **SOS EMERGENCY MODE ACTIVATED**\n\n"
            "I have opened the **SOS Distress Panel** for you.\n\n"
            "**Immediate actions:**\n"
            "1. **Call Indian Coast Guard: 1554** (toll-free)\n"
            "2. **Call National Emergency: 112**\n"
            "3. If at sea with VHF → **Channel 16** (MAYDAY)\n"
            "4. Use the WhatsApp SOS button to send your location + conditions to contacts.\n\n"
            "Stay calm. Help is available. The SOS panel is now open above."
            if language == "English" else
            "🆘 **एसओएस आपात मोड सक्रिय**\n\n"
            "मैंने आपके लिए **SOS डिस्ट्रेस पैनल** खोल दिया है।\n\n"
            "**तुरंत करें:**\n"
            "1. **भारतीय तटरक्षक: 1554** (टोल-फ्री)\n"
            "2. **राष्ट्रीय आपात: 112**\n"
            "3. समुद्र में VHF हो तो **Channel 16** (MAYDAY)\n"
            "4. WhatsApp SOS बटन से स्थान + स्थिति भेजें।\n\n"
            "शांत रहें। मदद उपलब्ध है। SOS पैनल ऊपर खुला है।"
        )

    loc = nlp_plan.get("location")
    if loc and weather_info:
        loc_name = loc.get("name", "Location")
        state = loc.get("state", "")
        full_name = f"{loc_name}, {state}" if state else loc_name

        context = f"""
Location: {full_name}
Weather: Temp {weather_info.get('temperature')}°C | Wind {weather_info.get('wind_speed')} km/h | Humidity {weather_info.get('humidity')}%
Status: {weather_info.get('safety_status')}
SST: {weather_info.get('sea_surface_temperature')}°C | Wave: {weather_info.get('wave_height')} m
"""
        if pfz_info:
            context += f"\nBest PFZ: {pfz_info['best_zone']['name']} ({pfz_info['best_zone']['distance']})"

        system_prompt = f"""You are a helpful weather & marine assistant for India.
{lang_inst}
Give a clear, concise weather summary first. Mention safety status.
If PFZ data is available, highlight the best fishing zone.
Keep it short and useful."""

        response = call_groq_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query + "\n\nData:\n" + context}
        ])
        if response:
            return response

        return (
            f"📍 **Weather for {full_name}**\n\n"
            f"- Temperature: **{weather_info.get('temperature')}°C**\n"
            f"- Wind: **{weather_info.get('wind_speed')} km/h**\n"
            f"- Humidity: **{weather_info.get('humidity')}%**\n"
            f"- Status: **{weather_info.get('safety_status')}**\n"
            f"- {weather_info.get('safety_message')}"
        )

    response = call_groq_llm([
        {"role": "system", "content": f"You are a helpful assistant for Indian weather and marine information. {lang_inst}"},
        {"role": "user", "content": user_query}
    ])
    return response or "I can check weather for any place in India or marine conditions for coastal ports. Just ask!"

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
    lang_code = "en-IN" if language == "English" else "hi-IN"
    uid = f"tts_{abs(hash(speech_text[:40]))}" if not msg_id else f"tts_{msg_id}"
    auto_trigger = f"setTimeout(function(){{ playTTS_{uid}(); }}, 300);" if auto_play else ""

    html = f"""
    <div style="margin-top:8px; display:flex; align-items:center; gap:8px;">
        <button id="btn_play_{uid}" onclick="playTTS_{uid}();" style="background:linear-gradient(135deg,#0284c7,#0369a1); color:white; border:none; border-radius:8px; padding:6px 14px; font-size:0.82rem; font-weight:600; cursor:pointer;">
            🔊 Listen ({language})
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
    """Beautiful coastal monitoring cards matching the screenshot"""
    if not monitor_data:
        st.warning("Monitoring temporarily unavailable.")
        return

    color_map = {
        "Safe": "#10B981",
        "Moderately Safe": "#F59E0B",
        "Not Safe": "#EF4444"
    }

    cols = st.columns(5)
    for idx, data in enumerate(monitor_data[:5]):
        with cols[idx]:
            badge_color = color_map.get(data["safety_status"], "#3B82F6")
            sst = data.get("sst")
            wave = data.get("wave_height")
            temp = data.get("temperature")

            st.markdown(f"""
            <div style="
                background: rgba(15, 40, 70, 0.72);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255,255,255,0.18);
                border-radius: 18px;
                padding: 16px 12px;
                text-align: center;
                color: white;
                box-shadow: 0 8px 32px rgba(0,0,0,0.25);
                min-height: 160px;
            ">
                <div style="font-size:1.05rem; font-weight:700; margin-bottom:8px;">{data['name']}</div>
                <div style="
                    display:inline-block;
                    background:{badge_color};
                    color:white;
                    font-size:0.72rem;
                    font-weight:700;
                    padding:4px 12px;
                    border-radius:20px;
                    margin-bottom:12px;
                ">{data['safety_status']}</div>
                <div style="font-size:0.9rem; margin:4px 0;">💨 {data['wind_speed']} km/h</div>
                <div style="font-size:0.82rem; opacity:0.9; margin:3px 0;">
                    {f"🌊 {wave} m  |  SST {sst}°C" if wave is not None and sst is not None else f"SST {sst}°C" if sst else ""}
                </div>
                <div style="font-size:0.82rem; opacity:0.85;">Air {temp}°C</div>
            </div>
            """, unsafe_allow_html=True)

def render_weather_card(weather_data, location_name):
    if not weather_data or weather_data.get("status") != "success":
        return
    safety_color_map = {"green": "#10B981", "orange": "#F59E0B", "red": "#EF4444"}
    accent = safety_color_map.get(weather_data.get("safety_color", "green"), "#3B82F6")
    wind_deg = weather_data.get("wind_direction", 0) or 0
    sst = weather_data.get("sea_surface_temperature")
    wave = weather_data.get("wave_height")

    html = f"""
    <div style="background: linear-gradient(160deg, rgba(15,23,42,0.85) 0%, rgba(30,41,59,0.85) 100%); 
                border-radius: 20px; padding: 20px; color: white; max-width: 480px; margin: 10px 0 15px; 
                border: 1px solid rgba(255,255,255,0.15); backdrop-filter: blur(10px);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div style="font-size:1.15rem; font-weight:600;">📍 {location_name}</div>
            <div style="background:{accent}; color:white; padding:4px 12px; border-radius:50px; font-size:0.75rem; font-weight:700;">{weather_data.get('safety_status')}</div>
        </div>
        <div style="text-align:center; margin:8px 0;">
            <span style="font-size:3.2rem; font-weight:300;">{weather_data.get('temperature', '--')}</span>
            <span style="font-size:1.4rem; opacity:0.7;">°C</span>
        </div>
        <div style="text-align:center; font-size:0.9rem; opacity:0.9; margin-bottom:10px;">{weather_data.get('safety_message', '')}</div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:8px;">
            <div style="background:rgba(255,255,255,0.08); border-radius:10px; padding:10px 5px; text-align:center;">
                <div>💨</div><div style="font-weight:600;">{weather_data.get('wind_speed', '--')}</div>
                <div style="font-size:0.65rem; opacity:0.7;">WIND</div>
            </div>
            <div style="background:rgba(255,255,255,0.08); border-radius:10px; padding:10px 5px; text-align:center;">
                <div style="transform:rotate({wind_deg}deg);">➤</div><div style="font-weight:600;">{wind_deg}°</div>
                <div style="font-size:0.65rem; opacity:0.7;">DIR</div>
            </div>
            <div style="background:rgba(255,255,255,0.08); border-radius:10px; padding:10px 5px; text-align:center;">
                <div>💧</div><div style="font-weight:600;">{weather_data.get('humidity', '--')}%</div>
                <div style="font-size:0.65rem; opacity:0.7;">HUMIDITY</div>
            </div>
            <div style="background:rgba(255,255,255,0.08); border-radius:10px; padding:10px 5px; text-align:center;">
                <div>☁️</div><div style="font-weight:600;">{weather_data.get('cloud_cover', '--')}%</div>
                <div style="font-size:0.65rem; opacity:0.7;">CLOUD</div>
            </div>
        </div>
        {f'<div style="margin-top:10px; text-align:center; font-size:0.85rem;">🌊 SST: {sst}°C &nbsp;|&nbsp; Wave: {wave} m</div>' if sst or wave else ''}
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

# ---------- Beautiful Beach Background + Global Styles ----------
st.markdown("""
<style>
/* Full page beach background */
.stApp {
    background-image: linear-gradient(rgba(0, 40, 80, 0.35), rgba(0, 30, 60, 0.45)),
                      url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    background-repeat: no-repeat;
}

/* Make main content area transparent so background shows */
.main .block-container {
    background: transparent !important;
    padding-top: 1.5rem !important;
}

/* Sidebar glass style */
[data-testid="stSidebar"] {
    background: rgba(8, 30, 55, 0.88) !important;
    backdrop-filter: blur(18px);
    border-right: 1px solid rgba(255,255,255,0.12);
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

/* Headers */
h1, h2, h3, h4 {
    color: white !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.4);
}

/* Chat dock */
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

/* Floating SOS button */
.sos-float-btn {
    position: fixed !important;
    bottom: 160px !important;
    right: 22px !important;
    z-index: 999998 !important;
    width: 68px !important;
    height: 68px !important;
    border-radius: 50% !important;
    background: linear-gradient(145deg, #DC2626, #991B1B) !important;
    color: white !important;
    font-weight: 900 !important;
    font-size: 0.95rem !important;
    border: 3px solid #FEE2E2 !important;
    box-shadow: 0 6px 24px rgba(220, 38, 38, 0.55) !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    animation: sosFloatPulse 2s infinite !important;
    text-decoration: none !important;
}
@keyframes sosFloatPulse {
    0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.6); }
    70% { box-shadow: 0 0 0 16px rgba(220, 38, 38, 0); }
    100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
}

/* Buttons */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
}

/* Hide default Streamlit branding a bit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Session state
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
if "show_sos_panel" not in st.session_state: st.session_state.show_sos_panel = False

# ---------- HEADER ----------
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
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
">
    <div>
        <div style="font-size:1.1rem; font-weight:600;">
            📅 {now.strftime('%d %B %Y')} &nbsp;&nbsp;|&nbsp;&nbsp; 🕒 {now.strftime('%I:%M %p')}
        </div>
        <div style="font-size:0.88rem; opacity:0.9; margin-top:4px;">
            Instant agentic platform with real oceanographic data (Open-Meteo Marine), intelligent marine NLP, satellite maps, multi-route navigation, Alert Agent & voice assistance.
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- LIVE COASTAL MONITORING ----------
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
        <span style="font-size:1.25rem; font-weight:700; color:white;">Live Coastal Monitoring (Real Ocean Data)</span>
    </div>
    <div style="font-size:0.85rem; color:#94a3b8; margin-bottom:16px;">
        SST + Waves + Wind from Open-Meteo Marine | Auto-refreshes every ~2 mins
    </div>
</div>
""", unsafe_allow_html=True)

monitor_data = cached_continuous_monitor()
render_monitoring_dashboard(monitor_data)

# Action buttons
col_a1, col_a2, col_a3, col_a4 = st.columns([1.2, 1.1, 1.1, 1.4])
with col_a1:
    if st.button("🚨 View Active Alerts", use_container_width=True, type="primary"):
        st.session_state.show_alerts_panel = True
        st.session_state.show_sos_panel = False
with col_a2:
    if st.button("🆘 SOS EMERGENCY", use_container_width=True, type="primary"):
        st.session_state.show_sos_panel = True
        st.session_state.show_alerts_panel = False
with col_a3:
    if st.button("🔄 Refresh Monitoring", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with col_a4:
    st.caption(f"Monitoring {len(COASTAL_LOCATIONS)} coastal + {len(INLAND_MONITORED)} inland locations")

# ---------- SOS PANEL ----------
if st.session_state.show_sos_panel:
    st.markdown("---")
    render_sos_panel(st.session_state.language)
    if st.button("✖️ Close SOS Panel", key="close_sos"):
        st.session_state.show_sos_panel = False
        st.rerun()

if st.session_state.show_alerts_panel:
    st.markdown("---")
    render_active_alerts_panel(st.session_state.language)
    if st.button("Close Alerts Panel"):
        st.session_state.show_alerts_panel = False
        st.rerun()

# ---------- NEW FEATURE: Oceanographic + Meteorological Data Panel ----------
st.markdown("---")
st.markdown("""
<div style="
    background: rgba(15, 40, 70, 0.65);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 16px;
    padding: 14px 18px;
    margin-bottom: 8px;
">
    <div style="font-size:1.15rem; font-weight:700; color:white;">🌊☁️ Detailed Oceanographic & Meteorological Data</div>
    <div style="font-size:0.82rem; color:#94a3b8; margin-top:4px;">
        Select any monitored coastal port to view richer atmosphere + ocean parameters (isolated feature)
    </div>
</div>
""", unsafe_allow_html=True)

ocean_met_loc = st.selectbox(
    "Select location for detailed Ocean + Met data",
    options=COASTAL_LOCATIONS,
    index=0,
    key="ocean_met_location_selector",
    label_visibility="collapsed"
)

# Resolve coords from LOCATIONS dict
_sel_loc = next((v for v in LOCATIONS.values() if v["name"] == ocean_met_loc), None)
if _sel_loc:
    with st.spinner(f"Fetching oceanographic & meteorological data for {ocean_met_loc}..."):
        ocean_met_data = fetch_ocean_met_data(_sel_loc["lat"], _sel_loc["lon"], ocean_met_loc)
    render_ocean_met_panel(ocean_met_data)
else:
    st.info("Location not found in coastal database.")

st.markdown("<br>", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🌐 Language")
    language = st.radio("Select Language", ["English", "Hindi"],
                        index=0 if st.session_state.language == "English" else 1,
                        label_visibility="collapsed")
    st.session_state.language = language

    st.markdown("---")
    st.markdown("### 🔊 Voice & Speech")
    st.session_state.auto_speak = st.toggle("Auto-Speak Responses", value=st.session_state.auto_speak)

    st.markdown("---")
    st.markdown("### 🚤 Vessel Cruising Speed")
    speed_option = st.selectbox(
        "Select Trawler / Boat Type",
        ["Motorized Boat (8 knots)", "Mechanized Trawler (10 knots)", "Fiber Speedboat (16 knots)"],
        index=1,
        label_visibility="collapsed"
    )
    st.session_state.boat_speed_knots = 8 if "8 knots" in speed_option else 16 if "16 knots" in speed_option else 10

    st.markdown("---")
    st.markdown("### 🆘 SOS & Helpline")

    # Big SOS trigger in sidebar
    if st.button("🆘 OPEN SOS PANEL", use_container_width=True, type="primary", key="sidebar_sos"):
        st.session_state.show_sos_panel = True
        st.session_state.show_alerts_panel = False
        st.rerun()

    st.markdown(f"""
        <a href="tel:{COAST_GUARD_TOLL_FREE}" style="text-decoration:none;">
            <button style="width:100%; padding:12px; margin-top:8px; background:#DC2626; color:white; border:none; border-radius:12px; cursor:pointer; font-weight:800; font-size:1rem;">
                🚨 Call Coast Guard 1554
            </button>
        </a>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <a href="tel:{NATIONAL_EMERGENCY}" style="text-decoration:none;">
            <button style="width:100%; padding:10px; margin-top:6px; background:#B91C1C; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:700;">
                🆘 Call 112 (National Emergency)
            </button>
        </a>
    """, unsafe_allow_html=True)

    st.link_button("💬 Chat on WhatsApp (Support)", f"https://wa.me/{WHATSAPP_NUMBER}?text={quote('Hello, I need weather / marine help.')}", use_container_width=True)
    st.markdown(f'''
        <a href="tel:{PHONE_NUMBER}" style="text-decoration:none;">
            <button style="width:100%; padding:10px; background:#25D366; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:600;">
                📞 Call Platform Helpline
            </button>
        </a>
    ''', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💡 Try Asking")
    st.markdown("""
    - *Weather in Delhi*
    - *Temperature in Jaipur*
    - *Is it raining in Hyderabad?*
    - *Is it safe to fish in Goa?*
    - *Show active alerts*
    - *Best PFZ near Kochi*
    - *SOS* or *Emergency*
    """)

# Chat history
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg.get("weather_data"):
            render_weather_card(msg["weather_data"], msg.get("location_name", "Location"))
        if msg.get("alert_data"):
            render_alert_banner(msg["alert_data"])
        if msg.get("pfz_data"):
            render_pfz_section(msg["pfz_data"])
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_tts_button(msg["content"], st.session_state.language, auto_play=False, msg_id=f"hist_{idx}")
        if msg.get("agent_log"):
            st.caption(f"🧠 **Agents:** {' → '.join(msg['agent_log'])}")

# Satellite map (coastal only)
if st.session_state.map_location and st.session_state.map_location.get("is_coastal", True):
    loc = st.session_state.map_location
    harbour_name = loc.get("harbour_name", f"{loc['name']} Harbour")
    origin_lat = loc.get("harbour_lat", loc["lat"])
    origin_lon = loc.get("harbour_lon", loc["lon"])

    st.markdown("---")
    st.subheader(f"🛰️ Satellite Map & Routes — {loc['name']}")

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
                        <div style="font-size:0.8rem; color:#94a3b8;">⛽ ~{r['fuel_l']} L | SST {z['sst']}°C</div>
                    </div>
                """, unsafe_allow_html=True)
                st.link_button(f"📍 Open {z['type']} in Google Maps", r["gmaps_url"], use_container_width=True)

        active_zone_type = st.radio("Select Active Route:",
            ["🟢 Primary", "🔵 Secondary", "🟠 Alternate"],
            index=st.session_state.selected_zone_index, horizontal=True)
        st.session_state.selected_zone_index = 0 if "Primary" in active_zone_type else 1 if "Secondary" in active_zone_type else 2
        active_route = all_routes[st.session_state.selected_zone_index]

    m = folium.Map(location=[origin_lat, origin_lon], zoom_start=10, tiles=None)
    folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri", name="Satellite").add_to(m)
    folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", attr="Esri", name="Labels", overlay=True).add_to(m)
    folium.Marker([origin_lat, origin_lon], popup=f"<b>{harbour_name}</b>", tooltip=harbour_name, icon=folium.Icon(color="red", icon="info-sign")).add_to(m)

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

# Floating SOS button (always visible)
st.markdown("""
<a href="?sos=1" class="sos-float-btn" title="SOS Emergency">
    🆘<br>SOS
</a>
<script>
// Intercept floating SOS click to set session via query param (Streamlit will pick it up)
</script>
""", unsafe_allow_html=True)

# Handle floating SOS query param
if "sos" in st.query_params:
    try:
        del st.query_params["sos"]
    except Exception:
        pass
    st.session_state.show_sos_panel = True
    st.session_state.show_alerts_panel = False
    st.rerun()

# ---------- CHAT DOCK ----------
def submit_text():
    text = st.session_state.get("user_typed_input", "").strip()
    if text:
        st.session_state.pending_prompt = text
        st.session_state.user_typed_input = ""

with st.container(key="chat_dock_container"):
    st.markdown("""
        <div style="display:flex; gap:8px; margin-bottom:8px; overflow-x:auto; padding-bottom:4px;">
            <span style="font-size:0.75rem; color:#38bdf8; font-weight:600; align-self:center;">Quick:</span>
            <button onclick="window.submitMarinePrompt && window.submitMarinePrompt('Is it safe to fish in Goa?', false)" 
                style="background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.4); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:3px 12px; cursor:pointer;">
                🌊 Goa Safety
            </button>
            <button onclick="window.submitMarinePrompt && window.submitMarinePrompt('Show active alerts', false)" 
                style="background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.4); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:3px 12px; cursor:pointer;">
                🚨 Active Alerts
            </button>
            <button onclick="window.submitMarinePrompt && window.submitMarinePrompt('Best PFZ near Kochi', false)" 
                style="background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.4); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:3px 12px; cursor:pointer;">
                🎯 Kochi PFZ
            </button>
            <button onclick="window.submitMarinePrompt && window.submitMarinePrompt('Hi', false)" 
                style="background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.4); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:3px 12px; cursor:pointer;">
                👋 Say Hi
            </button>
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
            placeholder="Type question or click Speak (e.g. Is it safe to fish in Goa?, Show alerts)...",
            key="user_typed_input",
            on_change=submit_text,
            label_visibility="collapsed"
        )
    with mic_col:
        speech_lang = "en-IN" if st.session_state.language == "English" else "hi-IN"
        st.markdown(f"""
            <button onclick="
                var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SR) {{ alert('Use Chrome/Edge for live speech'); return; }}
                var b = this; b.style.background='#dc2626'; b.innerHTML='🔴 Listening...';
                var r = new SR(); r.lang='{speech_lang}'; r.interimResults=true;
                r.onresult = function(e) {{
                    if (e.results[0].isFinal) {{
                        b.style.background='#16a34a'; b.innerHTML='✅ Done';
                        window.submitMarinePrompt(e.results[0][0].transcript, true);
                    }}
                }};
                r.onerror = r.onend = function() {{ setTimeout(()=>{{b.style.background='#0284c7'; b.innerHTML='🎙️ Live Speak';}}, 2000); }};
                r.start();
            " style="width:100%; height:42px; background:#0284c7; color:white; border:none; border-radius:12px; font-weight:700; cursor:pointer;">
                🎙️ Live Speak
            </button>
        """, unsafe_allow_html=True)
    with send_col:
        st.button("Send ➤", on_click=submit_text, use_container_width=True, type="primary")

    with st.expander("🎙️ High-Accuracy Voice (Whisper)", expanded=False):
        audio_file = st.audio_input("Record", label_visibility="collapsed", key="dock_mic_input")

# Handle voice query params
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
        st.toast(f"🗣️ Heard: {voice_text}", icon="🎙️")

if audio_file is not None:
    try: audio_bytes = audio_file.getvalue()
    except: audio_bytes = audio_file.read()
    if audio_bytes and len(audio_bytes) > 200:
        audio_hash = hashlib.md5(audio_bytes).hexdigest()
        if st.session_state.last_audio_hash != audio_hash:
            st.session_state.last_audio_hash = audio_hash
            with st.spinner("🎧 Transcribing..."):
                transcribed = transcribe_voice_query(audio_bytes, st.session_state.language)
                if transcribed:
                    st.session_state.pending_prompt = transcribed
                    st.session_state.voice_mode_triggered = True
                    st.toast(f"🗣️ {transcribed}", icon="🎙️")
                else:
                    st.toast("Could not detect speech clearly.", icon="⚠️")

# ====================== MAIN ORCHESTRATION ======================
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
        agent_log = [f"NLP ({nlp_plan['intent']})"]

        if nlp_plan["intent"] in ["GREETING", "BOT_IDENTITY", "GRATITUDE", "NORMAL_CHAT"]:
            st.session_state.map_location = None
            st.session_state.pfz_data = None

        if nlp_plan["intent"] == "SOS_EMERGENCY":
            agent_log.append("SOS Emergency Agent")
            st.session_state.show_sos_panel = True
            st.session_state.show_alerts_panel = False
            render_sos_panel(st.session_state.language)

        if nlp_plan["intent"] == "SHOW_ALERTS":
            agent_log.append("Real-Time Alert Agent (Coastal First)")
            st.session_state.show_alerts_panel = True
            render_active_alerts_panel(st.session_state.language)

        if nlp_plan["needs_weather"] and nlp_plan.get("location"):
            loc = nlp_plan["location"]
            location_name = loc["name"]
            if loc.get("state"):
                location_name = f"{loc['name']}, {loc['state']}"

            weather_data = weather_agent(loc["lat"], loc["lon"])
            agent_log.append("Weather Agent")
            render_weather_card(weather_data, location_name)

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
                agent_log.append("PFZ + Navigation")
                render_pfz_section(pfz_data)
            else:
                st.session_state.map_location = None
                st.session_state.pfz_data = None

        agent_log.append("Response Agent")
        final_answer = response_agent(active_prompt, nlp_plan, weather_data, pfz_data, alert_data, st.session_state.language)
        st.markdown(final_answer)

        should_speak = st.session_state.get("voice_mode_triggered", False) or st.session_state.get("auto_speak", False)
        render_tts_button(final_answer, st.session_state.language, auto_play=should_speak, msg_id="latest")
        st.session_state.voice_mode_triggered = False
        st.caption(f"🧠 **Agents:** {' → '.join(agent_log)}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": final_answer,
        "weather_data": weather_data,
        "pfz_data": pfz_data,
        "alert_data": alert_data,
        "location_name": location_name,
        "agent_log": agent_log
    })
    st.rerun()
