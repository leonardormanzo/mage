import os
import sys
sys.path.insert(0, 'publicado/vigia-obra-seguranca')
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('publicado/vigia-obra-seguranca/.env'))
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

with open('publicado/vigia-obra-seguranca/crop_cand1.png', 'rb') as f:
    img_bytes = f.read()

part = types.Part.from_bytes(data=img_bytes, mime_type='image/png')
prompt = "Inspecione a pessoa na imagem. Responda em JSON: {\"tem_capacete\": bool, \"cor_capacete\": str, \"tem_oculos\": bool, \"descricao\": str}"

try:
    res = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=[part, prompt],
        config=types.GenerateContentConfig(response_mime_type='application/json')
    )
    print(res.text)
except Exception as e:
    print('Gemini error:', e)
