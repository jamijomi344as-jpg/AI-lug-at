from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import base64
import json
import traceback
import os
from openai import OpenAI

# Kalit Vercel sozlamalaridan xavfsiz olinadi (OPENROUTER_API_KEY)
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

        prompt = """
        Look at this image. Extract all the important English vocabulary words, idioms, and phrasal verbs found in the text within the image.
        Provide their Uzbek translations.
        Return ONLY a valid JSON in this exact format, with no markdown formatting like ```json, no extra text:
        {
            "words": [{"en": "word", "uz": "tarjima"}],
            "idioms": [{"en": "idiom phrase", "uz": "tarjima"}]
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
            ]
        )
        
        # AI dan kelgan asl javobni ajratib olish
        result_text = response.choices[0].message.content or ""
        result_text = result_text.strip()
        
        # Keraksiz belgilarni tozalash
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        elif result_text.startswith("```"):
            result_text = result_text[3:]
            
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        result_text = result_text.strip()
        
        # MANA SHU YERDA XATONI TUTIB OLAMIZ:
        try:
            data = json.loads(result_text)
            return data
        except json.JSONDecodeError:
            # Agar JSON bo'lmasa, AI nima yozganini to'g'ridan-to'g'ri ekranga chiqaramiz
            return {
                "error": "AI biz kutgan JSON formatida javob bermadi", 
                "details": f"AI aslida shunday deb yozdi: \n\n{result_text}"
            }

    except Exception as e:
        print("\n=== XATOLIK TAFSILOTI ===")
        traceback.print_exc()
        print("=========================\n")
        return {"error": "Serverda ulanish xatosi", "details": str(e)}
