from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import base64
import json
import os
import re
from openai import OpenAI

api_key = os.environ.get("OPENROUTER_API_KEY")

# Timeoutni qo'shish ulanishni barqaror qiladi
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    timeout=20.0, 
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

        # Promptni yanada qisqartirdik (tezroq javob olish uchun)
        prompt = "Extract English words and idioms from image. Translate to Uzbek. Return ONLY JSON: {\"words\": [{\"en\": \"...\", \"uz\": \"...\"}], \"idioms\": []}"
        
        response = client.chat.completions.create(
            model="google/gemini-flash-1.5-8b", # 8b versiyasi tezroq javob beradi
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
        return {"error": "Matn topilmadi", "details": raw_content}

    except Exception as e:
        return {"error": "Ulanishda xato yuz berdi", "details": str(e)}
