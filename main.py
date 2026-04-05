from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from PIL import Image
import io
import json
import traceback
import os
from google import genai

# Sizning haqiqiy kalitingiz kodga kiritildi
api_key = "AIzaSyA_MDCoMuKHSepAqisoKBn6FJZ2Ef18UYQ"

client = genai.Client(api_key=api_key)

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home_page():
    # Vercel serverlarida fayl manzilini to'g'ri topish uchun
    base_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_dir, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload/")
async def process_image(file: UploadFile = File(...)):
    try:
        # Rasmni qabul qilish
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))

        # Gemini'ga to'g'ridan-to'g'ri rasmni va buyruqni beramiz
        prompt = """
        Look at this image. Extract all the important English vocabulary words, idioms, and phrasal verbs found in the text within the image.
        Provide their Uzbek translations.
        Return ONLY a valid JSON in this exact format, with no markdown formatting like ```json, no extra text:
        {
            "words": [{"en": "word", "uz": "tarjima"}],
            "idioms": [{"en": "idiom phrase", "uz": "tarjima"}]
        }
        """
        
        # Gemini 2.0 Flash ga rasmni o'zini yuborish
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[image, prompt],
        )
        
        # Javobni tozalash va JSON ga o'girish
        result_text = response.text.strip()
        
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        elif result_text.startswith("```"):
            result_text = result_text[3:]
            
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        data = json.loads(result_text.strip())
        return data

    except Exception as e:
        print("\n=== XATOLIK TAFSILOTI ===")
        traceback.print_exc()
        print("=========================\n")
        return {"error": "Serverda xatolik yuz berdi", "details": str(e)}
