import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key encontrada: {api_key[:20]}..." if api_key else "No API key")

# Test simple
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Di 'ok'"}],
        max_tokens=5,
        timeout=10
    )
    print(f"✅ OpenAI responde: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {e}")
