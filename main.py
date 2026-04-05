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

        # AI ga juda qattiq buyruq beramiz
        prompt = """
        Look at this image. Extract all the important English vocabulary words and idioms.
        Provide their Uzbek translations.
        WARNING: YOU MUST OUTPUT EXACTLY AND ONLY A VALID JSON OBJECT. 
        NO EXPLANATORY TEXT. NO INTRODUCTIONS. DO NOT FORGET COMMAS BETWEEN ITEMS.
        Only use 'words' and 'idioms' keys.
        Format EXACTLY like this:
        {
            "words": [{"en": "word", "uz": "tarjima"}],
            "idioms": [{"en": "idiom", "uz": "tarjima"}]
        }
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
            temperature=0.1 # Xato qilmasligi uchun aniqlikni oshirdik
        )
        
        result_text = response.choices[0].message.content or ""
        
        # 1. Ortiqcha gap-so'zlarni kesib tashlab, faqat { va } orasidagi JSON ni olish
        start_idx = result_text.find('{')
        end_idx = result_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = result_text[start_idx:end_idx+1]
            
            # 2. Llama unutgan vergullarni avtomatik tuzatish (regex sehr-jodusi)
            json_str = re.sub(r'"\s*"uz"', '", "uz"', json_str)
            
            try:
                data = json.loads(json_str)
                
                # Agar u yana ahmoqlik qilib boshqa bo'lim qo'shsa, faqat keragini olamiz
                clean_data = {
                    "words": data.get("words", []),
                    "idioms": data.get("idioms", [])
                }
                
                # Agar phrasalverbs qo'shgan bo'lsa, uni idioms ga qo'shib yuboramiz
                if "phrasalverbs" in data:
                    clean_data["idioms"].extend(data["phrasalverbs"])
                    
                return clean_data
                
            except json.JSONDecodeError as e:
                return {"error": "AI javobi noto'g'ri chiqdi", "details": str(e) + f"\n\nJSON qismi: {json_str}"}
        else:
            return {"error": "AI javobida JSON topilmadi", "details": result_text}

    except Exception as e:
        print("\n=== XATOLIK TAFSILOTI ===")
        traceback.print_exc()
        print("=========================\n")
        return {"error": "Serverda ulanish xatosi", "details": str(e)}
