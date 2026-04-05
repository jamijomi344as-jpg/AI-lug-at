from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import base64
import json
import traceback
import os
import re
from openai import OpenAI

# API kalitni olish
api_key = os.environ.get("OPENROUTER_API_KEY")

# OpenRouter ulanishi (timeout qo'shildi)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    timeout=25.0
)

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home_page():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_dir, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload/")
async def process_image(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')

        prompt = """
        OCR AND TRANSLATE: Extract ALL English words and idioms from image. 
        Translate to Uzbek. Return ONLY JSON: {"words": [{"en": "...", "uz": "..."}], "idioms": []}
        """
        
        # Eng barqaror bepul model
        response = client.chat.completions.create(
            model="google/gemini-flash-1.5-8b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            temperature=0.1
        )
        
        raw_content = response.choices[0].message.content or ""
        match = re.search(r'(\{.*\})', raw_content, re.DOTALL)
        
        if match:
            return json.loads(match.group(1))
        
        return {"error": "AI tushunarsiz javob berdi", "details": raw_content}

    except Exception as e:
        # Xatoni Vercel Logs'ga chiqarish (Diagnostika uchun)
        print("--- XATOLIK TAFSILOTI ---")
        traceback.print_exc()
        print("-------------------------")
        return {
            "error": "Ulanishda xato yuz berdi", 
            "details": str(e),
            "type": str(type(e).__name__)
        }
