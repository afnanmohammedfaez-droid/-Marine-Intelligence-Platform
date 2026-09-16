import streamlit as st
from groq import Groq
import requests
from datetime import datetime
from zoneinfo import Zoneinfo
import folium
from streamlit_folium import st_folium
from urllib.parse import quote
import random
import math
import re
import io
import hashlib
import json
import os

# ====================== CONFIG ======================
try:
    GROQ_API_KEY ="gsk_OEkrKvWavvYxVd70nOHZWGdyb3 FY2ORUZisXFCK85HFspCqEtrke"
except (FileNotFoundError, KeyError):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is not configured. Add it to Streamlit secrets or the environment.")
    st.stop()

client = Groq(api_key="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")

WHATSAPP_NUMBER = "919876543210"
PHONE_NUMBER = "+919876543210"

# Coastal locations with primary departure fishing harbour coordinates
LOCATIONS = {
    "kochi": {
        "lat": 9.9312, "lon": 76.2673, "name": "Kochi",
        "harbour_name": "Cochin Fisheries Harbour",
        "harbour_lat": 9.9402, "harbour_lon": 76.2598,
        "coast": "west"
    },
    "cochin": {
        "lat": 9.9312, "lon": 76.2673, "name": "Kochi",
        "harbour_name": "Cochin Fisheries Harbour",
        "harbour_lat": 9.9402, "harbour_lon": 76.2598,
        "coast": "west"
    },
    "mumbai": {
        "lat": 19.0760, "lon": 72.8777, "name": "Mumbai",
        "harbour_name": "Sassoon Docks Harbour",
        "harbour_lat": 18.9167, "harbour_lon": 72.8258,
        "coast": "west"
    },
    "chennai": {
        "lat": 13.0827, "lon": 80.2707, "name": "Chennai",
        "harbour_name": "Kasimedu Fishing Harbour",
        "harbour_lat": 13.1250, "harbour_lon": 80.2985,
        "coast": "east"
    },
    "goa": {
        "lat": 15.2993, "lon": 74.1240, "name": "Goa",
        "harbour_name": "Mormugao / Betul Fishing Harbour",
        "harbour_lat": 15.4124, "harbour_lon": 73.8052,
        "coast": "west"
    },
    "visakhapatnam": {
        "lat": 17.6868, "lon": 83.2185, "name": "Visakhapatnam",
        "harbour_name": "Vizag Fishing Harbour",
        "harbour_lat": 17.6980, "harbour_lon": 83.2982,
        "coast": "east"
    },
    "mangalore": {
        "lat": 12.9141, "lon": 74.8560, "name": "Mangalore",
        "harbour_name": "Old Mangalore Bunder Port",
        "harbour_lat": 12.8584, "harbour_lon": 74.8351,
        "coast": "west"
    },
    "tuticorin": {
        "lat": 8.7642, "lon": 78.1348, "name": "Tuticorin",
        "harbour_name": "Thoothukudi Fishing Harbour",
        "harbour_lat": 8.8052, "harbour_lon": 78.1630,
        "coast": "east"
    },
    "pondicherry": {
        "lat": 11.9416, "lon": 79.8083, "name": "Pondicherry",
        "harbour_name": "Thengaithittu Fishing Harbour",
        "harbour_lat": 11.9168, "harbour_lon": 79.8251,
        "coast": "east"
    },
    "ratnagiri": {
        "lat": 16.9902, "lon": 73.3120, "name": "Ratnagiri",
        "harbour_name": "Mirkarwada Fishing Harbour",
        "harbour_lat": 16.9935, "harbour_lon": 73.2840,
        "coast": "west"
    },
}

MONITORED_LOCATIONS = ["Kochi", "Mumbai", "Chennai", "Mangalore", "Visakhapatnam"]

ROUTE_COLORS = {
    0: {"hex": "#00E5FF", "label": "Primary Route (Neon Cyan)"},
    1: {"hex": "#3B82F6", "label": "Secondary Route (Electric Blue)"},
    2: {"hex": "#F59E0B", "label": "Alternate Route (Amber Gold)"}
}

# Pre-compiled regex patterns for accurate intent recognition
RE_GREETING = re.compile(r'\b(hi|hello|hey|heyy|greetings|namaste|namaskar|vanakkam|kem\s*cho|good\s*(morning|afternoon|evening|day)|kaise\s*ho|kya\s*haal|kese\s*ho|hi\s*there|hello\s*there)\b', re.IGNORECASE)
RE_IDENTITY = re.compile(r'\b(who are you|what is your name|kya ho tum|tum kaun ho|what can you do|your features|help me|what do you do|introduce yourself|tell me about yourself|how can you help)\b', re.IGNORECASE)
RE_GRATITUDE = re.compile(r'\b(thank\s*you|thanks|dhanyawad|shukriya|bye|goodbye|alvida|see you)\b', re.IGNORECASE)
RE_MARINE_CORE = re.compile(r'\b(sea|weather|wind|safe\w*|fish\w*|wave\w*|tide\w*|ocean|cyclon\w*|storm\w*|rain|boat|harbour|harbor|port|coast|pfz|navigation|direction\w*|route\w*|distance|samundar|mausam|hawa|machli)\b', re.IGNORECASE)
RE_ALERT = re.compile(r'\b(alert|alerts|warning|warnings|danger|dangerous|risk|risky|emergency|caution|advisory|advisories|chetaavani|chetavani|khatra|khatre)\b', re.IGNORECASE)

