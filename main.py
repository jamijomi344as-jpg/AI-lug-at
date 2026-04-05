from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import base64
import json
import traceback
import os
import re
from openai import OpenAI

api_key = os.environ.get("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
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

        # Modelni Gemini 1.5 Flash ga o'zgartirdik (U rasmni zo'r ko'radi)
        # Promptni ham aniqlashtirdik
        prompt = """
        OCR AND TRANSLATE TASK:
        1. Scan the image and find ALL English words, phrases, and idioms.
        2. Translate them accurately into Uzbek.
        3. Do NOT add any words that are not in the image (like 'apple').
        4. Return ONLY a JSON object. No conversation.
        Format: {"words": [{"en": "text from image", "uz": "tarjimasi"}], "idioms": []}
        """
        
        response = client.chat.completions.create(
            model="google/gemini-flash-1.5-8b", # Yoki "google/gemini-flash-1.5"
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
        
        # JSONni ajratib olish uchun regex
        match = re.search(r'(\{.*\})', raw_content, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            try:
                data = json.loads(json_str)
                # Agar AI barcha so'zlarni bitta massivga tiqib yuborsa ham ishlaydi
                return {
                    "words": data.get("words", []),
                    "idioms": data.get("idioms", [])
                }
            except:
                return {"error": "AI javobi formatga tushmadi", "details": raw_content}
        else:
            return {"error": "Rasmda matn topilmadi", "details": raw_content}

    except Exception as e:
        return {"error": "Ulanish xatosi", "details": str(e)}
