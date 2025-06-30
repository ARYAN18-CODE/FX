import requests
import json
from datetime import datetime
import pytz

# Constants
API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = "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" # Replace with your actual API key
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
LAT, LON = 35.6895, 139.6917  # Default: Tokyo

# Updated wardrobe with trending colors
wardrobe = [
    {"item_id": "001", "type": "shirt", "color": "mocha mousse", "texture": "cotton", "pattern": "solid", "season": "summer"},
    {"item_id": "002", "type": "jeans", "color": "black", "texture": "denim", "pattern": "plain", "season": "all"},
    {"item_id": "003", "type": "shirt", "color": "white", "texture": "linen", "pattern": "solid", "season": "summer"},
    {"item_id": "004", "type": "pants", "color": "navy", "texture": "cotton", "pattern": "plain", "season": "all"},
    {"item_id": "005", "type": "jacket", "color": "gray", "texture": "wool", "pattern": "solid", "season": "winter"},
    {"item_id": "006", "type": "shoes", "color": "brown", "texture": "leather", "pattern": "plain", "season": "all"},
    {"item_id": "007", "type": "shoes", "color": "black", "texture": "suede", "pattern": "plain", "season": "winter"},
    {"item_id": "008", "type": "shoes", "color": "white", "texture": "canvas", "pattern": "plain", "season": "summer"},
    {"item_id": "009", "type": "shirt", "color": "butter yellow", "texture": "silk", "pattern": "solid", "season": "summer"},
    {"item_id": "010", "type": "pants", "color": "chocolate brown", "texture": "linen", "pattern": "solid", "season": "summer"},
    {"item_id": "011", "type": "shirt", "color": "wispy pink", "texture": "cotton", "pattern": "solid", "season": "summer"}
]

personal_info = {
    "height": "182 cm",
    "weight": "67 kg",
    "skin_tone": "warm",
    "body_type": "skinny",
    "face_shape": "long",
    "preferred_color_scheme": "complementary or trending colors"
}

def get_weather():
    try:
        res = requests.get(WEATHER_API_URL, params={"latitude": LAT, "longitude": LON, "current_weather": True})
        res.raise_for_status()
        weather = res.json()["current_weather"]
        temp = weather["temperature"]
        code = weather["weathercode"]

        if 0 <= code < 10:
            condition = "clear"
        elif 10 <= code < 20:
            condition = "partly cloudy"
        elif 20 <= code < 30:
            condition = "cloudy"
        elif 30 <= code < 40:
            condition = "foggy"
        elif 50 <= code < 60:
            condition = "rainy"
        elif 60 <= code < 70:
            condition = "stormy"
        elif 70 <= code < 80:
            condition = "snowy"
        else:
            condition = "unknown"

        if condition in ["clear", "partly cloudy", "cloudy", "foggy"]:
            if temp < 10:
                condition += " & cold"
            elif temp > 30:
                condition += " & hot"
            else:
                condition += " & mild"

        month = datetime.now(pytz.utc).month
        season = (
            "spring" if 3 <= month <= 5 else
            "summer" if 6 <= month <= 8 else
            "autumn" if 9 <= month <= 11 else
            "winter"
        )

        return temp, season, condition
    except Exception as e:
        print(f"⚠️ Weather fetch failed: {e}")
        return "unknown", "unknown", "unknown"

def build_prompt(event, temp, season, condition):
    items = "\n".join([
        f"- {w['item_id']}: {w['color']} {w['texture']} {w['pattern']} {w['type']} (season: {w['season']})"
        for w in wardrobe
    ])
    return f"""
You are a professional fashion AI assistant.
User details:
- Height: {personal_info['height']}
- Weight: {personal_info['weight']}
- Skin tone: {personal_info['skin_tone']}
- Body type: {personal_info['body_type']}
- Face shape: {personal_info['face_shape']}
- Preferred color scheme: {personal_info['preferred_color_scheme']}

Wardrobe items:
{items}

Event: {event}
Current temperature: {temp}°C
Current season: {season}
Weather condition: {condition}

Select the best one-day full outfit including shoes appropriate for the weather condition.
Follow color theory principles (e.g., complementary, analogous, trending colors) in your selection.
ONLY OUTPUT THE CHOSEN ITEM IDS SEPARATED BY COMMAS. Example: 003, 004, 008
DO NOT PROVIDE ANY EXPLANATION OR ADDITIONAL TEXT.
"""

def call_groq(prompt):
    res = requests.post(API_URL,
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
                        data=json.dumps({
                            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 50,
                            "temperature": 0.7
                        }))
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"].strip()

def display_outfit(ids):
    id_list = [id_.strip() for id_ in ids.split(",") if id_.strip().isdigit()]
    print("\n🎉 Recommended Outfit:")
    for id_ in id_list:
        item = next((w for w in wardrobe if w["item_id"] == id_), None)
        if item:
            print(f"✅ {item['type'].capitalize()}: {item['color']} {item['texture']} {item['pattern']} (season: {item['season']})")
        else:
            print(f"⚠️ Unknown item ID: {id_}")

def main():
    event = input("Enter event (e.g., office party, wedding, casual outing): ").strip()
    temp, season, condition = get_weather()
    print(f"\n🌤 Temp: {temp}°C | Season: {season} | Condition: {condition}\n")

    prompt = build_prompt(event, temp, season, condition)
    print("📝 Asking Groq...")
    ids = call_groq(prompt)
    print(f"\nGroq returned IDs: {ids}")
    display_outfit(ids)

if __name__ == "__main__":
    main()
