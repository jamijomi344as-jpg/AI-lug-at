import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import asyncio
import requests

# --- 1. RENDER.COM UCHUN ALDOVCHI SERVER (24/7 ishlashi uchun) ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot 24/7 ishlayapti!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("", port), DummyServer)
    server.serve_forever()

# Serverni orqa fonda ishga tushiramiz
threading.Thread(target=run_dummy_server, daemon=True).start()


# --- 2. PYROGRAM XATOSINI OLDINI OLISH (Python 3.14+ uchun) ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from deep_translator import GoogleTranslator

# --- 3. SOZLAMALAR ---
API_ID = 36053423
API_HASH = "82f39002cfa480485590bf961e20bf55"
BOT_TOKEN = "8798789058:AAGKA20LbcczGx4N0YrSLMhm2Wj1tci-V4E"

app = Client("dictionary_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Foydalanuvchilarning qaysi tilda ekanligini saqlash uchun lug'at
user_modes = {}


# --- 4. FUNKSIYALAR ---
def get_details(word):
    """Inglizcha so'zning ta'rifi va misollarini API dan olish"""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()[0]
            phonetic = data.get('phonetic', 'N/A')
            meanings = data['meanings'][0]['definitions'][0]
            syns = data['meanings'][0].get('synonyms', [])
            return {
                "ok": True,
                "phonetic": phonetic,
                "definition": meanings.get('definition', 'Topilmadi'),
                "example": meanings.get('example', 'Mavjud emas'),
