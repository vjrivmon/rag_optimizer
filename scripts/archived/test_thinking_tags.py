#!/usr/bin/env python3
"""
🧪 Test: ¿Qué modelos generan etiquetas <think>?

Prueba cada modelo de tu configuración para ver si genera
etiquetas de razonamiento.
"""

import requests
import json
import re

MODELS_TO_TEST = [
    {"name": "qwen3:32b", "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"},
    {"name": "deepseek-r1:latest", "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"},
    {"name": "gemma2:27b", "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"},
    {"name": "llama3.3:70b", "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"},
]

def test_model_for_thinking(model_name: str, endpoint: str) -> dict:
    """Prueba si un modelo genera etiquetas de razonamiento"""
    
    # Pregunta simple que invita a razonar
    prompt = """¿Cuánto es 15 × 23? Muestra tu razonamiento paso a paso."""
    
    print(f"\n{'='*60}")
    print(f"🧪 Probando: {model_name}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            endpoint,
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 300
                }
            },
            verify=False,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('response', '')
            
            # Buscar etiquetas
            has_think = bool(re.search(r'<think>', answer, re.IGNORECASE))
            has_thinking = bool(re.search(r'<thinking>', answer, re.IGNORECASE))
            has_reasoning = bool(re.search(r'<reasoning>', answer, re.IGNORECASE))
            
            # Mostrar respuesta
            print(f"\n📝 Respuesta ({len(answer)} chars):")
            print("-" * 60)
            print(answer[:500])
            if len(answer) > 500:
                print(f"... (truncado, {len(answer) - 500} chars más)")
            print("-" * 60)
            
            # Resultados
            print(f"\n🔍 Análisis de etiquetas:")
            print(f"   <think>:     {'✅ SÍ' if has_think else '❌ NO'}")
            print(f"   <thinking>:  {'✅ SÍ' if has_thinking else '❌ NO'}")
            print(f"   <reasoning>: {'✅ SÍ' if has_reasoning else '❌ NO'}")
            
            uses_tags = has_think or has_thinking or has_reasoning
            
            if uses_tags:
                print(f"\n⚠️  REQUIERE LIMPIEZA")
                
                # Mostrar versión limpia
                cleaned = answer
                for pattern in [r'<think>.*?</think>', r'<thinking>.*?</thinking>', r'<reasoning>.*?</reasoning>']:
                    cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
                cleaned = cleaned.strip()
                
                print(f"\n🧹 Después de limpiar ({len(cleaned)} chars):")
                print("-" * 60)
                print(cleaned[:300])
                print("-" * 60)
                print(f"   Reducción: -{len(answer) - len(cleaned)} caracteres ({(1 - len(cleaned)/len(answer))*100:.1f}%)")
            else:
                print(f"\n✅ NO requiere limpieza")
            
            return {
                'model': model_name,
                'success': True,
                'uses_thinking_tags': uses_tags,
                'answer_length': len(answer),
                'has_think': has_think,
                'has_thinking': has_thinking,
                'has_reasoning': has_reasoning
            }
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return {'model': model_name, 'success': False, 'error': f"HTTP {response.status_code}"}
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {'model': model_name, 'success': False, 'error': str(e)}


if __name__ == "__main__":
    print("🧪 TEST: Detección de etiquetas <think> en modelos")
    print("=" * 60)
    
    results = []
    
    for model_config in MODELS_TO_TEST:
        result = test_model_for_thinking(
            model_config['name'],
            model_config['endpoint']
        )
        results.append(result)
    
    # Resumen final
    print(f"\n\n{'='*60}")
    print("📊 RESUMEN FINAL")
    print(f"{'='*60}")
    
    print("\n🟢 Modelos que NO necesitan limpieza:")
    for r in results:
        if r['success'] and not r.get('uses_thinking_tags', False):
            print(f"   ✅ {r['model']}")
    
    print("\n🟡 Modelos que SÍ necesitan limpieza:")
    needs_cleaning = False
    for r in results:
        if r['success'] and r.get('uses_thinking_tags', False):
            print(f"   ⚠️  {r['model']}")
            tags = []
            if r.get('has_think'): tags.append('<think>')
            if r.get('has_thinking'): tags.append('<thinking>')
            if r.get('has_reasoning'): tags.append('<reasoning>')
            print(f"      Etiquetas detectadas: {', '.join(tags)}")
            needs_cleaning = True
    
    if not needs_cleaning:
        print("   (Ninguno)")
    
    print("\n🔴 Modelos con errores:")
    has_errors = False
    for r in results:
        if not r['success']:
            print(f"   ❌ {r['model']}: {r.get('error', 'Unknown error')}")
            has_errors = True
    
    if not has_errors:
        print("   (Ninguno)")
    
    # Recomendación
    print(f"\n{'='*60}")
    print("💡 RECOMENDACIÓN")
    print(f"{'='*60}")
    
    if needs_cleaning:
        print("⚠️  Algunos modelos generan etiquetas de razonamiento.")
        print("   DEBES integrar la función clean_thinking_tags()")
        print("   en tu benchmark para obtener métricas correctas.")
    else:
        print("✅ Ninguno de tus modelos usa etiquetas de razonamiento.")
        print("   La limpieza NO es necesaria (pero tampoco hace daño).")
    
    print("\n" + "="*60)