# ====================== ROBUST VOICE TRANSCRIPTION ======================
def get_audio_filename_and_mime(audio_bytes, original_name=None, mime_type=None):
    """Accurately detects browser audio container format from binary magic bytes."""
    if not audio_bytes or len(audio_bytes) < 4:
        return "voice_input.wav", "audio/wav"

    header = audio_bytes[:12]
    # Check EBML header for WebM / Matroska (\x1a\x45\xdf\xa3)
    if header.startswith(b"\x1aE\xdf\xa3") or b"webm" in audio_bytes[:64].lower():
        return "voice_input.webm", "audio/webm"
    # Check WAV (RIFF....WAVE)
    if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WAVE":
        return "voice_input.wav", "audio/wav"
    # Check OGG
    if header.startswith(b"OggS"):
        return "voice_input.ogg", "audio/ogg"
    # Check MP3
    if header.startswith(b"ID3") or header[:2] in [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"]:
        return "voice_input.mp3", "audio/mpeg"
    # Check MP4 / M4A
    if len(header) >= 8 and header[4:8] == b"ftyp":
        return "voice_input.mp4", "audio/mp4"

    # Check original name extension if provided
    if original_name and "." in original_name:
        ext = original_name.rsplit(".", 1)[-1].lower()
        if ext in ["webm", "wav", "mp3", "ogg", "mp4", "m4a"]:
            return f"voice_input.{ext}", mime_type or f"audio/{ext}"

    # Default fallback for Chrome / Edge MediaRecorder
    return "voice_input.webm", "audio/webm"

def transcribe_voice_query(audio_bytes, language="English"):
    """Accurately transcribes audio into text using Groq Whisper with proper container detection."""
    if not audio_bytes or len(audio_bytes) < 100:
        return None

    filename, mime_type = get_audio_filename_and_mime(audio_bytes)
    lang_code = "en" if language == "English" else "hi"

    # Try whisper-large-v3-turbo first, then whisper-large-v3
    for model_name in ["whisper-large-v3-turbo", "whisper-large-v3"]:
        try:
            audio_file_tuple = (filename, audio_bytes, mime_type)
            transcription = client.audio.transcriptions.create(
                file=audio_file_tuple,
                model=model_name,
                language=lang_code,
                temperature=0.0
            )
            text = transcription.text.strip()
            if text:
                return text
        except Exception:
            try:
                # Retry without language constraint (Whisper auto-detects language)
                audio_file_tuple = (filename, audio_bytes, mime_type)
                transcription = client.audio.transcriptions.create(
                    file=audio_file_tuple,
                    model=model_name,
                    temperature=0.0
                )
                text = transcription.text.strip()
                if text:
                    return text
            except Exception:
                continue

    return None

@st.cache_data(ttl=180, show_spinner=False)
def weather_agent(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weather_code",
            "timezone": "Asia/Kolkata"
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            return {"status": "error", "message": f"API Error: {response.status_code}"}

        data = response.json()
        current = data.get("current", {})
        if not current:
            return {"status": "error", "message": "No weather data received"}

        wind_speed = current.get("wind_speed_10m", 0)

        if wind_speed < 15:
            safety_status = "Safe"
            safety_color = "green"
            safety_message = "Sea conditions appear favourable for fishing."
            prediction = "Favourable conditions expected for fishing."
        elif wind_speed < 25:
            safety_status = "Moderately Safe"
            safety_color = "orange"
            safety_message = "Exercise caution. Wind is moderate."
            prediction = "Moderate winds. Keep safety gear ready."
        else:
            safety_status = "Not Safe"
            safety_color = "red"
            safety_message = "High wind speed. Not recommended to go to sea."
            prediction = "Rough sea conditions expected. Avoid venturing."

        return {
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": round(wind_speed, 1),
            "wind_direction": current.get("wind_direction_10m"),
            "safety_status": safety_status,
            "safety_color": safety_color,
            "safety_message": safety_message,
            "prediction": prediction,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@st.cache_data(ttl=300, show_spinner=False)
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
                "prediction": weather.get("prediction", "No prediction"),
                "lat": loc["lat"],
                "lon": loc["lon"]
            })
    return results

# ====================== ALERT AGENT ======================
def alert_agent(weather_info, location_name, language="English"):
    """
    Generates structured marine safety alerts based on weather conditions.
    Levels: CRITICAL | WARNING | ADVISORY | CLEAR
    """
    if not weather_info or weather_info.get("status") != "success":
        return {
            "status": "error",
            "level": "UNKNOWN",
            "title": "Alert Unavailable",
            "message": "Could not retrieve weather data for alert generation.",
            "color": "#64748b",
            "icon": "❓",
            "action": "Please try again later.",
            "whatsapp_text": ""
        }

    wind = weather_info.get("wind_speed", 0)
    safety = weather_info.get("safety_status", "Safe")
    temp = weather_info.get("temperature", "--")
    prediction = weather_info.get("prediction", "")

    # Determine alert level
    if wind >= 30 or safety == "Not Safe":
        level = "CRITICAL"
        color = "#DC2626"
        icon = "🚨"
        if language == "English":
            title = f"CRITICAL ALERT — {location_name}"
            message = (
                f"High wind speed of **{wind} km/h** detected. "
                f"Sea conditions are dangerous. **Do NOT venture out to sea.** "
                f"Stay in harbour until conditions improve."
            )
            action = "Return to port immediately if already at sea. Contact local Coast Guard if needed."
        else:
            title = f"गंभीर चेतावनी — {location_name}"
            message = (
                f"**{wind} km/h** की तेज़ हवा दर्ज की गई है। "
                f"समुद्र की स्थिति खतरनाक है। **समुद्र में बिल्कुल न जाएं।** "
                f"हालात सुधरने तक बंदरगाह में रहें।"
            )
            action = "यदि पहले से समुद्र में हैं तो तुरंत बंदरगाह लौटें। आवश्यकता पड़ने पर कोस्ट गार्ड से संपर्क करें।"
    elif wind >= 20 or safety == "Moderately Safe":
        level = "WARNING"
        color = "#F59E0B"
        icon = "⚠️"
        if language == "English":
            title = f"WARNING — {location_name}"
            message = (
                f"Moderate to strong winds of **{wind} km/h**. "
                f"Exercise extreme caution. Only experienced crews with proper safety gear should consider going out."
            )
            action = "Carry life jackets, GPS, and VHF radio. Monitor weather closely."
        else:
            title = f"चेतावनी — {location_name}"
            message = (
                f"**{wind} km/h** की मध्यम से तेज़ हवा। "
                f"अत्यधिक सावधानी बरतें। केवल अनुभवी चालक दल ही उचित सुरक्षा उपकरणों के साथ जाएं।"
            )
            action = "लाइफ जैकेट, GPS और VHF रेडियो साथ रखें। मौसम पर लगातार नज़र रखें।"
    elif wind >= 12:
        level = "ADVISORY"
        color = "#3B82F6"
        icon = "ℹ️"
        if language == "English":
            title = f"ADVISORY — {location_name}"
            message = (
                f"Wind speed is **{wind} km/h**. Conditions are generally manageable "
                f"but remain alert for sudden changes."
            )
            action = "Check latest forecast before departure. Keep safety equipment ready."
        else:
            title = f"सलाह — {location_name}"
            message = (
                f"हवा की गति **{wind} km/h** है। स्थितियाँ सामान्य रूप से प्रबंधनीय हैं "
                f"लेकिन अचानक बदलाव के लिए सतर्क रहें।"
            )
            action = "प्रस्थान से पहले नवीनतम पूर्वानुमान जांचें। सुरक्षा उपकरण तैयार रखें।"
    else:
        level = "CLEAR"
        color = "#10B981"
        icon = "✅"
        if language == "English":
            title = f"ALL CLEAR — {location_name}"
            message = (
                f"Favourable conditions. Wind speed **{wind} km/h**. "
                f"Sea appears safe for fishing operations."
            )
            action = "Have a productive and safe trip. Monitor conditions periodically."
        else:
            title = f"सभी ठीक — {location_name}"
            message = (
                f"अनुकूल स्थितियाँ। हवा की गति **{wind} km/h**। "
                f"मछली पकड़ने के लिए समुद्र सुरक्षित प्रतीत होता है।"
            )
            action = "सुरक्षित और सफल यात्रा हो। समय-समय पर स्थितियों की निगरानी करते रहें।"

    # WhatsApp ready text (plain)
    if language == "English":
        whatsapp_text = (
            f"🌊 MARINE ALERT — {location_name}\n"
            f"Level: {level}\n"
            f"Wind: {wind} km/h | Temp: {temp}°C\n"
            f"Status: {safety}\n"
            f"{message.replace('**', '')}\n"
            f"Action: {action}\n"
            f"Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
        )
    else:
        whatsapp_text = (
            f"🌊 समुद्री अलर्ट — {location_name}\n"
            f"स्तर: {level}\n"
            f"हवा: {wind} km/h | तापमान: {temp}°C\n"
            f"स्थिति: {safety}\n"
            f"{message.replace('**', '')}\n"
            f"कार्य: {action}\n"
            f"समय: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
        )

    return {
        "status": "success",
        "level": level,
        "title": title,
        "message": message,
        "color": color,
        "icon": icon,
        "action": action,
        "wind_speed": wind,
        "temperature": temp,
        "safety_status": safety,
        "prediction": prediction,
        "location": location_name,
        "whatsapp_text": whatsapp_text,
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }


def generate_active_alerts(language="English"):
    """Scans all monitored locations and returns list of active (non-CLEAR) alerts."""
    active = []
    for name in MONITORED_LOCATIONS:
        loc = next((val for val in LOCATIONS.values() if val["name"] == name), None)
        if not loc:
            continue
        weather = weather_agent(loc["lat"], loc["lon"])
        if weather.get("status") == "success":
            alert = alert_agent(weather, name, language)
            if alert["level"] in ["CRITICAL", "WARNING", "ADVISORY"]:
                active.append(alert)
    # Sort: CRITICAL first, then WARNING, then ADVISORY
    priority = {"CRITICAL": 0, "WARNING": 1, "ADVISORY": 2}
    active.sort(key=lambda x: priority.get(x["level"], 99))
    return active


def render_alert_banner(alert_data):
    """Renders a prominent visual alert card."""
    if not alert_data or alert_data.get("status") != "success":
        return

    level = alert_data["level"]
    color = alert_data["color"]
    icon = alert_data["icon"]

    # Different intensity for different levels
    if level == "CRITICAL":
        border = f"3px solid {color}"
        bg = "linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%)"
        pulse = "animation: pulse 1.5s infinite;"
    elif level == "WARNING":
        border = f"2px solid {color}"
        bg = "linear-gradient(135deg, #78350f 0%, #451a03 100%)"
        pulse = ""
    elif level == "ADVISORY":
        border = f"2px solid {color}"
        bg = "linear-gradient(135deg, #1e3a8a 0%, #1e293b 100%)"
        pulse = ""
    else:
        border = f"2px solid {color}"
        bg = "linear-gradient(135deg, #064e3b 0%, #022c22 100%)"
        pulse = ""

    html = f"""
    <style>
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7); }}
        70% {{ box-shadow: 0 0 0 12px rgba(220, 38, 38, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }}
    }}
    </style>
    <div style="background: {bg}; border: {border}; border-radius: 16px; padding: 18px 20px;
                color: white; margin: 12px 0 18px; {pulse}">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <div style="font-size:1.15rem; font-weight:700;">
                {icon} {alert_data['title']}
            </div>
            <div style="background:{color}; color:#000; font-weight:800; font-size:0.75rem;
                        padding:3px 10px; border-radius:20px;">
                {level}
            </div>
        </div>
        <div style="font-size:0.95rem; line-height:1.45; margin-bottom:10px;">
            {alert_data['message']}
        </div>
        <div style="font-size:0.85rem; opacity:0.9; margin-bottom:6px;">
            <b>Recommended Action:</b> {alert_data['action']}
        </div>
        <div style="font-size:0.75rem; opacity:0.7;">
            💨 Wind: {alert_data['wind_speed']} km/h &nbsp;|&nbsp;
            🌡️ {alert_data['temperature']}°C &nbsp;|&nbsp;
            🕒 {alert_data['timestamp']}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_active_alerts_panel(language="English"):
    """Shows a summary panel of all current active alerts."""
    active = generate_active_alerts(language)

    if not active:
        st.success("✅ **No active marine alerts** across monitored coastal locations. Conditions are currently favourable.")
        return

    st.markdown(f"### 🚨 Active Marine Alerts ({len(active)})")
    for alert in active:
        render_alert_banner(alert)

        # WhatsApp share button for each alert
        wa_text = quote(alert["whatsapp_text"])
        st.link_button(
            f"📤 Share {alert['location']} Alert on WhatsApp",
            f"https://wa.me/?text={wa_text}",
            use_container_width=False
        )
        st.markdown("<br>", unsafe_allow_html=True)


# ====================== NAVIGATION CALCULATIONS ======================
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    return round((math.degrees(math.atan2(x, y)) + 360) % 360, 1)

def bearing_to_compass(bearing):
    points = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
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
    wp2 = [
        round(origin_lat + (dest_lat - origin_lat) * 0.25 + (0.01 if dest_lat > origin_lat else -0.01), 4),
        round(origin_lon + (dest_lon - origin_lon) * 0.25, 4)
    ]
    wp3 = [
        round(origin_lat + (dest_lat - origin_lat) * 0.65, 4),
        round(origin_lon + (dest_lon - origin_lon) * 0.65, 4)
    ]
    wp4 = [dest_lat, dest_lon]

    steps = [
        {
            "step": 1,
            "title": f"Depart {harbour_name}",
            "coords": wp1,
            "instruction": f"Cast off from berth. Steer bearing {bearing}° ({compass_dir}) towards fairway.",
            "distance": f"{round(dist_km * 0.25, 1)} km"
        },
        {
            "step": 2,
            "title": "Clear Harbor Fairway",
            "coords": wp2,
            "instruction": f"Exit breakwater into open waters. Maintain steady speed heading {compass_dir}.",
            "distance": f"{round(dist_km * 0.40, 1)} km"
        },
        {
            "step": 3,
            "title": "Mid-Course Ocean Waypoint",
            "coords": wp3,
            "instruction": "Navigating deep coastal shelf. Monitor echo sounder & wind velocity.",
            "distance": f"{round(dist_km * 0.35, 1)} km"
        },
        {
            "step": 4,
            "title": f"Arrival: {dest_name}",
            "coords": wp4,
            "instruction": "Arrive at high-concentration Potential Fishing Zone. Deploy fishing gear.",
            "distance": "Destination Reached"
        }
    ]

    gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_lat},{origin_lon}&destination={dest_lat},{dest_lon}&travelmode=driving"

    return {
        "distance_km": dist_km,
        "distance_nm": dist_nm,
        "bearing": bearing,
        "compass_dir": compass_dir,
        "eta": f"{hours}h {minutes}m",
        "fuel_l": fuel_est_liters,
        "waypoints": [wp1, wp2, wp3, wp4],
        "steps": steps,
        "gmaps_url": gmaps_url
    }

# ====================== ADVANCED NLP INTENT DETECTOR ======================
def get_natural_greeting(language="English"):
    if language == "English":
        return (
            "👋 **Hello! Welcome to the Marine Intelligence Platform.**\n\n"
            "I am your **Marine AI Assistant**, designed specifically for Indian fishermen and marine navigators to keep you safe at sea and guide you to high-catch zones.\n\n"
            "### 🌊 How can I help you today?\n"
            "- 🛡️ **Safety & Weather**: Ask *'Is it safe to go fishing in Goa?'*\n"
            "- 🚨 **Alerts**: Ask *'Show active alerts'* or *'Is there any warning for Mumbai?'*\n"
            "- 🎯 **Best Fishing Zones**: Ask *'Where is the nearest PFZ near Kochi?'*\n"
            "- 💨 **Live Wind & Sea State**: Ask *'What is the wind speed in Mumbai?'*\n"
            "- 🧭 **Routes & Directions**: Ask *'Show fishing route for Chennai'*\n\n"
            "You can type your question below or click the **🎙️ microphone** to speak!"
        )
    else:
        return (
            "👋 **नमस्ते! मरीन इंटेलिजेंस प्लेटफ़ॉर्म में आपका स्वागत है।**\n\n"
            "मैं आपका **समुद्री एआई सहायक (Marine AI Assistant)** हूँ। मैं भारतीय मछुआरों की सुरक्षा, समुद्र के मौसम और संभावित मत्स्यन क्षेत्रों (PFZ) की सटीक जानकारी प्रदान करता हूँ।\n\n"
            "### 🌊 मैं आपकी क्या मदद कर सकता हूँ?\n"
            "- 🛡️ **समुद्र सुरक्षा**: पूछें *'क्या गोवा में समुद्र में जाना सुरक्षित है?'*\n"
            "- 🚨 **अलर्ट**: पूछें *'सक्रिय अलर्ट दिखाएं'* या *'मुंबई के लिए कोई चेतावनी है?'*\n"
            "- 🎯 **मत्स्यन क्षेत्र (PFZ)**: पूछें *'कोच्चि के पास मछली पकड़ने का क्षेत्र कहाँ है?'*\n"
            "- 💨 **हवा और मौसम**: पूछें *'मुंबई में हवा की गति और मौसम कैसा है?'*\n"
            "- 🧭 **नेविगेशन मार्ग**: पूछें *'चेन्नई के लिए मार्ग और दूरी दिखाएं'*\n\n"
            "आप नीचे अपना प्रश्न लिख सकते हैं या **🎙️ माइक** पर बोल सकते हैं!"
        )

def get_natural_identity(language="English"):
    if language == "English":
        return (
            "🤖 **I am the Marine Intelligence Assistant (Marine AI).**\n\n"
            "I am an agentic AI system developed for Indian coastal communities. Here is what I can do for you:\n\n"
            "1. 💨 **Real-Time Safety Analysis**: Evaluate live wind speed and wave conditions to advise if it is Safe, Moderately Safe, or Risky to venture into the sea.\n"
            "2. 🚨 **Alert Agent**: Continuously monitors coastal locations and issues CRITICAL / WARNING / ADVISORY alerts.\n"
            "3. 🐟 **Potential Fishing Zones (PFZs)**: Map high-catch areas based on ocean temperature (SST) and chlorophyll concentrations.\n"
            "4. 🛰️ **Multi-Route Satellite Navigation**: Draw 3 distinct colored routes (Primary, Secondary, Alternate) on satellite maps.\n"
            "5. 🗺️ **Google Maps Integration**: 1-click directions from port to offshore zones.\n"
            "6. 🎙️ **Voice Assistance**: Speak or listen to advisories in English or Hindi.\n\n"
            "Which coastal port are you departing from? (e.g., *Goa, Kochi, Mumbai, Chennai, Visakhapatnam*)"
        )
    else:
        return (
            "🤖 **मैं मरीन इंटेलिजेंस असिस्टेंट (Marine AI) हूँ।**\n\n"
            "मैं भारतीय मछुआरों और नाविकों के लिए विकसित एक विशेष एआई सहायक हूँ। मैं निम्नलिखित सहायता प्रदान करता हूँ:\n\n"
            "1. 💨 **समुद्र मौसम और सुरक्षा**: लाइव हवा की गति के आधार पर समुद्र में जाने की सुरक्षा सलाह।\n"
            "2. 🚨 **अलर्ट एजेंट**: तटीय स्थानों की निरंतर निगरानी और CRITICAL / WARNING / ADVISORY अलर्ट।\n"
            "3. 🐟 **मत्स्यन क्षेत्र (PFZ)**: उपग्रह डेटा द्वारा मछली मिलने के सबसे अच्छे स्थान।\n"
            "4. 🛰️ **सैटेलाइट नेविगेशन**: बंदरगाह से समुद्र तक 3 अलग-अलग नेविगेशन मार्ग।\n"
            "5. 🗺️ **गूगल मैप्स नेविगेशन**: लाइव दिशा-निर्देश और दूरी।\n\n"
            "आप किस बंदरगाह या शहर की जानकारी चाहते हैं? (जैसे: *गोवा, कोच्चि, मुंबई, चेन्नई, विशाखापट्टनम*)"
        )

def advanced_nlp_agent(user_query):
    query = user_query.lower().strip()

    detected_location = None
    for key, value in LOCATIONS.items():
        if re.search(r'\b' + re.escape(key) + r'\b', query):
            detected_location = value
            break

    has_greeting = bool(RE_GREETING.search(query))
    has_identity = bool(RE_IDENTITY.search(query))
    has_gratitude = bool(RE_GRATITUDE.search(query))
    has_marine = bool(RE_MARINE_CORE.search(query))
    has_alert = bool(RE_ALERT.search(query))

    # Priority: Alert intent
    if has_alert and not detected_location:
        intent = "SHOW_ALERTS"
    elif has_alert and detected_location:
        intent = "LOCATION_ALERT"
    elif detected_location and (has_marine or not has_greeting):
        intent = "MARINE_LOCATION"
    elif detected_location and has_greeting and not has_marine:
        intent = "MARINE_LOCATION"
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
        "has_greeting": has_greeting,
        "needs_weather": bool(intent in ["MARINE_LOCATION", "LOCATION_ALERT"]),
        "needs_pfz": bool(intent == "MARINE_LOCATION"),
        "needs_alert": bool(intent in ["SHOW_ALERTS", "LOCATION_ALERT", "MARINE_LOCATION"]),
        "original_query": user_query
    }

def pfz_agent(location_info, weather_info=None):
    location_name = location_info["name"]
    base_lat = location_info.get("harbour_lat", location_info["lat"])
    base_lon = location_info.get("harbour_lon", location_info["lon"])
    coast = location_info.get("coast", "west")

    sst = round(random.uniform(27.8, 30.2), 1)
    chlorophyll = round(random.uniform(0.7, 1.8), 2)
    wind_speed = weather_info.get("wind_speed", 12) if weather_info else 14

    sst_score = 100 if 28 <= sst <= 29.5 else 70
    chl_score = min(100, int(chlorophyll * 55))
    wind_score = 100 if wind_speed < 15 else 60 if wind_speed < 25 else 20
    total_score = int((sst_score * 0.35) + (chl_score * 0.40) + (wind_score * 0.25))

    lon_dir = -1 if coast == "west" else 1

    offsets = [
        (0.04, lon_dir * 0.17),
        (0.12, lon_dir * 0.25),
        (-0.07, lon_dir * 0.21)
    ]

    base_zones = []
    types = ["Primary", "Secondary", "Alternate"]
    for i, (lat_off, lon_off) in enumerate(offsets):
        zone_lat = round(base_lat + lat_off, 4)
        zone_lon = round(base_lon + lon_off, 4)
        dist_km = haversine_distance(base_lat, base_lon, zone_lat, zone_lon)
        dist_nm = round(dist_km / 1.852, 1)
        zone_score = max(40, total_score - (i * 8))

        base_zones.append({
            "name": f"{types[i]} PFZ - {location_name}",
            "type": types[i],
            "distance_km": dist_km,
            "distance_nm": dist_nm,
            "distance": f"{dist_km} km ({dist_nm} NM)",
            "score": zone_score,
            "lat": zone_lat,
            "lon": zone_lon,
            "sst": sst,
            "chlorophyll": chlorophyll,
            "color_hex": ROUTE_COLORS[i]["hex"]
        })

    best_zone = base_zones[0]
    recommendation = "Highly Recommended" if best_zone["score"] >= 75 else "Moderately Recommended"

    return {
        "status": "success",
        "best_zone": best_zone,
        "all_zones": base_zones,
        "overall_score": total_score,
        "recommendation": recommendation,
        "sst": sst,
        "chlorophyll": chlorophyll,
        "harbour_name": location_info.get("harbour_name", f"{location_name} Port"),
        "harbour_lat": base_lat,
        "harbour_lon": base_lon,
        "note": "Simulated PFZ based on SST, Chlorophyll & Wind. For official advisories refer to INCOIS."
    }

def call_groq_llm(messages, max_tokens=350, temperature=0.3):
    """Executes chat completions with active fast models and strips reasoning tokens."""
    models = ["qwen/qwen3.8-27b", "qwen/qwen3.6-27b"]
    for model_name in models:
        try:
            completion = client.chat.completions.create(
                messages=messages,
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature
            )
            raw = completion.choices[0].message.content or ""
            clean = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            if clean:
                return clean
        except Exception:
            continue
    return None

def response_agent(user_query, nlp_plan, weather_info=None, pfz_info=None, alert_info=None, language="English"):
    intent = nlp_plan.get("intent", "NORMAL_CHAT")
    lang_inst = "Reply in clear English." if language == "English" else "Reply in clear Hindi."

    # 1. Deterministic Instant Responses (Zero latency, always works)
    if intent == "GREETING":
        return get_natural_greeting(language)
    elif intent == "BOT_IDENTITY":
        return get_natural_identity(language)
    elif intent == "GRATITUDE":
        return (
            "🙏 **You're very welcome! Stay safe out on the waters, and wishing you a great catch! 🌊⚓**"
            if language == "English"
            else "🙏 **आपका बहुत-बहुत धन्यवाद! समुद्र में सुरक्षित रहें और आपकी यात्रा सफल हो! 🌊⚓**"
        )
    elif intent == "LOCATION_AMBIGUOUS":
        return (
            "🌊 **I'd be glad to check sea conditions and fishing zones for you!**\n\n"
            "Which coastal city or port are you departing from?\n"
            "*(For example: **Goa, Kochi, Mumbai, Chennai, Visakhapatnam, Mangalore, Tuticorin, or Ratnagiri**)*"
            if language == "English"
            else "🌊 **मैं आपके लिए समुद्र की स्थिति और मछली पकड़ने के क्षेत्र की जांच करने के लिए तैयार हूँ!**\n\n"
            "कृपया बताएं कि आप किस तटीय शहर या बंदरगाह से प्रस्थान कर रहे हैं?\n"
            "*(उदाहरण: **गोवा, कोच्चि, मुंबई, चेन्नई, विशाखापट्टनम, मैंगलोर**)*"
        )
    elif intent == "SHOW_ALERTS":
        # Handled specially in the main flow with visual banners
        if language == "English":
            return (
                "🚨 **Checking active marine alerts across all monitored coastal locations...**\n\n"
                "Please see the detailed alert banners below. You can also share any alert directly on WhatsApp."
            )
        else:
            return (
                "🚨 **सभी निगरानी वाले तटीय स्थानों पर सक्रिय समुद्री अलर्ट जाँच रहा हूँ...**\n\n"
                "कृपया नीचे दिए गए विस्तृत अलर्ट बैनर देखें। आप किसी भी अलर्ट को सीधे व्हाट्सएप पर साझा कर सकते हैं।"
            )

    # 2. Marine Location Advisory (Guarded against NoneType errors)
    loc = nlp_plan.get("location")
    if loc and isinstance(loc, dict) and weather_info:
        loc_name = loc.get("name", "Coastal Port")
        greeting_prefix = "Start with a brief polite greeting." if nlp_plan.get("has_greeting") else ""

        alert_context = ""
        if alert_info and alert_info.get("status") == "success":
            alert_context = f"""
Alert Level: {alert_info.get('level')}
Alert Message: {alert_info.get('message')}
Recommended Action: {alert_info.get('action')}
"""

        pfz_context = ""
        if pfz_info and pfz_info.get("status") == "success":
            pfz_context = f"""
Best PFZ: {pfz_info['best_zone']['name']} (Dist: {pfz_info['best_zone']['distance']}, Score: {pfz_info['best_zone']['score']}/100)
All 3 routes (Primary, Secondary, Alternate) are drawn on the satellite map below.
"""

        context = f"""
Location: {loc_name}
Harbour: {pfz_info.get('harbour_name', 'Port') if pfz_info else loc_name}
Weather: Temp {weather_info.get('temperature')}°C | Wind {weather_info.get('wind_speed')} km/h | Status: {weather_info.get('safety_status')}
Advice: {weather_info.get('safety_message')} | Prediction: {weather_info.get('prediction')}
{alert_context}
{pfz_context}
"""
        system_prompt = f"""You are Marine AI Assistant for Indian fishermen.
{lang_inst}
{greeting_prefix}
Instructions:
- State Safety Status and Wind Speed clearly first.
- If there is a CRITICAL or WARNING alert, emphasize it strongly at the beginning.
- Give sea condition advice and highlight the best Potential Fishing Zone if available.
- Mention that interactive satellite navigation routes and Google Maps directions are ready below (if applicable).
- Keep it concise, structured, and helpful.
Data:
{context}"""

        response = call_groq_llm(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            max_tokens=350,
            temperature=0.3
        )
        if response:
            return response

        # Safe deterministic fallback if API is unreachable
        status = weather_info.get("safety_status", "Safe")
        wind = weather_info.get("wind_speed", 12)
        best_z = pfz_info['best_zone']['name'] if pfz_info else "N/A"
        dist = pfz_info['best_zone']['distance'] if pfz_info else ""
        return (
            f"📍 **Sea Advisory for {loc_name}:**\n\n"
            f"- **Safety Status**: {status}\n"
            f"- **Wind Speed**: {wind} km/h\n"
            f"- **Recommended Zone**: {best_z} ({dist})\n"
            f"- **Advisory**: {weather_info.get('safety_message')}\n\n"
            f"🗺️ Please check the satellite map and Google Maps routes below."
        )

    # 3. Conversational / Normal Non-Marine Chat
    system_prompt = f"""You are Marine AI Assistant, a helpful assistant for Indian fishermen and marine navigators.
{lang_inst}
Instructions:
- Answer the user's question politely, warmly and conversationally.
- Let them know you are their dedicated marine guide and can check real-time sea safety, weather, alerts, or fishing zones for coastal ports like Goa, Kochi, Mumbai, Chennai, Visakhapatnam, etc."""

    response = call_groq_llm(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        max_tokens=250,
        temperature=0.4
    )
    if response:
        return response

    return (
        "🌊 **I am your Marine AI Assistant.**\n\n"
        "I can help you check real-time sea safety, live weather forecasts, active alerts, and Potential Fishing Zones (PFZs) with satellite navigation routes.\n\n"
        "Try asking:\n"
        "- *'Is it safe to fish in Goa?'*\n"
        "- *'Show active alerts'*\n"
        "- *'Where is the best fishing zone near Kochi?'*\n"
        "- *'What is the wind in Mumbai?'*"
    )

# ====================== RENDER HELPERS ======================
def clean_text_for_tts(text):
    """Strips markdown formatting, code blocks, URLs, and emojis for natural, human-like speech."""
    if not text:
        return ""
    t = re.sub(r"```[\s\S]*?```", "", text)
    t = re.sub(r"`.*?`", "", t)
    t = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", t)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"[\U00010000-\U0010ffff]", "", t)
    t = re.sub(r"[*_~#|>]", " ", t)
    t = re.sub(r"^\s*[-+•]\s+", " ", t, flags=re.MULTILINE)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def render_tts_button(text_to_speak, language="English", auto_play=False, msg_id=None):
    """Renders an interactive Text-to-Speech audio bar with auto-speak, voice selection, and pulse indicator."""
    speech_text = clean_text_for_tts(text_to_speak)
    if not speech_text:
        return

    text_json = json.dumps(speech_text, ensure_ascii=False)
    lang_code = "en-IN" if language == "English" else "hi-IN"
    uid = f"tts_{abs(hash(speech_text[:40]))}" if not msg_id else f"tts_{msg_id}"
    auto_trigger = f"setTimeout(function(){{ playTTS_{uid}(); }}, 300);" if auto_play else ""

    html = f"""
    <div id="container_{uid}" style="margin-top: 8px; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
        <button id="btn_play_{uid}" onclick="playTTS_{uid}();" style="display:inline-flex; align-items:center; gap:6px; background:linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color:white; border:none; border-radius:8px; padding:6px 14px; font-size:0.82rem; font-weight:600; cursor:pointer; box-shadow:0 2px 8px rgba(2,132,199,0.3); transition:all 0.2s ease;">
            <span id="icon_{uid}">🔊</span> <span id="label_{uid}">Listen to Advisory ({language})</span>
        </button>
        <button id="btn_stop_{uid}" onclick="stopTTS_{uid}();" style="display:none; align-items:center; gap:4px; background:#334155; color:#cbd5e1; border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:6px 12px; font-size:0.82rem; cursor:pointer; transition:all 0.2s ease;">
            ⏹️ Stop
        </button>
        <span id="indicator_{uid}" style="display:none; font-size:0.75rem; color:#38bdf8; font-weight:600;">
            🎙️ Speaking...
        </span>
    </div>
    <script>
    (function() {{
        var text = {text_json};
        var lang = '{lang_code}';
        var uid = '{uid}';
        var keepAliveTimer = null;

        window['playTTS_' + uid] = function() {{
            if (!('speechSynthesis' in window)) {{
                alert('Text-to-speech is not supported in this browser.');
                return;
            }}
            window.speechSynthesis.cancel();
            if (keepAliveTimer) clearInterval(keepAliveTimer);

            var u = new SpeechSynthesisUtterance(text);
            u.lang = lang;
            u.rate = 1.0;
            u.pitch = 1.0;

            // Prioritize natural Hindi / Indian English voices if installed
            var voices = window.speechSynthesis.getVoices();
            if (voices && voices.length > 0) {{
                var targetPrefix = lang.startsWith('hi') ? 'hi' : 'en';
                var preferred = voices.find(function(v) {{
                    return v.lang && v.lang.toLowerCase().replace('_', '-').startsWith(lang.toLowerCase());
                }}) || voices.find(function(v) {{
                    return v.lang && v.lang.toLowerCase().startsWith(targetPrefix);
                }});
                if (preferred) u.voice = preferred;
            }}

            var playBtn = document.getElementById('btn_play_' + uid);
            var stopBtn = document.getElementById('btn_stop_' + uid);
            var label = document.getElementById('label_' + uid);
            var icon = document.getElementById('icon_' + uid);
            var indicator = document.getElementById('indicator_' + uid);

            u.onstart = function() {{
                if (playBtn) playBtn.style.background = '#15803d';
                if (label) label.innerText = 'Speaking...';
                if (icon) icon.innerText = '🔊';
                if (stopBtn) stopBtn.style.display = 'inline-flex';
                if (indicator) indicator.style.display = 'inline';

                // Chrome 15s garbage collection keepalive
                keepAliveTimer = setInterval(function() {{
                    if (!window.speechSynthesis.speaking) {{
                        clearInterval(keepAliveTimer);
                    }} else {{
                        window.speechSynthesis.pause();
                        window.speechSynthesis.resume();
                    }}
                }}, 10000);
            }};

            var resetState = function() {{
                if (keepAliveTimer) clearInterval(keepAliveTimer);
                if (playBtn) playBtn.style.background = 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)';
                if (label) label.innerText = 'Listen to Advisory ({language})';
                if (icon) icon.innerText = '🔊';
                if (stopBtn) stopBtn.style.display = 'none';
                if (indicator) indicator.style.display = 'none';
            }};

            u.onend = resetState;
            u.onerror = resetState;

            window._activeSpeechUtterance = u;
            window.speechSynthesis.speak(u);
        }};

        window['stopTTS_' + uid] = function() {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
            }}
            if (keepAliveTimer) clearInterval(keepAliveTimer);
            var playBtn = document.getElementById('btn_play_' + uid);
            var stopBtn = document.getElementById('btn_stop_' + uid);
            var label = document.getElementById('label_' + uid);
            var indicator = document.getElementById('indicator_' + uid);
            if (playBtn) playBtn.style.background = 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)';
            if (label) label.innerText = 'Listen to Advisory ({language})';
            if (stopBtn) stopBtn.style.display = 'none';
            if (indicator) indicator.style.display = 'none';
        }};

        {auto_trigger}
    }})();
    </script>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_monitoring_dashboard(monitor_data):
    st.subheader("📡 Live Coastal Monitoring")
    st.caption("Status cached for fast response | Auto-refreshes every 5 mins")

    if not monitor_data:
        st.warning("Monitoring feed temporarily unavailable.")
        return

    cols = st.columns(len(monitor_data))
    for idx, data in enumerate(monitor_data):
        with cols[idx]:
            color = data["safety_color"]
            st.markdown(
                f"""
                <div style="background:#0f172a; border-radius:12px; padding:12px 10px; color:white; text-align:center; border:1px solid rgba(255,255,255,0.08);">
                    <div style="font-weight:600; font-size:1rem;">{data['name']}</div>
                    <div style="margin:6px 0; padding:3px 8px; background:{color}; border-radius:15px; display:inline-block; font-size:0.75rem; font-weight:700;">
                        {data['safety_status']}
                    </div>
                    <div style="font-size:0.85rem; margin-top:4px;">💨 {data['wind_speed']} km/h</div>
                    <div style="font-size:0.8rem; opacity:0.8;">🌡️ {data['temperature']}°C</div>
                </div>
                """,
                unsafe_allow_html=True
            )

