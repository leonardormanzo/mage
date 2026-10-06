import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('publicado/vigia-obra-seguranca/.env'))
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
with open('publicado/vigia-obra-seguranca/actual_user_with_blue_helmet.png', 'rb') as f:
    b = f.read()

part = types.Part.from_bytes(data=b, mime_type='image/png')
prompt = "Inspecione a pessoa na imagem. Ela esta usando capacete de seguranca de obra? Responda em JSON: {\"tem_capacete\": bool, \"cor_capacete\": str, \"tem_oculos\": bool, \"descricao\": str}"

http_opts = types.HttpOptions(timeout=10000, retry_options=types.HttpRetryOptions(attempts=1))
for m in ['gemini-flash-lite-latest', 'gemini-3.1-flash-lite', 'gemini-3.5-flash-lite']:
    try:
        res = client.models.generate_content(
            model=m,
            contents=[part, prompt],
            config=types.GenerateContentConfig(response_mime_type='application/json', http_options=http_opts)
        )
        print(f"Model {m}:")
        print(res.text)
        break
    except Exception as e:
        print(f"Model {m} failed:", e)
