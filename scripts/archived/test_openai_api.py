#!/usr/bin/env python3
"""
🧪 Test de OpenAI API - Verificación rápida

Verifica que:
1. La API key está configurada
2. Puedes hacer llamadas a OpenAI
3. Las métricas RAGAs se generan correctamente
4. Los tiempos son realistas
"""

import os
import time
import json
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

print("🧪 Test de OpenAI API para RAGAs")
print("=" * 60)

# 1. Verificar API key
api_key = os.environ.get('OPENAI_API_KEY')

if not api_key:
    print("❌ No se encuentra OPENAI_API_KEY")
    print("   Verifica tu archivo .env")
    exit(1)

print(f"✅ API Key encontrada: {api_key[:8]}...{api_key[-4:]}")

# 2. Importar OpenAI
try:
    from openai import OpenAI
    print("✅ Librería OpenAI importada correctamente")
except ImportError:
    print("❌ No se puede importar OpenAI")
    print("   Ejecuta: pip install openai")
    exit(1)

# 3. Crear cliente
try:
    client = OpenAI(api_key=api_key)
    print("✅ Cliente OpenAI creado")
except Exception as e:
    print(f"❌ Error al crear cliente: {e}")
    exit(1)

# 4. Hacer llamada de prueba
print("\n📡 Haciendo llamada de prueba a OpenAI...")
print("   Modelo: gpt-4o-mini")

test_prompt = """Eres un evaluador experto de sistemas RAG.
Evalúa la respuesta según estas 6 métricas (escala 0-1):

1. faithfulness: ¿La respuesta es fiel al contexto? (no alucina)
2. answer_relevancy: ¿La respuesta es relevante a la pregunta?
3. context_precision: ¿El contexto recuperado es preciso?
4. context_recall: ¿Se recuperó todo el contexto necesario?
5. answer_correctness: ¿La respuesta es correcta vs ground truth?
6. answer_similarity: Similitud semántica con ground truth

Responde SOLO con JSON:
{"faithfulness": 0.X, "answer_relevancy": 0.X, ...}"""

test_question = """Pregunta: ¿Qué es Python?

Contexto recuperado:
Python es un lenguaje de programación interpretado de alto nivel.

Respuesta del modelo:
Python es un lenguaje de programación muy utilizado para desarrollo web, análisis de datos y machine learning.

Evalúa la respuesta."""

try:
    start_time = time.time()
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": test_prompt},
            {"role": "user", "content": test_question}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    elapsed = time.time() - start_time
    
    print(f"✅ Respuesta recibida en {elapsed:.2f} segundos")
    
    # Analizar respuesta
    response_text = completion.choices[0].message.content
    print(f"\n📊 Respuesta de OpenAI:")
    print(response_text)
    
    # Parsear JSON
    metrics = json.loads(response_text)
    print(f"\n✅ JSON parseado correctamente:")
    for metric, value in metrics.items():
        print(f"   {metric}: {value:.3f}")
    
    # Info de uso
    print(f"\n💰 Información de uso:")
    print(f"   Tokens prompt: {completion.usage.prompt_tokens}")
    print(f"   Tokens completion: {completion.usage.completion_tokens}")
    print(f"   Tokens totales: {completion.usage.total_tokens}")
    print(f"   Costo aproximado: ${completion.usage.total_tokens * 0.00000015:.6f}")
    
    # Verificar tiempo
    print(f"\n⏱️  Análisis de tiempo:")
    if elapsed < 1.0:
        print(f"   ⚠️  WARNING: Muy rápido ({elapsed:.2f}s)")
        print(f"      Puede ser que esté usando caché")
    elif elapsed < 3.0:
        print(f"   ✅ Tiempo normal para gpt-4o-mini ({elapsed:.2f}s)")
    else:
        print(f"   ℹ️  Tiempo alto ({elapsed:.2f}s) - puede ser red lenta")
    
    print(f"\n" + "=" * 60)
    print("🎉 TEST COMPLETADO EXITOSAMENTE")
    print("=" * 60)
    print("\n✅ Tu configuración está lista para ejecutar el benchmark")
    print("   Ejecuta: python benchmark_v2.py --max-questions 3")
    
except Exception as e:
    print(f"\n❌ ERROR en llamada a OpenAI:")
    print(f"   {str(e)}")
    
    if "authentication" in str(e).lower() or "api key" in str(e).lower():
        print("\n💡 Solución:")
        print("   1. Verifica que tu API key sea correcta")
        print("   2. Ve a: https://platform.openai.com/api-keys")
        print("   3. Crea una nueva API key si es necesario")
    
    elif "quota" in str(e).lower() or "billing" in str(e).lower():
        print("\n💡 Solución:")
        print("   1. Verifica tu saldo en OpenAI")
        print("   2. Ve a: https://platform.openai.com/account/billing")
        print("   3. Añade créditos si es necesario")
    
    exit(1)