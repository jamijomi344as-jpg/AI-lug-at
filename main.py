from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import base64
import json
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

        # Modelga qat'iy buyruq: so'zlarni lug'at shaklida qaytar (Lemmatization)
        prompt = """
        OCR AND ANALYZE: 
        1. Find English words, phrasal verbs, and idioms. 
        2. Convert verbs to base form (e.g., 'running' -> 'run').
        3. Translate to Uzbek. 
        4. Return ONLY JSON: {"words": [{"en": "run", "uz": "yugurmoq"}], "idioms": []}
        """
        
        response = client.chat.completions.create(
        meta-llama/llama-3.2-11b-vision-instruct:free
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            temperature=0.1
        )
        
        raw_content = response.choices[0].message.content or ""
        match = re.search(r'(\{.*\})', raw_content, re.DOTALL)
        
        if match:
            return json.loads(match.group(1))
        return {"error": "Matn topilmadi"}

    except Exception as e:
        return {"error": "Server xatosi", "details": str(e)}
