#!/usr/bin/env python3
# fashion_show.py
# Robust: fetch weather → call LLM → parse & enforce two outfits → display a 2×3 gallery,
# with AVIF support via Pillow fallback.

import os
import re
import glob
import random
import requests
import pytz
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image as PILImage
from datetime import datetime

# -------------------- CONFIG --------------------
API_URL         = "https://api.groq.com/openai/v1/chat/completions"
API_KEY         = "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"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
LAT, LON        = 33.9055, 130.8113   # Kitakyushu, Wakamatsu

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, "image")

# -------------------- USER INFO --------------------
personal_info = {
    "height": "182 cm",
    "weight": "67 kg",
    "skin_tone": "warm",
    "body_type": "skinny",
    "face_shape": "long",
    "preferred_color_scheme": "complementary or trending colors"
}

# -------------------- WARDROBE --------------------
wardrobe = [
    {"item_id":"001","type":"shirt",  "color":"mocha mousse","base":"shirt_mocha_mousse"},
    {"item_id":"002","type":"jeans",  "color":"black",       "base":"jeans_black"},
    {"item_id":"003","type":"shirt",  "color":"white",       "base":"shirt_white"},
    {"item_id":"004","type":"pants",  "color":"navy",        "base":"pants_navy"},
    {"item_id":"005","type":"jacket", "color":"gray",        "base":"jacket_gray"},
    {"item_id":"006","type":"shoes",  "color":"brown",       "base":"shoes_brown"},
    {"item_id":"007","type":"shoes",  "color":"black",       "base":"shoes_black"},
    {"item_id":"008","type":"shoes",  "color":"white",       "base":"shoes_white"},
    {"item_id":"009","type":"shirt",  "color":"butter yellow","base":"shirt_butter_yellow"},
    {"item_id":"010","type":"pants",  "color":"chocolate brown","base":"pants_chocolate_brown"},
    {"item_id":"011","type":"shirt",  "color":"wispy pink",   "base":"shirt_wispy_pink"},
    {"item_id":"012","type":"sweater","color":"forest green", "base":"sweater_forest_green"},
    # …add items 013–025 here…
]

CATS = {
    "tops":    {"shirt","jacket","sweater"},
    "bottoms": {"pants","jeans"},
    "shoes":   {"shoes"}
}

# -------------------- WEATHER --------------------
def get_weather(lat, lon):
    try:
        r = requests.get(WEATHER_API_URL,
                         params={"latitude":lat,"longitude":lon,"current_weather":True},
                         timeout=5)
        r.raise_for_status()
        w = r.json()["current_weather"]
        t, code = w["temperature"], w["weathercode"]
        cond = ("clear" if code<10 else "cloudy" if code<50 else "rainy" if code<70 else "snowy")
        cond += " & cold" if t<10 else " & hot" if t>30 else " & mild"
        m = datetime.now(pytz.utc).month
        season = ("spring" if 3<=m<=5 else "summer" if 6<=m<=8 else "autumn" if 9<=m<=11 else "winter")
        return t, season, cond
    except:
        return None, None, None

# -------------------- PROMPT --------------------
def build_prompt(event, temp, season, cond):
    ui = personal_info
    user_block = "\n".join(f"- {k.replace('_',' ').title()}: {v}" for k,v in ui.items())
    ward_block = "\n".join(f"- {w['item_id']}: {w['type']} {w['color']}" for w in wardrobe)
    return "\n".join([
        "You are a professional fashion AI assistant.",
        "User details:", user_block, "",
        "Wardrobe items:", ward_block, "",
        f"Event: {event}",
        f"Temp: {temp}°C | Season: {season} | Weather: {cond}", "",
        "Provide TWO distinct outfits. Each must have exactly one top, one bottom, one shoes.",
        "Output two lines of comma-separated IDs, e.g.:",
        "009,004,006",
        "003,002,008"
    ])

# -------------------- LLM CALL --------------------
def call_llm(prompt):
    r = requests.post(API_URL,
                      json={"model":"meta-llama/llama-4-scout-17b-16e-instruct",
                            "messages":[{"role":"user","content":prompt}],
                            "max_tokens":100},
                      headers={"Content-Type":"application/json","Authorization":f"Bearer {API_KEY}"},
                      timeout=10)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

# -------------------- PARSE & VALIDATE OUTFITS --------------------
def parse_outfits(raw):
    lines = re.findall(r"(\d{3}\s*,\s*\d{3}\s*,\s*\d{3})", raw)
    outfits = []
    for ln in lines[:2]:
        ids = re.findall(r"\d{3}", ln)
        cats = { w["type"] for i in ids for w in wardrobe if w["item_id"]==i }
        if (cats & CATS["tops"] and cats & CATS["bottoms"] and cats & CATS["shoes"]):
            outfits.append(ids)
    def rnd_triplet():
        return [
            random.choice([w["item_id"] for w in wardrobe if w["type"] in CATS["tops"]]),
            random.choice([w["item_id"] for w in wardrobe if w["type"] in CATS["bottoms"]]),
            random.choice([w["item_id"] for w in wardrobe if w["type"] in CATS["shoes"]])
        ]
    while len(outfits)<2:
        outfits.append(rnd_triplet())
    return outfits

# -------------------- DISPLAY GALLERY --------------------
def show_gallery(outfits):
    images, titles = [], []
    for outfit in outfits:
        for item_id in outfit:
            w = next(w for w in wardrobe if w["item_id"]==item_id)
            matches = glob.glob(os.path.join(IMAGES_DIR, f"{w['base']}.*"))
            if not matches:
                images.append(None)
                titles.append(f"Missing\n{item_id}")
                continue
            path = matches[0]
            ext = os.path.splitext(path)[1].lower()
            if ext==".avif":
                img = np.array(PILImage.open(path))
            else:
                img = mpimg.imread(path)
            images.append(img)
            titles.append(f"{w['type'].capitalize()}\n{w['color']}")
    fig, axes = plt.subplots(2,3,figsize=(12,8))
    for ax, img, title in zip(axes.flatten(), images, titles):
        if img is not None:
            ax.imshow(img)
        ax.axis("off")
        ax.set_title(title, fontsize=10)
    plt.tight_layout()
    plt.show()

# -------------------- MAIN --------------------
if __name__=="__main__":
    event = input("Enter event (e.g., summer party): ").strip()
    temp, season, cond = get_weather(LAT, LON)
    if temp is None:
        temp, season, cond = 20, "summer", "clear & mild"

    prompt = build_prompt(event, temp, season, cond)
    print("Prompting LLM…")
    raw = ""
    try:
        raw = call_llm(prompt)
    except Exception as e:
        print("LLM error:", e)
    print("LLM returned:\n", raw)

    outfits = parse_outfits(raw)
    print("Final outfits:", outfits)
    show_gallery(outfits)
