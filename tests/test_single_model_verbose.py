#!/usr/bin/env python3
"""Test con logging detallado para diagnosticar timeouts"""

import requests
import time
import json
import sys

def test_model_verbose(model_name, timeout_seconds=300):
    """Test con output verbose cada 10 segundos"""

    print(f"\n{'='*80}")
    print(f"🧪 VERBOSE TEST: {model_name}")
    print(f"{'='*80}\n")

    url = "https://ollama.gti-ia.upv.es:443/api/generate"

    payload = {
        'model': model_name,
        'prompt': 'Responde en una frase corta: ¿Qué es un desayuno?',
        'stream': False,
        'options': {
            'temperature': 0.3,
            'num_predict': 50
        }
    }

    print(f"📤 Enviando request a servidor Ollama...")
    print(f"⏱️  Timeout configurado: {timeout_seconds}s")
    print(f"🔄 Esperando respuesta", end='', flush=True)

    start_time = time.time()
    last_dot = start_time

    try:
        # Crear sesión con timeout progresivo
        session = requests.Session()
        session.verify = False

        response = session.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=timeout_seconds,
            stream=False
        )

        elapsed = time.time() - start_time
        print(f"\n\n✅ RESPUESTA RECIBIDA ({elapsed:.1f}s)")

        if response.status_code == 200:
            result = response.json()
            answer = result.get('response', '')
            print(f"📝 Contenido: {answer[:200]}")
            print(f"✅ SUCCESS")
            return True
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Error: {response.text[:300]}")
            return False

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"\n\n⏰ TIMEOUT después de {elapsed:.1f}s")
        return False

    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start_time
        print(f"\n\n❌ CONNECTION ERROR ({elapsed:.1f}s)")
        print(f"Detalle: {str(e)[:200]}")
        return False

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n\n❌ ERROR ({elapsed:.1f}s)")
        print(f"Tipo: {type(e).__name__}")
        print(f"Detalle: {str(e)[:200]}")
        return False

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')

    model = sys.argv[1] if len(sys.argv) > 1 else "gemma2:27b"
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    success = test_model_verbose(model, timeout)
    sys.exit(0 if success else 1)
