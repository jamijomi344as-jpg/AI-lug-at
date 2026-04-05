import os
import threading
import asyncio
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from deep_translator import GoogleTranslator

# --- 1. PYROGRAM MOTORINI ISHGA TUSHIRISH ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- 2. RENDER.COM UCHUN ALDOVCHI SERVER ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot 24/7 ishlayapti!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()


# --- 3. SOZLAMALAR ---
API_ID = 36053423
API_HASH = "82f39002cfa480485590bf961e20bf55"
BOT_TOKEN = "8798789058:AAGKA20LbcczGx4N0YrSLMhm2Wj1tci-V4E"
MW_API_KEY = "SHU_YERGA_MERRIAM_WEBSTER_KALITINGIZNI_QOYING" # <-- Olingan yangi kalitni shu yerga kiritasiz

app = Client("dictionary_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True) 
user_modes = {}


# --- 4. MERRIAM-WEBSTER FUNKSIYASI ---
def get_mw_details(word):
    """Merriam-Webster'dan so'z ta'riflari va ovoz faylini olish"""
    url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={MW_API_KEY}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            return {"ok": False}
            
        data = res.json()
        
        # Agar so'z topilmasa
        if not data or not isinstance(data[0], dict):
            return {"ok": False}
            
        # Transkripsiya va Ovoz fayli nomini ajratib olish
        hwi = data[0].get('hwi', {})
        prs = hwi.get('prs', [{}])[0]
        phonetic = prs.get('mw', 'N/A')
        audio_name = prs.get('sound', {}).get('audio') # Ovozli fayl nomi
        
        meanings_text = ""
        
        # Eng asosiy 3 ta ma'noni olish
        for item in data[:3]:
            part_of_speech = item.get('fl', 'bilinmaydi') # noun, verb...
            shortdefs = item.get('shortdef', [])
            
            if shortdefs:
                meanings_text += f"\n🔹 **{part_of_speech.capitalize()}**: _{shortdefs[0]}_\n"

        return {
            "ok": True,
            "phonetic": f"/{phonetic}/" if phonetic != 'N/A' else "N/A",
            "meanings_text": meanings_text if meanings_text else "Ta'rif topilmadi",
            "audio_name": audio_name
        }
    except Exception:
        return {"ok": False}


# --- 5. TUGMALAR VA BUYRUQLAR ---
def get_keyboard(user_id, audio_name=None):
    mode = user_modes.get(user_id, "en_uz")
    btn_text = "🔄 Inglizcha ➡️ O'zbekcha" if mode == "en_uz" else "🔄 O'zbekcha ➡️ Inglizcha"
    
    # Asosiy tugmalar
    buttons = [[InlineKeyboardButton(btn_text, callback_data="toggle_mode")]]
    
    # Agar ovoz fayli mavjud bo'lsa, "O'qilishi" tugmasini qo'shamiz
    if audio_name:
        buttons.append([InlineKeyboardButton("🔊 O'qilishi", callback_data=f"audio_{audio_name}")])
        
    buttons.append([InlineKeyboardButton("📚 Dasturchi bilan aloqa", url="https://t.me/durov")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    user_modes[user_id] = "en_uz"
    await message.reply_text(
        "👋 **Salom! Men Merriam-Webster akademik bazasiga ulangan lug'at botiman.**\n\n"
        "Menga istalgan so'zni yuboring, men uning tarjimasini, professional ta'rifini va talaffuzini keltiraman:",
        reply_markup=get_keyboard(user_id)
    )

@app.on_callback_query(filters.regex("toggle_mode"))
async def toggle_mode(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    current_mode = user_modes.get(user_id, "en_uz")
    new_mode = "uz_en" if current_mode == "en_uz" else "en_uz"
    user_modes[user_id] = new_mode
    text = "✅ **O'zbekchadan Inglizchaga**" if new_mode == "uz_en" else "✅ **Inglizchadan O'zbekchaga**"
    await callback_query.answer("Til o'zgartirildi!", show_alert=False)
    await callback_query.message.edit_text(f"{text}\n\nMenga so'z yuboring:", reply_markup=get_keyboard(user_id))

# --- OVOZ YUBORISH FUNKSIYASI ---
@app.on_callback_query(filters.regex(r"^audio_"))
async def send_audio(client, callback_query: CallbackQuery):
    # Tugmadan fayl nomini ajratib olamiz
    audio_name = callback_query.data.split("_", 1)[1]
    
    # Merriam-Webster API ovoz fayllarini joylashuvi qoidalari
    if audio_name.startswith("bix"):
        subdir = "bix"
    elif audio_name.startswith("gg"):
        subdir = "gg"
    elif audio_name[0].isalpha():
        subdir = audio_name[0]
    else:
        subdir = "number"
        
    # URL ni yig'ish
    audio_url = f"https://media.merriam-webster.com/audio/prons/en/us/mp3/{subdir}/{audio_name}.mp3"
    
    await callback_query.answer("Ovoz yuklanmoqda... 🔊")
    try:
        # Telegram orqali audioni bevosita url dan yuborish
        await client.send_voice(callback_query.message.chat.id, voice=audio_url)
    except Exception:
        await callback_query.message.reply_text("⚠️ Ovozni yuklab olishda xatolik yuz berdi.")

# --- ASOSIY XABARLARNI QABUL QILISH ---
@app.on_message(filters.text & filters.private)
async def handle_message(client, message):
    word = message.text.strip()
    user_id = message.from_user.id
    mode = user_modes.get(user_id, "en_uz")
    
    if len(word.split()) > 3: 
        await message.reply_text("Iltimos, qisqaroq so'z yoki ibora yuboring.")
        return
    
    wait_msg = await message.reply_text("🔍 Qidirilmoqda...")
    
    try:
        word_to_translate = word.lower()

        # O'zbekchadan Inglizchaga va teskari tarjima
        if mode == "en_uz":
            uz_translation = GoogleTranslator(source='en', target='uz').translate(word_to_translate)
            en_word, uz_word = word, uz_translation
        else:
            en_translation = GoogleTranslator(source='uz', target='en').translate(word_to_translate)
            en_word, uz_word = en_translation, word

        # Merriam-Webster
        details = get_mw_details(en_word)

        text = f"🔤 **Inglizcha**: `{en_word.capitalize()}`\n"
        text += f"🇺🇿 **O'zbekcha**: `{uz_word.capitalize()}`\n\n"
        
        audio_to_pass = None
        
        if details["ok"]:
            text += f"🗣 **Talaffuz**: `{details['phonetic']}`\n"
            text += f"📖 **Merriam-Webster izohi**: {details['meanings_text']}"
            audio_to_pass = details.get("audio_name") # Agar audio bor bo'lsa
        else:
            if mode == "uz_en":
                text += "⚠️ _Inglizcha aniq ta'rif topilmadi._"
        
        await wait_msg.edit_text(text, reply_markup=get_keyboard(user_id, audio_to_pass))
    except Exception as e:
        await wait_msg.edit_text(f"Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.\n`{e}`")


# --- 6. ISHGA TUSHIRISH ---
async def main():
    async with app:
        print("✅ Merriam-Webster Bot muvaffaqiyatli ishga tushdi!")
        await idle()

if __name__ == "__main__":
    loop.run_until_complete(main())
