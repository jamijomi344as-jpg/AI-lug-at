import asyncio
import requests

# --- 1. PYROGRAM XATOSINI OLDINI OLISH ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from deep_translator import GoogleTranslator

# --- SOZLAMALAR (Bularni o'zingiznikiga almashtirish SHART!) ---
API_ID =  36053423               # O'zingiznikini qo'ying (faqat raqamlar)
API_HASH = "82f39002cfa480485590bf961e20bf55"    # O'zingiznikini qo'ying
BOT_TOKEN = "8798789058:AAGKA20LbcczGx4N0YrSLMhm2Wj1tci-V4E"  # O'zingiznikini qo'ying

app = Client("dictionary_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Foydalanuvchilarning qaysi tilda ekanligini saqlash uchun lug'at
user_modes = {}

# --- FUNKSIYALAR ---
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
                "synonyms": ", ".join(syns[:5]) if syns else "Mavjud emas"
            }
        return {"ok": False}
    except:
        return {"ok": False}

def get_keyboard(user_id):
    """Foydalanuvchi holatiga qarab tugma yaratish"""
    mode = user_modes.get(user_id, "en_uz")
    
    if mode == "en_uz":
        btn_text = "🔄 Inglizcha ➡️ O'zbekcha (O'zgartirish)"
    else:
        btn_text = "🔄 O'zbekcha ➡️ Inglizcha (O'zgartirish)"
        
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_text, callback_data="toggle_mode")],
        [InlineKeyboardButton("📚 Dasturchi bilan aloqa", url="https://t.me/durov")] # Buni o'zingizni username'ga o'zgartiring
    ])

# --- BOT BUYRUQLARI ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    user_modes[user_id] = "en_uz" # Standart holat
    
    await message.reply_text(
        "👋 **Salom! Men aqlli lug'at botiman.**\n\n"
        "Menga so'z yuboring. Tarjima yo'nalishini quyidagi tugma orqali o'zgartirishingiz mumkin:",
        reply_markup=get_keyboard(user_id)
    )

@app.on_callback_query(filters.regex("toggle_mode"))
async def toggle_mode(client, callback_query: CallbackQuery):
    """Tugma bosilganda tilni o'zgartirish"""
    user_id = callback_query.from_user.id
    current_mode = user_modes.get(user_id, "en_uz")
    
    # Tilni almashtirish
    new_mode = "uz_en" if current_mode == "en_uz" else "en_uz"
    user_modes[user_id] = new_mode
    
    text = "✅ Endi bot **O'zbekchadan Inglizchaga** tarjima qiladi." if new_mode == "uz_en" else "✅ Endi bot **Inglizchadan O'zbekchaga** tarjima qiladi."
    
    await callback_query.answer("Til o'zgartirildi!", show_alert=False)
    await callback_query.message.edit_text(
        f"{text}\n\nMenga so'z yuboring:", 
        reply_markup=get_keyboard(user_id)
    )

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
        # Tarjima qilish
        if mode == "en_uz":
            translator = GoogleTranslator(source='en', target='uz')
            uz_translation = translator.translate(word)
            en_word = word
            uz_word = uz_translation
        else:
            translator = GoogleTranslator(source='uz', target='en')
            en_translation = translator.translate(word)
            en_word = en_translation
            uz_word = word

        # Inglizcha so'zning ta'rifini olish
        details = get_details(en_word)

        # Matnni chiroyli qilib shakllantirish
        text = f"🔤 **Inglizcha**: `{en_word.capitalize()}`\n"
        text += f"🇺🇿 **O'zbekcha**: `{uz_word.capitalize()}`\n\n"
        
        if details["ok"]:
            text += f"🗣 **Transkripsiya**: `{details['phonetic']}`\n"
            text += f"📖 **Ta'rif (Def)**: {details['definition']}\n"
            text += f"💡 **Misol**: _{details['example']}_\n"
            text += f"🔗 **Sinonimlar**: {details['synonyms']}"
        else:
            if mode == "uz_en":
                text += "⚠️ _Inglizcha ta'rif topilmadi._"
        
        await wait_msg.edit_text(text, reply_markup=get_keyboard(user_id))
    except Exception as e:
        await wait_msg.edit_text(f"Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.\n`{e}`")

# --- ISHGA TUSHIRISH ---
async def main():
    async with app:
        print("✅ Bot muvaffaqiyatli ishga tushdi va xabarlarni kutyapti!")
        await idle()

if __name__ == "__main__":
    loop.run_until_complete(main())
