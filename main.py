import os
import threading
import asyncio
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from gtts import gTTS
from deep_translator import GoogleTranslator

# --- 1. PYROGRAM MOTORINI ISHGA TUSHIRISH ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- 2. RENDER UCHUN ALDOVCHI SERVER ---
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

app = Client("dictionary_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True) 

# --- 4. TUGMALAR ---
def get_keyboard(audio_word=None):
    buttons = []
    if audio_word:
        buttons.append([InlineKeyboardButton("🔊 O'qilishi (Ovozli)", callback_data=f"audio_{audio_word}")])
    buttons.append([InlineKeyboardButton("📚 Dasturchi bilan aloqa", url="https://t.me/durov")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 **Salom! Men sizning Lug'at botingizman.**\n\n"
        "Menga xohlagan o'zbekcha yoki inglizcha so'zingizni yuboring. Men uning tarjimasini, ta'rifini va audiosini topib beraman!"
    )

# --- 5. OVOZ YASASH FUNKSIYASI (gTTS) ---
@app.on_callback_query(filters.regex(r"^audio_"))
async def send_audio(client, callback_query: CallbackQuery):
    word = callback_query.data.split("_", 1)[1]
    await callback_query.answer("Ovoz tayyorlanmoqda... 🔊")
    
    try:
        tts = gTTS(text=word, lang='en', slow=False)
        filename = f"{word}.mp3"
        tts.save(filename)
        await client.send_voice(callback_query.message.chat.id, voice=filename)
        os.remove(filename)
    except Exception as e:
        await callback_query.message.reply_text("⚠️ Ovozni yasashda xatolik yuz berdi.")

# --- 6. KLASSIK LUG'AT FUNKSIYASI ---
def get_dictionary_info(word):
    """Tekin Free Dictionary API orqali so'z ma'lumotlarini olish"""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return None
        data = res.json()[0]
        
        # Transkripsiya
        phonetic = data.get("phonetic", "")
        if not phonetic:
            for phon in data.get("phonetics", []):
                if "text" in phon and phon["text"]:
                    phonetic = phon["text"]
                    break
                    
        meanings = data.get("meanings", [])
        if not meanings:
            return None
            
        # Ta'rif, misol va sinonimlar
        definition, example, synonyms = "", "", []
        
        for meaning in meanings:
            for def_dict in meaning.get("definitions", []):
                if not definition:
                    definition = def_dict.get("definition", "")
                if not example and "example" in def_dict:
                    example = def_dict.get("example", "")
            if not synonyms and meaning.get("synonyms"):
                synonyms = meaning.get("synonyms")[:3]
                
        return {
            "phonetic": phonetic,
            "definition": definition,
            "example": example,
            "synonyms": ", ".join(synonyms) if synonyms else "Topilmadi"
        }
    except Exception:
        return None

@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def handle_message(client, message):
    text = message.text.strip()
    
    if len(text.split()) > 5: 
        return 
    
    wait_msg = await message.reply_text("🔍 Qidirilmoqda...")
    
    try:
        # 1. So'zni Ingliz tiliga o'giramiz
        translator_to_en = GoogleTranslator(source='auto', target='en')
        english_word = translator_to_en.translate(text).lower()
        
        # 2. Inglizcha so'zni O'zbek tiliga qayta o'giramiz (to'g'ri tarjima olish uchun)
        translator_to_uz = GoogleTranslator(source='en', target='uz')
        uzbek_word = translator_to_uz.translate(english_word).lower()
        
        # 3. Inglizcha so'zning ta'riflarini tekin bazadan qidiramiz
        dict_info = get_dictionary_info(english_word)
        
        response_text = f"🔤 **Inglizcha**: `{english_word.capitalize()}`\n"
        response_text += f"🇺🇿 **O'zbekcha**: `{uzbek_word.capitalize()}`\n\n"
        
        if dict_info:
            if dict_info['phonetic']: 
                response_text += f"🗣 **Transkripsiya**: `{dict_info['phonetic']}`\n"
            response_text += f"📖 **Ta'rif**: {dict_info['definition']}\n"
            
            if dict_info['example']: 
                # Misolni ham o'zbekchaga tarjima qilib qo'shamiz
                uz_example = translator_to_uz.translate(dict_info['example'])
                response_text += f"💡 **Misol**: {dict_info['example']} - _{uz_example}_\n"
                
            response_text += f"🔗 **Sinonimlar**: {dict_info['synonyms']}"
        else:
            response_text += "⚠️ _Batafsil inglizcha ta'rif va misollar topilmadi._"

        await wait_msg.edit_text(response_text, reply_markup=get_keyboard(english_word))
        
    except Exception as e:
        await wait_msg.edit_text("⚠️ Tarjima qilishda xatolik yuz berdi. Internet yoki baza uzilib qolgan bo'lishi mumkin.")

# --- 7. ISHGA TUSHIRISH ---
async def main():
    async with app:
        print("✅ Klassik Lug'at Bot muvaffaqiyatli ishga tushdi!")
        await idle()

if __name__ == "__main__":
    loop.run_until_complete(main())
