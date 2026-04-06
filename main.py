import os
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from gtts import gTTS

# --- 1. PYROGRAM MOTORINI ISHGA TUSHIRISH ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import google.generativeai as genai
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- 2. RENDER UCHUN ALDOVCHI SERVER (24/7 ishlashi uchun) ---
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
GEMINI_API_KEY = "AIzaSyC72VvxxboViR-c2kuzoK2_PFGkVP4IFsM" # Sizning kalitingiz kiritildi!

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

app = Client("dictionary_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True) 

# --- 4. TUGMALAR ---
def get_keyboard(audio_word=None):
    buttons = []
    # Agar so'z mavjud bo'lsa, uni ovozli qilib berish tugmasi
    if audio_word:
        buttons.append([InlineKeyboardButton("🔊 O'qilishi (Ovozli)", callback_data=f"audio_{audio_word}")])
        
    buttons.append([InlineKeyboardButton("📚 Dasturchi bilan aloqa", url="https://t.me/durov")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 **Salom! Men sizning Shaxsiy AI Lug'at botingizman.**\n\n"
        "Menga xohlagan o'zbekcha yoki inglizcha so'zingizni yuboring. Men uning **aniq ma'nosini**, o'qilishini, misolini va audiosini darhol topib beraman!"
    )

# --- 5. OVOZ YASASH FUNKSIYASI (gTTS) ---
@app.on_callback_query(filters.regex(r"^audio_"))
async def send_audio(client, callback_query: CallbackQuery):
    word = callback_query.data.split("_", 1)[1]
    await callback_query.answer("Ovoz tayyorlanmoqda... 🔊")
    
    try:
        # Tekin Google Text-to-Speech orqali mp3 yasaymiz
        tts = gTTS(text=word, lang='en', slow=False)
        filename = f"{word}.mp3"
        tts.save(filename)
        
        # Tayyor faylni Telegramga tashlaymiz
        await client.send_voice(callback_query.message.chat.id, voice=filename)
        
        # Tashlab bo'lgach, server axlatga to'lmasligi uchun o'chirib tashlaymiz
        os.remove(filename)
    except Exception as e:
        await callback_query.message.reply_text("⚠️ Ovozni yasashda xatolik yuz berdi.")

# --- 6. AQLLI TARJIMA VA TA'RIF (ASOSIY QISM) ---
@app.on_message(filters.text & filters.private)
async def handle_message(client, message):
    word = message.text.strip()
    
    if len(word.split()) > 4: 
        await message.reply_text("Iltimos, bitta so'z yoki qisqaroq ibora yuboring.")
        return
    
    wait_msg = await message.reply_text("🧠 Sun'iy intellekt tahlil qilmoqda...")
    
    # GEMINI UCHUN SUPER-BUYRUQ
    prompt = f"""
    Sen professional va aqlli ingliz-o'zbek lug'atbotisan. 
    Foydalanuvchi quyidagi so'zni yubordi: "{word}"

    Vazifang:
    1. Agar so'z o'zbek tilida bo'lsa (masalan "maktub"), uning inglizcha tarjimasini top ("letter").
    2. DIQQAT: Inglizcha so'zning KO'P MA'NOLARI BO'LSA, FAQAT foydalanuvchi yuborgan o'zbekcha so'zga mos keladigan ma'nosini ol! (Masalan, "maktub" deb yuborilgan bo'lsa, "letter"ning alfavit harfi ma'nosini emas, balki "yozilgan xat/xabar" ma'nosini ol).
    3. Ta'rif, misol va sinonimlar AYNAN SHU TANLANGAN MA'NOGA mos bo'lishi shart.
    
    Javobni AYNAN quyidagi formatda, ortiqcha gaplarsiz qaytar. Boshida va oxirida hechnarsa yozma:
    [{word}_EN]
    🔤 **Inglizcha**: [Inglizcha so'z]
    🇺🇿 **O'zbekcha**: [O'zbekcha so'z]
    🗣 **Transkripsiya**: [Xalqaro talaffuzi, masalan /wɜːrd/]
    📖 **Ta'rif (Def)**: [Inglizcha oson ta'rifi]
    💡 **Misol**: [Akademik va tushunarli sifatli inglizcha gap] - [O'zbekcha tarjimasi]
    🔗 **Sinonimlar**: [3-4 ta mos inglizcha sinonim]
    """

    try:
        response = await model.generate_content_async(prompt)
        ai_text = response.text.strip()
        
        # 1. Matnni qatorlarga ajratamiz
        lines = ai_text.split('\n')
        
        # 2. Ovoz fayli yaratish uchun sof inglizcha so'zni matn ichidan aqlli ushlab olamiz
        english_word_for_audio = "word"
        for line in lines:
            if "🔤" in line and "**Inglizcha**" in line:
                # "🔤 **Inglizcha**: Letter" kabi qatordan faqat "Letter" so'zini qirqib olamiz
                english_word_for_audio = line.split(":", 1)[1].strip().replace('*', '').replace('`', '')
                break
        
        # 3. Yordamchi birinchi qatorni (masalan [maktub_EN]) foydalanuvchiga ko'rsatmaslik uchun kesib tashlaymiz
        if lines[0].startswith("[") and lines[0].endswith("]"):
            display_text = '\n'.join(lines[1:]).strip()
        else:
            display_text = ai_text

        await wait_msg.edit_text(display_text, reply_markup=get_keyboard(english_word_for_audio))
    except Exception as e:
        await wait_msg.edit_text(f"Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.\n`{e}`")

# --- 7. ISHGA TUSHIRISH ---
async def main():
    async with app:
        print("✅ Super AI Bot muvaffaqiyatli ishga tushdi!")
        await idle()

if __name__ == "__main__":
    loop.run_until_complete(main())
