from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import base64
import json
import traceback
import os
from openai import OpenAI

# Kalit Vercel sozlamalaridan xavfsiz olinadi (OpenRouter kalitingiz qolaveradi)
api_key = os.environ.get("OPENROUTER_API_KEY")

# OpenRouter tizimiga ulanish
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
        
        # OpenRouter orqali Amerikaning IP manzili bilan bepul Gemini'ga ulanamiz!
        response = client.chat.completions.create(
        model="google/gemini-1.5-flash:free",
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
        
        result_text = response.choices[0].message.content.strip()
        
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
