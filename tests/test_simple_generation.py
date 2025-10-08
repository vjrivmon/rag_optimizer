#!/usr/bin/env python3
"""Test simple de generación sin RAG ni evaluación"""

import requests
import time
import json

def test_generate(model_name):
    """Test simple de generación"""

    print(f"\n{'='*80}")
    print(f"Testing: {model_name}")
    print(f"{'='*80}")

    url = "https://ollama.gti-ia.upv.es:443/api/generate"

    payload = {
        'model': model_name,
        'prompt': 'Responde en una frase: ¿Qué es un desayuno?',
        'stream': False,
        'options': {
            'temperature': 0.3,
            'num_predict': 100
        }
    }

    print(f"⏱️  Iniciando request...")
    start = time.time()

    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            verify=False,
            timeout=300
        )

        elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()
            answer = result.get('response', '')
            print(f"✅ SUCCESS ({elapsed:.1f}s)")
            print(f"📝 Respuesta: {answer[:200]}")
            return True
        else:
            print(f"❌ HTTP {response.status_code} ({elapsed:.1f}s)")
            print(f"Error: {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"⏰ TIMEOUT ({elapsed:.1f}s)")
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ ERROR ({elapsed:.1f}s): {e}")
        return False

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')

    models = [
        "qwen3:32b",
        "deepseek-r1:latest",
        "gemma2:27b",
        "llama3.3:70b"
    ]

    for model in models:
        test_generate(model)
        time.sleep(2)  # Esperar entre requests