def render_weather_card(weather_data, location_name):
    if not weather_data or weather_data.get("status") != "success":
        return

    safety_color_map = {"green": "#10B981", "orange": "#F59E0B", "red": "#EF4444"}
    accent = safety_color_map.get(weather_data.get("safety_color", "green"), "#3B82F6")
    wind_deg = weather_data.get("wind_direction", 0) or 0
    prediction = weather_data.get("prediction", "")
    prediction_html = f'<div style="text-align:center; font-size:0.88rem; color:#93c5fd; margin-bottom:12px;">🔮 {prediction}</div>' if prediction else ''

    html = f"""
    <div style="background: linear-gradient(160deg, #0f172a 0%, #1e293b 100%);
                border-radius: 20px; padding: 20px; color: white; max-width: 440px; margin: 10px 0 15px;
                border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 15px 30px rgba(0,0,0,0.3);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div style="font-size:1.15rem; font-weight:600;">📍 {location_name}</div>
            <div style="background:{accent}; color:white; padding:4px 12px; border-radius:50px; font-size:0.75rem; font-weight:700;">
                {weather_data.get('safety_status', 'Unknown')}
            </div>
        </div>
        <div style="text-align:center; margin:8px 0;">
            <span style="font-size:3.2rem; font-weight:300;">{weather_data.get('temperature', '--')}</span>
            <span style="font-size:1.4rem; opacity:0.7;">°C</span>
        </div>
        <div style="text-align:center; font-size:0.9rem; opacity:0.9; margin-bottom:10px;">{weather_data.get('safety_message', '')}</div>
        {prediction_html}
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px;">
            <div style="background:rgba(255,255,255,0.06); border-radius:10px; padding:10px 5px; text-align:center;">
                <div>💨</div>
                <div style="font-weight:600;">{weather_data.get('wind_speed', '--')}</div>
                <div style="font-size:0.65rem; opacity:0.7;">WIND KM/H</div>
            </div>
            <div style="background:rgba(255,255,255,0.06); border-radius:10px; padding:10px 5px; text-align:center;">
                <div style="transform:rotate({wind_deg}deg); display:inline-block;">➤</div>
                <div style="font-weight:600;">{wind_deg}°</div>
                <div style="font-size:0.65rem; opacity:0.7;">DIRECTION</div>
            </div>
            <div style="background:rgba(255,255,255,0.06); border-radius:10px; padding:10px 5px; text-align:center;">
                <div>💧</div>
                <div style="font-weight:600;">{weather_data.get('humidity', '--')}%</div>
                <div style="font-size:0.65rem; opacity:0.7;">HUMIDITY</div>
            </div>
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
        st.success(f"🎯 **Best PFZ:** {best['name']} ({best['distance']})")
        st.caption(f"⚓ **Port of Departure:** {pfz_data.get('harbour_name')}")
    with c2:
        st.metric("PFZ Score", f"{best['score']}/100", pfz_data["recommendation"])
    st.caption(f"🌡️ SST: {pfz_data['sst']}°C &nbsp;|&nbsp; 🟢 Chlorophyll: {pfz_data['chlorophyll']} mg/m³")

# ====================== UI SETUP & STATE ======================
st.set_page_config(page_title="Marine Intelligence Platform", page_icon="🌊", layout="wide")

if "language" not in st.session_state:
    st.session_state.language = "English"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "map_location" not in st.session_state:
    st.session_state.map_location = None
if "pfz_data" not in st.session_state:
    st.session_state.pfz_data = None
if "selected_zone_index" not in st.session_state:
    st.session_state.selected_zone_index = 0
if "boat_speed_knots" not in st.session_state:
    st.session_state.boat_speed_knots = 10
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "auto_speak" not in st.session_state:
    st.session_state.auto_speak = True
if "voice_mode_triggered" not in st.session_state:
    st.session_state.voice_mode_triggered = False
if "show_alerts_panel" not in st.session_state:
    st.session_state.show_alerts_panel = False

# Sticky Floating Chat Dock CSS
st.markdown(
    """
    <style>
    .st-key-chat_dock_container {
        position: fixed !important;
        bottom: 15px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: min(920px, 94vw) !important;
        z-index: 999999 !important;
        background: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(56, 189, 248, 0.45) !important;
        border-radius: 20px !important;
        padding: 8px 14px !important;
        box-shadow: 0 -8px 30px rgba(0, 0, 0, 0.65), 0 0 15px rgba(56, 189, 248, 0.2) !important;
    }
    .bottom-scroll-spacer {
        height: 120px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

now = datetime.now()
st.title("🌊 Marine Intelligence Platform")
st.markdown(f"### 📅 {now.strftime('%d %B %Y')} &nbsp;&nbsp;|&nbsp;&nbsp; 🕒 {now.strftime('%I:%M %p')}")
st.write("Instant agentic platform with intelligent marine NLP, satellite maps, multi-route navigation, **Alert Agent** & voice assistance.")
st.divider()

# Live Coastal Monitoring
monitor_data = cached_continuous_monitor()
render_monitoring_dashboard(monitor_data)

# Quick Alerts Button
col_a1, col_a2, col_a3 = st.columns([1, 1, 2])
with col_a1:
    if st.button("🚨 View Active Alerts", use_container_width=True, type="primary"):
        st.session_state.show_alerts_panel = True
with col_a2:
    if st.button("🔄 Refresh Monitoring", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if st.session_state.show_alerts_panel:
    st.markdown("---")
    render_active_alerts_panel(st.session_state.language)
    if st.button("Close Alerts Panel"):
        st.session_state.show_alerts_panel = False
        st.rerun()

st.divider()

# Sidebar
with st.sidebar:
    st.header("🌐 Language")
    language = st.radio(
        "Select Language",
        ["English", "Hindi"],
        index=0 if st.session_state.language == "English" else 1
    )
    st.session_state.language = language

    st.markdown("---")
    st.header("🔊 Voice & Speech")
    st.session_state.auto_speak = st.toggle(
        "Auto-Speak Responses",
        value=st.session_state.auto_speak,
        help="Automatically speak marine advisories aloud as soon as the answer is generated"
    )

    st.markdown("---")
    st.header("🚤 Vessel Cruising Speed")
    speed_option = st.selectbox(
        "Select Trawler / Boat Type",
        [
            "Motorized Boat (8 knots / ~15 km/h)",
            "Mechanized Trawler (10 knots / ~18.5 km/h)",
            "Fiber Speedboat (16 knots / ~30 km/h)"
        ],
        index=1
    )
    st.session_state.boat_speed_knots = 8 if "8 knots" in speed_option else 16 if "16 knots" in speed_option else 10

    st.markdown("---")
    st.header("🆘 24×7 Marine Helpline")
    whatsapp_msg = quote("Hello, I need urgent fishing advisory / sea condition help.")
    st.link_button("💬 Chat on WhatsApp", f"https://wa.me/{WHATSAPP_NUMBER}?text={whatsapp_msg}", use_container_width=True)

    st.markdown(
        f"""
        <a href="tel:{PHONE_NUMBER}">
            <button style="width:100%; padding:10px; background-color:#25D366; color:white;
                           border:none; border-radius:8px; font-size:16px; cursor:pointer;">
                📞 Call Helpline
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.subheader("💡 Try Asking")
    st.markdown("""
    - **Greetings**: *Hi / Hello / Namaste*
    - **Identity**: *Who are you?*
    - **Safety**: *Is it safe to go fishing in Goa?*
    - **Alerts**: *Show active alerts* / *Any warning for Mumbai?*
    - **Zones**: *Where is the nearest PFZ near Kochi?*
    - **Routes**: *Best route and distance for Mumbai*
    """)

# Chat History
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

# ====================== SATELLITE MAP & MULTI-ROUTE SECTION ======================
if st.session_state.map_location:
    loc = st.session_state.map_location
    harbour_name = loc.get("harbour_name", f"{loc['name']} Harbour")
    origin_lat = loc.get("harbour_lat", loc["lat"])
    origin_lon = loc.get("harbour_lon", loc["lon"])

    st.markdown("---")
    st.subheader(f"🛰️ Satellite Map & Multi-Zone Marine Routes — {loc['name']}")

    has_pfz = (
        st.session_state.pfz_data is not None and
        st.session_state.pfz_data.get("status") == "success" and
        len(st.session_state.pfz_data.get("all_zones", [])) > 0
    )

    all_routes = []
    if has_pfz:
        zones = st.session_state.pfz_data["all_zones"]

        for i, zone in enumerate(zones):
            r = generate_marine_route(
                origin_lat, origin_lon,
                zone["lat"], zone["lon"],
                harbour_name, zone["name"],
                st.session_state.boat_speed_knots
            )
            r["zone"] = zone
            r["color"] = ROUTE_COLORS[i]["hex"]
            r["label"] = ROUTE_COLORS[i]["label"]
            all_routes.append(r)

        # 3-Way Route Comparison Cards
        st.markdown("#### 🧭 Marine Routes Comparison & Google Maps Links")
        cols = st.columns(3)

        for i, r in enumerate(all_routes):
            z = r["zone"]
            is_active = (i == st.session_state.selected_zone_index)
            border_color = r["color"] if is_active else "rgba(255,255,255,0.12)"

            with cols[i]:
                st.markdown(
                    f"""
                    <div style="background:#1e293b; border-radius:14px; padding:15px; color:white;
                                border: 2px solid {border_color}; box-shadow: 0 8px 20px rgba(0,0,0,0.25);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="background:{r['color']}; color:#000; font-weight:800; font-size:0.75rem; padding:2px 8px; border-radius:10px;">
                                {r['label']}
                            </span>
                            <span style="font-size:0.85rem; color:#94a3b8;">Score: <b style="color:#fff;">{z['score']}/100</b></span>
                        </div>
                        <div style="font-size:1.05rem; font-weight:700; margin:8px 0 4px; color:#fff;">{z['name']}</div>
                        <div style="font-size:0.85rem; color:#cbd5e1;">📍 <b>{r['distance_km']} km</b> ({r['distance_nm']} NM)</div>
                        <div style="font-size:0.85rem; color:#cbd5e1;">⏱️ Travel Time: <b>{r['eta']}</b></div>
                        <div style="font-size:0.85rem; color:#cbd5e1;">🧭 Heading: <b>{r['bearing']}° ({r['compass_dir']})</b></div>
                        <div style="font-size:0.8rem; color:#94a3b8; margin-top:4px;">⛽ Est. Fuel: ~{r['fuel_l']} Liters</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.link_button(f"📍 Open {z['type']} Route in Google Maps", r["gmaps_url"], use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        active_zone_type = st.radio(
            "🔎 Select Active Route to Highlight & Inspect Waypoints:",
            ["🟢 Primary Route (Neon Cyan)", "🔵 Secondary Route (Electric Blue)", "🟠 Alternate Route (Amber Gold)"],
            index=st.session_state.selected_zone_index,
            horizontal=True
        )
        st.session_state.selected_zone_index = 0 if "Primary" in active_zone_type else 1 if "Secondary" in active_zone_type else 2
        active_route = all_routes[st.session_state.selected_zone_index]

    # ---------- PURE SATELLITE MAP WITH ALL 3 ROUTES ----------
    m = folium.Map(location=[origin_lat, origin_lon], zoom_start=10, tiles=None)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite",
        overlay=False,
        control=False
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Labels",
        overlay=True,
        control=True
    ).add_to(m)

    folium.Marker(
        [origin_lat, origin_lon],
        popup=f"<b>⚓ Departure Port: {harbour_name}</b><br>Coords: {origin_lat}, {origin_lon}",
        tooltip=f"{harbour_name} (Departure Port)",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

    if has_pfz:
        for i, r in enumerate(all_routes):
            z = r["zone"]
            is_active = (i == st.session_state.selected_zone_index)

            folium.PolyLine(
                locations=r["waypoints"],
                color=r["color"],
                weight=6 if is_active else 3.5,
                opacity=1.0 if is_active else 0.7,
                dash_array=None if is_active else "7, 9",
                tooltip=f"{r['label']}: {harbour_name} ➔ {z['name']} ({r['distance_km']} km)"
            ).add_to(m)

            marker_color = "green" if i == 0 else "blue" if i == 1 else "orange"
            folium.Marker(
                [z["lat"], z["lon"]],
                popup=f"<b>{z['name']}</b><br>Score: {z['score']}/100<br>Distance: {r['distance_km']} km<br>ETA: {r['eta']}",
                tooltip=f"🎯 {z['name']} ({z['score']}/100)",
                icon=folium.Icon(color=marker_color, icon="star" if i == 0 else "info-sign")
            ).add_to(m)

        for step in active_route["steps"][1:-1]:
            folium.CircleMarker(
                location=step["coords"],
                radius=5,
                color="#FFFFFF",
                fill=True,
                fill_color=active_route["color"],
                fill_opacity=1.0,
                popup=f"<b>Waypoint {step['step']}: {step['title']}</b><br>{step['instruction']}",
                tooltip=f"Waypoint {step['step']}"
            ).add_to(m)

        all_lats = [origin_lat] + [r["zone"]["lat"] for r in all_routes]
        all_lons = [origin_lon] + [r["zone"]["lon"] for r in all_routes]
        m.fit_bounds([[min(all_lats) - 0.03, min(all_lons) - 0.03],
                      [max(all_lats) + 0.03, max(all_lons) + 0.03]])

    folium.LayerControl().add_to(m)

    st_folium(
        m,
        width=900,
        height=480,
        returned_objects=[],
        key=f"satellite_marine_map_{loc['name']}_{st.session_state.selected_zone_index}"
    )

    if has_pfz:
        st.markdown(f"#### 📋 Step-by-Step Directions: {active_route['label']} ({active_route['zone']['name']})")
        step_cols = st.columns(len(active_route["steps"]))
        for idx, s in enumerate(active_route["steps"]):
            with step_cols[idx]:
                st.markdown(
                    f"""
                    <div style="background:#1e293b; border-top:3px solid {active_route['color']}; border-radius:10px;
                                padding:12px; color:white; min-height:165px;">
                        <div style="font-weight:700; font-size:0.9rem;">Step {s['step']}</div>
                        <div style="font-size:0.8rem; color:{active_route['color']}; font-weight:600; margin-top:2px;">{s['title']}</div>
                        <div style="font-size:0.75rem; color:#cbd5e1; margin-top:6px; line-height:1.3;">{s['instruction']}</div>
                        <div style="font-size:0.7rem; color:#94a3b8; margin-top:6px;">📍 {s['coords'][0]}, {s['coords'][1]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

st.markdown("<div class='bottom-scroll-spacer'></div>", unsafe_allow_html=True)

# ====================== STICKY BOTTOM CHAT PANEL ======================
def submit_text():
    """Extracts text and immediately empties the text box to prevent infinite loops."""
    text = st.session_state.get("user_typed_input", "").strip()
    if text:
        st.session_state.pending_prompt = text
        st.session_state.user_typed_input = ""

with st.container(key="chat_dock_container"):
    # Client-side JavaScript helper for instant reactive submission without page reload
    st.markdown(
        """
        <script>
        window.submitMarinePrompt = function(text, isVoice) {
            if (!text || !text.trim()) return;
            text = text.trim();
            var inp = document.querySelector('.st-key-chat_dock_container input') || 
                      document.querySelector('div[data-testid="stTextInput"] input') || 
                      document.querySelector('input[type="text"]');
            var submitted = false;
            if (inp) {
                var lastVal = inp.value;
                var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeSetter.call(inp, text);
                if (inp._valueTracker) {
                    inp._valueTracker.setValue(lastVal);
                }
                inp.dispatchEvent(new Event('input', { bubbles: true }));
                inp.dispatchEvent(new Event('change', { bubbles: true }));
                setTimeout(function() {
                    inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                }, 60);
                submitted = true;
            }
            setTimeout(function() {
                var currentInp = document.querySelector('.st-key-chat_dock_container input');
                if (!submitted || (currentInp && currentInp.value === text)) {
                    var u = new URL(window.location.href);
                    u.searchParams.set('v_prompt', text);
                    if (isVoice) {
                        u.searchParams.set('from_voice', '1');
                    }
                    window.location.href = u.toString();
                }
            }, 350);
        };
        </script>
        """,
        unsafe_allow_html=True
    )

    # Interactive Voice Prompt Chips
    st.markdown(
        """
        <div style="display:flex; gap:8px; margin-bottom:6px; overflow-x:auto; white-space:nowrap; padding-bottom:2px;">
            <span style="font-size:0.75rem; color:#38bdf8; font-weight:600; align-self:center;">🎙️ Voice / Quick:</span>
            <button onclick="if(window.submitMarinePrompt){ window.submitMarinePrompt('Is it safe to fish in Goa today?', false); }" style="background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.35); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:2px 10px; cursor:pointer;">
                🌊 Goa Safety
            </button>
            <button onclick="if(window.submitMarinePrompt){ window.submitMarinePrompt('Show active alerts', false); }" style="background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.35); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:2px 10px; cursor:pointer;">
                🚨 Active Alerts
            </button>
            <button onclick="if(window.submitMarinePrompt){ window.submitMarinePrompt('Where is the best PFZ near Kochi?', false); }" style="background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.35); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:2px 10px; cursor:pointer;">
                🎯 Kochi PFZ
            </button>
            <button onclick="if(window.submitMarinePrompt){ window.submitMarinePrompt('Hi', false); }" style="background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.35); color:#e2e8f0; border-radius:14px; font-size:0.72rem; padding:2px 10px; cursor:pointer;">
                👋 Say Hi
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

    input_col, mic_col, send_col = st.columns([5.0, 1.8, 1.0])

    with input_col:
        st.text_input(
            "Marine Question",
            placeholder="Type question or click 🎙️ Speak (e.g., Hi, Is it safe to fish in Goa?, Show alerts)...",
            key="user_typed_input",
            on_change=submit_text,
            label_visibility="collapsed"
        )

    with mic_col:
        speech_lang = "en-IN" if st.session_state.language == "English" else "hi-IN"
        st.markdown(
            f"""
            <button id="dock-speech-btn" onclick="
                var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SR) {{
                    alert('Live voice recognition requires Chrome, Edge, or Safari. For other browsers, please use the Voice Recorder tab below.');
                    return;
                }}
                var b = this;
                var origBg = '#0284c7';
                var origHtml = '🎙️ Live Speak';
                b.style.backgroundColor = '#dc2626';
                b.style.boxShadow = '0 0 20px rgba(220, 38, 38, 0.9)';
                b.innerHTML = '🔴 Listening...';
                var r = new SR();
                r.lang = '{speech_lang}';
                r.interimResults = true;
                r.maxAlternatives = 1;
                var finalRecognized = '';
                r.onresult = function(e) {{
                    if (e.results && e.results.length > 0) {{
                        var text = e.results[0][0].transcript;
                        b.innerHTML = '🔴 ' + text.substring(0, 14) + '...';
                        if (e.results[0].isFinal) {{
                            finalRecognized = text;
                            b.style.backgroundColor = '#16a34a';
                            b.innerHTML = '✅ Transcribing...';
                            if (window.submitMarinePrompt) {{
                                window.submitMarinePrompt(text, true);
                            }}
                        }}
                    }}
                }};
                r.onerror = function(e) {{
                    b.style.backgroundColor = '#eab308';
                    b.innerHTML = '⚠️ Retry';
                    setTimeout(function(){{ b.style.backgroundColor = origBg; b.style.boxShadow = 'none'; b.innerHTML = origHtml; }}, 2500);
                }};
                r.onend = function() {{
                    setTimeout(function(){{ if (!finalRecognized) {{ b.style.backgroundColor = origBg; b.style.boxShadow = 'none'; b.innerHTML = origHtml; }} }}, 2000);
                }};
                r.start();
            " style="width:100%; height:42px; background:#0284c7; color:white; border:none; border-radius:10px; font-weight:700; font-size:0.9rem; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:6px; box-shadow:0 4px 12px rgba(2,132,199,0.3); transition:all 0.2s ease;">
                🎙️ Live Speak
            </button>
            """,
            unsafe_allow_html=True
        )

    with send_col:
        st.button("Send ➤", on_click=submit_text, use_container_width=True, type="primary")

    with st.expander("🎙️ High-Accuracy Voice Input (Groq Whisper AI)", expanded=False):
        st.caption("Works on all devices and mobile browsers. Speak your question and stop recording:")
        audio_file = st.audio_input(
            "Record Audio File",
            label_visibility="collapsed",
            key="dock_mic_input"
        )

# Detect Audio Input from 1-Click Web Speech Recognition
if "v_prompt" in st.query_params:
    voice_text = str(st.query_params.get("v_prompt", "")).strip()
    is_from_voice = str(st.query_params.get("from_voice", "1")) == "1"
    try:
        del st.query_params["v_prompt"]
        if "from_voice" in st.query_params:
            del st.query_params["from_voice"]
    except Exception:
        pass
    if voice_text:
        st.session_state.pending_prompt = voice_text
        if is_from_voice:
            st.session_state.voice_mode_triggered = True
        st.toast(f"🗣️ Heard: {voice_text}", icon="🎙️")

# Detect Audio File Input from Whisper widget
if audio_file is not None:
    try:
        audio_bytes = audio_file.getvalue()
    except Exception:
        audio_bytes = audio_file.read()

    if audio_bytes and len(audio_bytes) > 200:
        audio_hash = hashlib.md5(audio_bytes).hexdigest()
        if st.session_state.last_audio_hash != audio_hash:
            st.session_state.last_audio_hash = audio_hash
            with st.spinner("🎧 Transcribing your voice via Groq Whisper..."):
                transcribed = transcribe_voice_query(audio_bytes, st.session_state.language)
                if transcribed:
                    st.session_state.pending_prompt = transcribed
                    st.session_state.voice_mode_triggered = True
                    st.toast(f"🗣️ Transcribed: {transcribed}", icon="🎙️")
                else:
                    st.toast("⚠️ Could not detect speech clearly. Please try speaking closer to your mic.", icon="🎙️")

# ====================== AGENT ORCHESTRATION ======================
active_prompt = None
if st.session_state.pending_prompt:
    active_prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None  # Consumed immediately

if active_prompt:
    st.session_state.messages.append({"role": "user", "content": active_prompt})

    with st.chat_message("user"):
        st.markdown(active_prompt)

    with st.chat_message("assistant"):
        # 1. Advanced NLP Intent Analysis (< 1ms)
        nlp_plan = advanced_nlp_agent(active_prompt)
        weather_data = None
        pfz_data = None
        alert_data = None
        location_name = None
        agent_log = [f"NLP Intent Agent ({nlp_plan['intent']})"]

        # If it's a greeting, clear any previous map location so old maps don't persist
        if nlp_plan["intent"] in ["GREETING", "BOT_IDENTITY", "GRATITUDE", "NORMAL_CHAT"]:
            st.session_state.map_location = None
            st.session_state.pfz_data = None

        # Special handling for SHOW_ALERTS
        if nlp_plan["intent"] == "SHOW_ALERTS":
            agent_log.append("Alert Agent (All Locations)")
            st.session_state.show_alerts_panel = True
            render_active_alerts_panel(st.session_state.language)

        # 2. Only invoke Weather & PFZ agents if it's a true marine location query
        if nlp_plan["needs_weather"] and nlp_plan.get("location"):
            loc = nlp_plan["location"]
            location_name = loc["name"]
            weather_data = weather_agent(loc["lat"], loc["lon"])
            st.session_state.map_location = loc
            agent_log.append("Weather Agent")
            render_weather_card(weather_data, location_name)

            # Always generate alert for the location
            alert_data = alert_agent(weather_data, location_name, st.session_state.language)
            agent_log.append(f"Alert Agent ({alert_data['level']})")
            render_alert_banner(alert_data)

            if nlp_plan.get("needs_pfz"):
                pfz_data = pfz_agent(loc, weather_data)
                st.session_state.pfz_data = pfz_data
                st.session_state.selected_zone_index = 0
                agent_log.append("PFZ Agent")
                agent_log.append("Multi-Route Navigation Agent")
                render_pfz_section(pfz_data)

        # 3. Fast Response Agent (Zero crashes, safe fallback)
        agent_log.append("Response Agent")
        final_answer = response_agent(
            active_prompt,
            nlp_plan,
            weather_data,
            pfz_data,
            alert_data,
            language=st.session_state.language
        )
        st.markdown(final_answer)

        # Voice output: Automatically speak answer if asked via voice or if auto_speak is active
        should_speak = st.session_state.get("voice_mode_triggered", False) or st.session_state.get("auto_speak", False)
        render_tts_button(final_answer, st.session_state.language, auto_play=should_speak, msg_id="latest")
        st.session_state.voice_mode_triggered = False  # Reset one-shot voice trigger

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
