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

        # Tezroq javob olish uchun aniq va qisqa buyruq
        prompt = """
        Extract important English words and idioms from the image. 
        Provide Uzbek translations.
        OUTPUT STRICTLY VALID JSON ONLY. NO OTHER TEXT. FAST OUTPUT.
        Format:
        {"words": [{"en": "word", "uz": "tarjima"}], "idioms": [{"en": "idiom", "uz": "tarjima"}]}
        """
        
        response = client.chat.completions.create(
            model="meta-llama/llama-3.2-11b-vision-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content or ""
        
        start_idx = result_text.find('{')
        end_idx = result_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = result_text[start_idx:end_idx+1]
            json_str = re.sub(r'"\s*"uz"', '", "uz"', json_str)
            
            try:
                data = json.loads(json_str)
                clean_data = {
                    "words": data.get("words", []),
                    "idioms": data.get("idioms", [])
                }
                if "phrasalverbs" in data:
                    clean_data["idioms"].extend(data["phrasalverbs"])
                return clean_data
                
            except json.JSONDecodeError as e:
                return {"error": "JSON xatosi", "details": str(e) + f"\n\nJSON qismi: {json_str}"}
        else:
            return {"error": "JSON topilmadi", "details": result_text}

    except Exception as e:
        return {"error": "Serverda xato", "details": str(e)}
