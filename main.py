import os
import threading
import asyncio
import requests
import uuid 
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

# --- 3. SOZLAMALAR VA BAZALAR ---
API_ID = 36053423
API_HASH = "82f39002cfa480485590bf961e20bf55"
BOT_TOKEN = "8798789058:AAGKA20LbcczGx4N0YrSLMhm2Wj1tci-V4E"

app = Client("dictionary_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True) 

# Xotira uchun lug'atlar (Vaqtinchalik ma'lumotlar bazasi)
AUDIO_CACHE = {}  # Ovoz va Saqlash uchun so'zlarni ushlab turadi
USER_LANGS = {}   # Foydalanuvchi qaysi tilni tanlagani (UZ-EN yoki EN-UZ)
USER_VOCAB = {}   # Foydalanuvchining shaxsiy zametkasi (Saqlagan so'zlari)

# --- 4. TUGMALAR (YANGILANGAN) ---
def get_keyboard(user_id, audio_id=None):
    buttons = []
    
    # 1-qator: Ovoz va Saqlash (Faqat so'z qidirilganda chiqadi)
    row1 = []
    if audio_id:
        row1.append(InlineKeyboardButton("🔊 O'qilishi", callback_data=f"audio_{audio_id}"))
        row1.append(InlineKeyboardButton("💾 Saqlash", callback_data=f"save_{audio_id}"))
    if row1:
        buttons.append(row1)
        
    # 2-qator: Tilni almashtirish va Zametka
    current_lang = USER_LANGS.get(user_id, "uz-en")
    lang_text = "🇺🇿 UZ ➡️ 🇬🇧 EN" if current_lang == "uz-en" else "🇬🇧 EN ➡️ 🇺🇿 UZ"
    
    buttons.append([
        InlineKeyboardButton(f"🔄 {lang_text}", callback_data="lang"),
        InlineKeyboardButton("📝 Lug'atim", callback_data="vocab")
    ])
    
    # 3-qator: Dasturchi bilan aloqa
    buttons.append([InlineKeyboardButton("📚 Dasturchi bilan aloqa", url="https://t.me/durov")])
    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    await message.reply_text(
        "👋 **Salom! Men sizning Shaxsiy Lug'at botingizman.**\n\n"
        "Menga xohlagan so'z yoki gaplarni (15 ta so'zgacha) yuboring. O'zingizga yoqqan so'zlarni xotiraga saqlab borishingiz mumkin!",
        reply_markup=get_keyboard(user_id) # Start bosganda ham pastki tugmalar chiqadi
    )

# --- 5. BARCHA TUGMALAR UCHUN YAGONA BOSHQARUV ---
@app.on_callback_query()
async def handle_callbacks(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    
    # 1. OVOZ TUGMASI
    if data.startswith("audio_"):
        audio_id = data.split("_", 1)[1]
        word_data = AUDIO_CACHE.get(audio_id)
        
        if not word_data:
            return await query.answer("⚠️ Bu xabar eskirgan, so'zni qaytadan yuboring.", show_alert=True)
            
        await query.answer("Ovoz tayyorlanmoqda... 🔊")
        try:
            tts = gTTS(text=word_data["en"], lang='en', slow=False)
            filename = f"{audio_id}.mp3"
            tts.save(filename)
            await client.send_voice(query.message.chat.id, voice=filename)
            os.remove(filename)
        except Exception as e:
            await query.message.reply_text("⚠️ Ovozni yasashda xatolik yuz berdi.")
            
    # 2. SAQLASH TUGMASI (ZAMETKA)
    elif data.startswith("save_"):
        audio_id = data.split("_", 1)[1]
        word_data = AUDIO_CACHE.get(audio_id)
        
        if not word_data:
            return await query.answer("⚠️ Bu xabar eskirgan.", show_alert=True)
            
        if user_id not in USER_VOCAB:
            USER_VOCAB[user_id] = []
            
        # Saqlanadigan matn formati
        entry = f"🇬🇧 {word_data['en'].capitalize()} - 🇺🇿 {word_data['uz'].capitalize()}"
        
        if entry not in USER_VOCAB[user_id]:
            USER_VOCAB[user_id].append(entry)
            await query.answer("✅ So'z lug'atingizga muvaffaqiyatli saqlandi!", show_alert=True)
        else:
            await query.answer("ℹ️ Bu so'z allaqachon lug'atingizda bor.", show_alert=True)
            
    # 3. TILNI ALMASHTIRISH TUGMASI
    elif data == "lang":
        current = USER_LANGS.get(user_id, "uz-en")
        new_lang = "en-uz" if current == "uz-en" else "uz-en"
        USER_LANGS[user_id] = new_lang
        
        await query.answer(f"Til o'zgartirildi!", show_alert=False)
        
        # Tugma yozuvi o'zgarishi uchun ekranni yangilaymiz
        audio_id = None
        for row in query.message.reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data and btn.callback_data.startswith("audio_"):
                    audio_id = btn.callback_data.split("_", 1)[1]
                    break
        await query.message.edit_reply_markup(get_keyboard(user_id, audio_id))

    # 4. LUG'ATIM (SAQLANGAN SO'ZLARNI KO'RISH)
    elif data == "vocab":
        vocab = USER_VOCAB.get(user_id, [])
        if not vocab:
            return await query.answer("📭 Lug'atingiz hozircha bo'sh. Qidirgan so'zlaringizni '💾 Saqlash' tugmasi orqali yig'ib boring.", show_alert=True)
        
        text = "📝 **Sizning shaxsiy lug'atingiz:**\n\n"
        for i, word in enumerate(vocab, 1):
            text += f"{i}. {word}\n"
            
        await client.send_message(user_id, text)
        await query.answer()

# --- 6. ASOSIY LUG'AT FUNKSIYASI ---
def get_dictionary_info(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200: return None
        data = res.json()[0]
        
        phonetic = data.get("phonetic", "")
        if not phonetic:
            for phon in data.get("phonetics", []):
                if "text" in phon and phon["text"]:
                    phonetic = phon["text"]
                    break
                    
        meanings = data.get("meanings", [])
        if not meanings: return None
            
        definition, example, synonyms = "", "", []
        for meaning in meanings:
            for def_dict in meaning.get("definitions", []):
                if not definition: definition = def_dict.get("definition", "")
                if not example and "example" in def_dict: example = def_dict.get("example", "")
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
    user_id = message.from_user.id
    
    if len(text.split()) > 15: 
        await message.reply_text("⚠️ Iltimos, 15 ta so'zdan kamroq matn yuboring.")
        return 
    
    wait_msg = await message.reply_text("🔍 Qidirilmoqda...")
    
    try:
        # Foydalanuvchi tanlagan til yo'nalishiga qarab tarjima qilamiz
        current_lang = USER_LANGS.get(user_id, "uz-en")
        
        if current_lang == "uz-en":
            english_word = await asyncio.to_thread(GoogleTranslator(source='auto', target='en').translate, text)
            english_word = english_word.lower()
            uzbek_word = await asyncio.to_thread(GoogleTranslator(source='en', target='uz').translate, english_word)
            uzbek_word = uzbek_word.lower()
        else: # EN-UZ bo'lsa
            uzbek_word = await asyncio.to_thread(GoogleTranslator(source='auto', target='uz').translate, text)
            uzbek_word = uzbek_word.lower()
            english_word = await asyncio.to_thread(GoogleTranslator(source='uz', target='en').translate, uzbek_word)
            english_word = english_word.lower()
        
        dict_info = None
        if len(english_word.split()) == 1:
            dict_info = await asyncio.to_thread(get_dictionary_info, english_word)
        
        # Audio va Saqlash tugmalari ishlashi uchun so'zlarni xotiraga olamiz
        audio_id = str(uuid.uuid4())[:8]
        AUDIO_CACHE[audio_id] = {"en": english_word, "uz": uzbek_word}
        
        response_text = f"🔤 **Inglizcha**: `{english_word.capitalize()}`\n"
        response_text += f"🇺🇿 **O'zbekcha**: `{uzbek_word.capitalize()}`\n\n"
        
        if dict_info:
            if dict_info['phonetic']: 
                response_text += f"🗣 **Transkripsiya**: `{dict_info['phonetic']}`\n"
            response_text += f"📖 **Ta'rif**: {dict_info['definition']}\n"
            
            if dict_info['example']: 
                uz_example = await asyncio.to_thread(GoogleTranslator(source='en', target='uz').translate, dict_info['example'])
                response_text += f"💡 **Misol**: {dict_info['example']} - _{uz_example}_\n"
                
            response_text += f"🔗 **Sinonimlar**: {dict_info['synonyms']}"
        else:
            if len(english_word.split()) > 1:
                response_text += "💡 _Bu gap yoki ibora bo'lgani uchun, faqat tarjimasi va audiosi keltirildi._"
            else:
                response_text += "⚠️ _Batafsil inglizcha ta'rif va misollar topilmadi._"

        await wait_msg.edit_text(response_text, reply_markup=get_keyboard(user_id, audio_id))
        
    except Exception as e:
        await wait_msg.edit_text("⚠️ Tarjima qilishda xatolik yuz berdi. Internet yoki baza uzilib qolgan bo'lishi mumkin.")

# --- 7. ISHGA TUSHIRISH ---
async def main():
    async with app:
        print("✅ Zametkali Lug'at Bot (Mukammal versiya) ishga tushdi!")
        await idle()

if __name__ == "__main__":
    loop.run_until_complete(main())
