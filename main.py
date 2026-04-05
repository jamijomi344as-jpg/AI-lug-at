import os
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- 1. PYROGRAM MOTORINI ISHGA TUSHIRISH ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import google.generativeai as genai
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
GEMINI_API_KEY = "SHU_YERGA_GEMINI_KALITINGIZNI_QOYING" # <-- Kalitni kiritishni unutmang!

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Client("dictionary_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True) 
user_modes = {}


# --- 4. FUNKSIYALAR ---
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
        "👋 **Salom! Men Sun'iy Intellekt bilan ishlaydigan aqlli lug'at botiman.**\n\n"
        "Men so'zlarning shunchaki tarjimasini emas, balki aniq ma'nosini va akademik misollarini keltiraman. Menga so'z yuboring:",
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
    
    if len(word.split()) > 4: 
        await message.reply_text("Iltimos, qisqaroq so'z yoki ibora yuboring.")
        return
    
    wait_msg = await message.reply_text("🧠 Sun'iy intellekt o'ylamoqda...")
    
    yo_nalish = "Inglizchadan O'zbekchaga" if mode == "en_uz" else "O'zbekchadan Inglizchaga"
    
    prompt = f"""
    Sen professional ingliz-o'zbek lug'ati va til o'rganish bo'yicha ekspert bot rolidasan. 
    Foydalanuvchi quyidagi so'z/iborani yubordi: "{word}"
    Tarjima yo'nalishi: {yo_nalish}.

    Vazifang:
    1. So'zning aynan foydalanuvchi nazarda tutgan eng asosiy ma'nosini topish.
    2. Tarjimani oson, tabiiy, ammo akademik darajada (IELTS kabi imtihonlarga mos sifatli so'z boyligi bilan) ko'rsatish.
    
    Javobni AYNAN quyidagi formatda, ortiqcha gaplarsiz qaytar:
    🔤 **Inglizcha**: [So'zning inglizcha varianti]
    🇺🇿 **O'zbekcha**: [So'zning o'zbekcha tarjimasi]
    🗣 **Transkripsiya**: [Xalqaro transkripsiya, masalan /wɜːrd/]
    📖 **Ta'rif (Def)**: [Ingliz tilidagi oson va qisqa ta'rifi]
    💡 **Misol**: [IELTS darajasidagi, ammo tushunarli sifatli inglizcha gap] - [Shu gapning o'zbekcha tarjimasi]
    🔗 **Sinonimlar**: [3-4 ta eng aniq va mos inglizcha sinonimlar]
    """

    try:
        response = await model.generate_content_async(prompt)
        ai_text = response.text
        
        await wait_msg.edit_text(ai_text, reply_markup=get_keyboard(user_id))
    except Exception as e:
        await wait_msg.edit_text(f"Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.\n`{e}`")


# --- 6. ISHGA TUSHIRISH ---
async def main():
    async with app:
        print("✅ AI Bot muvaffaqiyatli ishga tushdi!")
        await idle()

if __name__ == "__main__":
    loop.run_until_complete(main())
