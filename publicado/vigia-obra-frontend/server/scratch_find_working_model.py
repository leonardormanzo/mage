import os
import sys
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('publicado/vigia-obra-seguranca/.env'))
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
models = [
    'gemini-2.5-flash-lite',
    'gemini-flash-lite-latest',
    'gemini-3.1-flash-lite',
    'gemini-3.5-flash-lite',
    'gemini-flash-latest',
    'gemini-3.5-flash',
    'gemini-3.6-flash',
    'gemini-3.8-flash'
]

with open('publicado/vigia-obra-seguranca/crop_cand1.png', 'rb') as f:
    b = f.read()
part = types.Part.from_bytes(data=b, mime_type='image/png')
prompt = 'Inspecione a pessoa. Responda em JSON: {"tem_capacete": true, "cor_capacete": "azul"}'

for m in models:
    try:
        http_opts = types.HttpOptions(timeout=10000, retry_options=types.HttpRetryOptions(attempts=1))
        res = client.models.generate_content(
            model=m,
            contents=[part, prompt],
            config=types.GenerateContentConfig(response_mime_type='application/json', http_options=http_opts)
        )
        print(f'SUCCESS with {m}:')
        print(res.text)
        break
    except Exception as e:
        err = str(e)
        if '503' in err:
            print(f'{m}: 503 Overload')
        elif '429' in err:
            print(f'{m}: 429 Quota')
        elif '404' in err:
            print(f'{m}: 404 Deprecated')
        else:
            print(f'{m}: {err[:80]}')
