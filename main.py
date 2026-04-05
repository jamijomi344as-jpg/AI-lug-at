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
        # Rasmni bazaga o'tkazish
        base64_image = base64.b64encode(image_data).decode('utf-8')

        prompt = """
        ACT AS AN OCR AND TRANSLATOR. 
        Extract English words and idioms from image. 
        Translate to Uzbek.
        RETURN ONLY JSON. NO CONVERSATION.
        Example: {"words": [{"en": "apple", "uz": "olma"}], "idioms": []}
        """
        
        response = client.chat.completions.create(
            model="meta-llama/llama-3.2-11b-vision-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        raw_content = response.choices[0].message.content or ""
        
        # JSONNI QIDIRISH (REGEX)
        # Bu qism matn ichidan faqat { ... } qismini qidirib topadi
        match = re.search(r'(\{.*\})', raw_content, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            # Ba'zan AI vergulni yoki qavsni xato qo'yadi, shuni tuzatishga urinish
            json_str = re.sub(r',\s*}', '}', json_str) 
            
            try:
                data = json.loads(json_str)
                return {
                    "words": data.get("words", []),
                    "idioms": data.get("idioms", [])
                }
            except:
                return {"error": "AI javobini o'qib bo'lmadi", "details": raw_content}
        else:
            return {"error": "AI matnni taniy olmadi", "details": raw_content}

    except Exception as e:
        return {"error": "Ulanishda xatolik", "details": str(e)}
