import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('publicado/vigia-obra-seguranca/.env'))
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
with open('publicado/vigia-obra-seguranca/person_with_helmet.png', 'rb') as f:
    b = f.read()

part = types.Part.from_bytes(data=b, mime_type='image/png')
prompt = "Observe com atencao a cabeca da pessoa nesta imagem. A pessoa esta usando capacete de seguranca? Responda em JSON: {\"tem_capacete\": bool, \"cor_capacete\": str, \"descricao\": str}"

res = client.models.generate_content(
    model='gemini-flash-lite-latest',
    contents=[part, prompt],
    config=types.GenerateContentConfig(response_mime_type='application/json')
)
print("gemini-flash-lite-latest result:")
print(res.text)

# Also test gemini-3.1-flash-lite
try:
    res2 = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=[part, prompt],
        config=types.GenerateContentConfig(response_mime_type='application/json')
    )
    print("gemini-3.1-flash-lite result:")
    print(res2.text)
except Exception as e:
    print("gemini-3.1-flash-lite error:", e)
