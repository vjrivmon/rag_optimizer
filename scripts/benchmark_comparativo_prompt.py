#!/usr/bin/env python3
"""
Benchmark COMPARATIVO - 20 preguntas críticas
Valida mejora del nuevo prompt
"""

import sys
sys.path.insert(0, '.')

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
import time
import json

print("="*80)
print("🧪 BENCHMARK COMPARATIVO - NUEVO PROMPT")
print("="*80)
print()

# 20 preguntas críticas que cubren todos los aspectos
preguntas_criticas = [
    # BÁSICAS (5)
    "¿Qué es DNI?",
    "¿Cuál es la filosofía de DNI?",
    "¿Cómo puedo unirme?",
    "¿Hay límite de edad?",
    "¿Es gratis?",
    
    # PROYECTOS (5)
    "¿Qué proyectos tenéis?",
    "desayunos solidarios",
    "horario abuelitos",
    "¿Dónde es el refuerzo escolar?",
    "ayuda DANA",
    
    # CONTACTO (3)
    "whatsapp",
    "instagram",
    "¿Cómo os contacto?",
    
    # EDGE CASES (4)
    "¿Qué tiempo hará mañana?",  # Fuera de scope
    "cómo me apunto",  # Typo/informal
    "HOLA",  # Mayúsculas/saludo
    "gracias",  # Agradecimiento
    
    # COMPLEJAS (3)
    "¿Qué hace DNI para ayudar a la comunidad?",
    "¿Puedo participar en varios proyectos?",
    "¿Qué necesito para ser voluntario?",
]

print(f"📋 {len(preguntas_criticas)} preguntas críticas seleccionadas\n")

# Inicializar
print("🔧 Inicializando sistema CON PROMPT MEJORADO...")
model = LLMWrapper("gemma2:27b", "https://ollama.gti-ia.upv.es:443/api/generate")
rag = EnhancedRAGEngineNew('data/vectorstore/chroma_db', model)
print("✅ Sistema listo\n")

resultados = []
start_total = time.time()

print(f"{'='*80}")
print(f"⏳ PROCESANDO {len(preguntas_criticas)} PREGUNTAS...")
print(f"{'='*80}\n")

for i, pregunta in enumerate(preguntas_criticas, 1):
    print(f"   [{i}/{len(preguntas_criticas)}] {pregunta[:50]}...")
    
    start = time.time()
    
    try:
        result = rag.process_query_with_validation(pregunta, i)
        elapsed = time.time() - start
        
        answer = result.get('answer', '')
        confidence = result.get('validation').confidence if 'validation' in result else 0.0
        contexts = result.get('contexts', [])
        
        # Evaluación de calidad
        tiene_contenido = len(answer) > 50
        tiene_alta_conf = confidence > 0.7
        es_util = tiene_contenido and tiene_alta_conf
        
        # Detectar si es respuesta de redirección apropiada
        es_redireccion = 'whatsapp' in answer.lower() or 'instagram' in answer.lower() or 'contacto' in answer.lower()
        
        # Clasificar calidad
        if pregunta in ["¿Qué tiempo hará mañana?"]:  # Fuera de scope
            calidad = es_redireccion and "dni" in answer.lower()
        elif pregunta in ["HOLA", "gracias"]:  # Sociales
            calidad = len(answer) > 10  # Cualquier respuesta cordial
        else:
            calidad = es_util
        
        resultado = {
            'id': i,
            'pregunta': pregunta,
            'respuesta': answer,
            'confidence': confidence,
            'tiempo': elapsed,
            'longitud': len(answer),
            'num_chunks': len(contexts),
            'calidad': calidad,
            'es_util': es_util
        }
        
        resultados.append(resultado)
        
        # Mostrar preview
        status = "✅" if calidad else "❌"
        print(f"      {status} Conf: {confidence:.2f} | {len(answer)} chars | {elapsed:.1f}s")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        resultados.append({
            'id': i,
            'pregunta': pregunta,
            'respuesta': '',
            'confidence': 0.0,
            'tiempo': time.time() - start,
            'longitud': 0,
            'num_chunks': 0,
            'calidad': False,
            'es_util': False,
            'error': str(e)
        })

total_time = time.time() - start_total

print(f"\n✅ Completado en {total_time:.1f}s\n")

# ANÁLISIS
print("="*80)
print("📊 RESULTADOS CON NUEVO PROMPT")
print("="*80)
print()

total = len(resultados)
respuestas_calidad = sum(1 for r in resultados if r['calidad'])
respuestas_utiles = sum(1 for r in resultados if r['es_util'])

