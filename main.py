import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import asyncio
import requests

# --- 1. RENDER.COM UCHUN ALDOVCHI SERVER ---
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

# --- 2. PYROGRAM XATOSINI OLDINI OLISH ---
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
user_modes = {}

# --- 4. FUNKSIYALAR ---
def get_details(word):
    """Inglizcha so'zning ta'riflari va misollarini aqlli va tartibli izlash"""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()[0]
            phonetic = data.get('phonetic', 'N/A')
            
            meanings_text = ""
            synonyms_set = set()

            # Barcha ma'nolarni (maksimum 3 xilini) alohida ajratib olamiz
            for meaning in data['meanings'][:3]:
                part_of_speech = meaning.get('partOfSpeech', 'bilinmaydi')
                def_obj = meaning['definitions'][0] # Shu guruhning eng asosiy ma'nosi
                
                definition = def_obj.get('definition', '')
                example = def_obj.get('example', '')
                
                # Matnni chiroyli qilib yig'amiz
                meanings_text += f"\n🔹 **{part_of_speech.capitalize()}**: {definition}\n"
                if example:
                    meanings_text += f"   _💡 Misol: {example}_\n"
                    
                # Sinonimlarni yig'ish (faqat mavjudlarini)
                for syn in meaning.get('synonyms', []):
                    synonyms_set.add(syn)

            # Sinonimlardan faqat 5 tasini ko'rsatamiz
            syns = list(synonyms_set)[:5]

            return {
                "ok": True,
                "phonetic": phonetic,
                "meanings_text": meanings_text if meanings_text else "\nTopilmadi",
                "synonyms": ", ".join(syns) if syns else "Mavjud emas"
            }
        return {"ok": False}
    except:
        return {"ok": False}

def get_keyboard(user_id):
    mode = user_modes.get(user_id, "en_uz")
    btn_text = "🔄 Inglizcha ➡️ O'zbekcha" if mode == "en_uz" else "🔄 O'zbekcha ➡️ Inglizcha"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_text, callback_data="toggle_mode")],
        [InlineKeyboardButton("📚 Dasturchi bilan aloqa", url="https://t.me/durov")]
    ])

# --- 5. BOT BUYRUQLARI ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    user_modes[user_id] = "en_uz"
    await message.reply_text(
        "👋 **Salom! Men aqlli lug'at botiman.**\n\n"
        "Menga so'z yuboring. Tarjima yo'nalishini quyidagi tugma orqali o'zgartirishingiz mumkin:",
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

        if mode == "en_uz":
            uz_translation = GoogleTranslator(source='en', target='uz').translate(word_to_translate)
            en_word, uz_word = word, uz_translation
        else:
            en_translation = GoogleTranslator(source='uz', target='en').translate(word_to_translate)
            en_word, uz_word = en_translation, word

        details = get_details(en_word)

        text = f"🔤 **Inglizcha**: `{en_word.capitalize()}`\n"
        text += f"🇺🇿 **O'zbekcha**: `{uz_word.capitalize()}`\n\n"
        
        if details["ok"]:
            text += f"🗣 **Transkripsiya**: `{details['phonetic']}`\n"
            text += f"📖 **Ma'nolari**:{details['meanings_text']}\n\n"
            text += f"🔗 **Sinonimlar**: {details['synonyms']}"
        else:
            if mode == "uz_en":
                text += "⚠️ _Inglizcha ta'rif topilmadi._"
        
        await wait_msg.edit_text(text, reply_markup=get_keyboard(user_id))
    except Exception as e:
        await wait_msg.edit_text(f"Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.\n`{e}`")

# --- 6. ISHGA TUSHIRISH ---
async def main():
    async with app:
        print("✅ Bot muvaffaqiyatli ishga tushdi!")
        await idle()

if __name__ == "__main__":
    loop.run_until_complete(main())
