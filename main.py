from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import base64
import json
import traceback
import os
from groq import Groq

# Kalit xavfsiz tarzda Vercel sozlamalaridan olinadi
api_key = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=api_key)

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
        
        chat_completion = client.chat.completions.create(
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
            # MANA SHU QATOR YANGILANDI: Rasmiy va barqaror model nomi
            model="llama-3.2-11b-vision-instruct",
        )
        
        result_text = chat_completion.choices[0].message.content.strip()
        
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