avg_confidence = sum(r['confidence'] for r in resultados) / total
confidence_std = (sum((r['confidence'] - avg_confidence)**2 for r in resultados) / total) ** 0.5

avg_time = sum(r['tiempo'] for r in resultados) / total
avg_length = sum(r['longitud'] for r in resultados) / total

print("📈 MÉTRICAS GLOBALES:")
print(f"   • Respuestas de calidad: {respuestas_calidad}/{total} ({respuestas_calidad/total*100:.1f}%)")
print(f"   • Respuestas útiles: {respuestas_utiles}/{total} ({respuestas_utiles/total*100:.1f}%)")
print(f"   • Confidence: μ={avg_confidence:.3f}, σ={confidence_std:.3f}")
print(f"   • Tiempo promedio: {avg_time:.2f}s")
print(f"   • Longitud promedio: {avg_length:.0f} chars")
print()

# Comparación con benchmark anterior
print("📊 COMPARACIÓN CON BENCHMARK ANTERIOR:")
print(f"{'Métrica':<25} {'Anterior':<15} {'Nuevo':<15} {'Mejora':<15}")
print("-"*80)
print(f"{'Calidad':<25} {'94.0%':<15} {f'{respuestas_calidad/total*100:.1f}%':<15} {f'{(respuestas_calidad/total*100) - 94.0:+.1f}%':<15}")
print(f"{'Confidence promedio':<25} {'0.916':<15} {f'{avg_confidence:.3f}':<15} {f'{avg_confidence - 0.916:+.3f}':<15}")
print(f"{'Confidence desv.std':<25} {'~0.000':<15} {f'{confidence_std:.3f}':<15} {'Nuevo!':<15}")
print(f"{'Tiempo promedio':<25} {'3.35s':<15} {f'{avg_time:.2f}s':<15} {f'{avg_time - 3.35:+.2f}s':<15}")
print()

# Ejemplos representativos
print("✅ EJEMPLOS DE RESPUESTAS (primeras 3 buenas):")
print("-"*80)
buenas = [r for r in resultados if r['calidad']][:3]
for r in buenas:
    print(f"\nPregunta: {r['pregunta']}")
    print(f"Respuesta ({r['longitud']} chars, conf={r['confidence']:.2f}):")
    print(f"{r['respuesta'][:200]}...")

print()

problematicas = [r for r in resultados if not r['calidad']]
if problematicas:
    print("❌ EJEMPLOS DE RESPUESTAS PROBLEMÁTICAS:")
    print("-"*80)
    for r in problematicas[:3]:
        print(f"\nPregunta: {r['pregunta']}")
        print(f"Respuesta ({r['longitud']} chars, conf={r['confidence']:.2f}):")
        print(f"{r['respuesta'][:200]}...")

print()

# Guardar resultados
output_file = f'results/benchmark_comparativo_prompt_{int(time.time())}.json'
import os
os.makedirs('results', exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'total_preguntas': total,
        'metricas': {
            'calidad': f"{respuestas_calidad}/{total}",
            'porcentaje_calidad': f"{respuestas_calidad/total*100:.1f}%",
            'avg_confidence': avg_confidence,
            'std_confidence': confidence_std,
            'avg_tiempo': avg_time
        },
        'mejoras': {
            'calidad': f"{(respuestas_calidad/total*100) - 94.0:+.1f}%",
            'confidence': f"{avg_confidence - 0.916:+.3f}",
            'confidence_std': "NUEVO - antes era fijo en 0.95"
        },
        'resultados': resultados
    }, f, indent=2, ensure_ascii=False)

print(f"💾 Resultados guardados en: {output_file}\n")

# VEREDICTO
print("="*80)
if respuestas_calidad >= 19:  # 95%+
    print("🎉 ✅ PROMPT MEJORADO EXITOSO")
    print(f"   {respuestas_calidad}/{total} respuestas de calidad ({respuestas_calidad/total*100:.1f}%)")
    print(f"   Confidence más variable (σ={confidence_std:.3f}) - DINÁMICO ✅")
elif respuestas_calidad >= 18:  # 90%+
    print("⚠️  PROMPT MEJORADO - NECESITA AJUSTES MENORES")
    print(f"   {respuestas_calidad}/{total} respuestas de calidad - Casi perfecto")
else:
    print("❌ PROMPT NECESITA MÁS TRABAJO")
    print(f"   Solo {respuestas_calidad}/{total} respuestas de calidad")
print("="*80)


