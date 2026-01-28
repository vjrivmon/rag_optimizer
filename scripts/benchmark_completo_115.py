#!/usr/bin/env python3
"""
Benchmark COMPLETO con 115 preguntas de test_queries.txt
Analiza TODOS los resultados y detecta patrones de fallo
"""

import sys
sys.path.insert(0, '.')

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
import time
import json

print("="*80)
print("🧪 BENCHMARK COMPLETO - 115 PREGUNTAS")
print("="*80)
print()

# Leer preguntas de test_queries.txt
print("📖 Cargando preguntas...")
with open('data/test_queries.txt', 'r', encoding='utf-8') as f:
    preguntas = [line.strip() for line in f if line.strip()]

print(f"✅ {len(preguntas)} preguntas cargadas\n")

# Inicializar
print("🔧 Inicializando sistema...")
model = LLMWrapper("gemma2:27b", "https://ollama.gti-ia.upv.es:443/api/generate")
rag = EnhancedRAGEngineNew('data/vectorstore/chroma_db', model)
print("✅ Sistema listo\n")

resultados = []
start_total = time.time()

# Categorías comunes para análisis
categorias = {
    'desayunos': ['desayuno', 'cena solidaria', 'bocadillo', 'porta de la mar'],
    'coles': ['refuerzo escolar', 'coles', 'niños', 'ceip'],
    'resis': ['abuelitos', 'ancianos', 'residencia', 'acollida'],
    'general': ['dni', 'voluntario', 'apuntar', 'requisito'],
    'dana': ['dana', 'horta sud', 'rehabilitar'],
}

def detectar_categoria(pregunta):
    pregunta_lower = pregunta.lower()
    for cat, keywords in categorias.items():
        if any(kw in pregunta_lower for kw in keywords):
            return cat
    return 'otros'

print(f"{'='*80}")
print(f"⏳ PROCESANDO {len(preguntas)} PREGUNTAS...")
print(f"{'='*80}\n")

for i, pregunta in enumerate(preguntas, 1):
    if i % 10 == 0:
        print(f"   Progreso: {i}/{len(preguntas)} ({i/len(preguntas)*100:.0f}%)")
    
    start = time.time()
    
    try:
        result = rag.process_query_with_validation(pregunta, i)
        elapsed = time.time() - start
        
        answer = result.get('answer', '')
        confidence = result.get('validation').confidence if 'validation' in result else 0.0
        contexts = result.get('contexts', [])
        
        categoria = detectar_categoria(pregunta)
        
        # Análisis de calidad
        tiene_contenido = len(answer) > 50
        tiene_alta_conf = confidence > 0.7
        recupero_chunks = len(contexts) >= 5
        
        # Detectar posibles problemas
        posibles_problemas = []
        if 'no sé' in answer.lower() or 'no tengo información' in answer.lower():
            posibles_problemas.append('respuesta_negativa')
        if len(answer) < 30:
            posibles_problemas.append('respuesta_muy_corta')
        if confidence < 0.5:
            posibles_problemas.append('baja_confianza')
        if len(contexts) < 3:
            posibles_problemas.append('pocos_chunks')
        
        resultado = {
            'id': i,
            'pregunta': pregunta,
            'categoria': categoria,
            'respuesta': answer,
            'confidence': confidence,
            'tiempo': elapsed,
            'num_chunks': len(contexts),
            'longitud_respuesta': len(answer),
            'tiene_contenido': tiene_contenido,
            'tiene_alta_conf': tiene_alta_conf,
            'recupero_chunks': recupero_chunks,
            'calidad': tiene_contenido and tiene_alta_conf and recupero_chunks,
            'problemas': posibles_problemas
        }
        
        resultados.append(resultado)
        
    except Exception as e:
        print(f"\n❌ ERROR en pregunta {i}: {e}")
        resultados.append({
            'id': i,
            'pregunta': pregunta,
            'categoria': detectar_categoria(pregunta),
            'respuesta': '',
            'confidence': 0.0,
            'tiempo': time.time() - start,
            'num_chunks': 0,
            'longitud_respuesta': 0,
            'tiene_contenido': False,
            'tiene_alta_conf': False,
            'recupero_chunks': False,
            'calidad': False,
            'problemas': ['error'],
            'error': str(e)
        })

total_time = time.time() - start_total

print(f"\n✅ Procesamiento completado en {total_time:.1f}s\n")

# ANÁLISIS DE RESULTADOS
print("="*80)
print("📊 ANÁLISIS DE RESULTADOS")
print("="*80)
print()

total = len(resultados)
con_calidad = sum(1 for r in resultados if r['calidad'])
con_contenido = sum(1 for r in resultados if r['tiene_contenido'])
con_alta_conf = sum(1 for r in resultados if r['tiene_alta_conf'])

avg_confidence = sum(r['confidence'] for r in resultados) / total
min_confidence = min(r['confidence'] for r in resultados)
max_confidence = max(r['confidence'] for r in resultados)
avg_time = sum(r['tiempo'] for r in resultados) / total
avg_response_len = sum(r['longitud_respuesta'] for r in resultados) / total

print("📈 MÉTRICAS GLOBALES:")
print(f"   • Respuestas de calidad: {con_calidad}/{total} ({con_calidad/total*100:.1f}%)")
print(f"   • Con contenido (>50 chars): {con_contenido}/{total} ({con_contenido/total*100:.1f}%)")
print(f"   • Alta confianza (>0.7): {con_alta_conf}/{total} ({con_alta_conf/total*100:.1f}%)")
print(f"   • Confidence: avg={avg_confidence:.3f}, min={min_confidence:.3f}, max={max_confidence:.3f}")
print(f"   • Tiempo promedio: {avg_time:.2f}s")
print(f"   • Longitud promedio: {avg_response_len:.0f} chars")
print()

# Análisis por categoría
print("📊 ANÁLISIS POR CATEGORÍA:")
print(f"{'Categoría':<15} {'Total':<8} {'Calidad':<10} {'% Calidad':<12}")
print("-"*80)

for cat in ['desayunos', 'coles', 'resis', 'general', 'dana', 'otros']:
    cat_results = [r for r in resultados if r['categoria'] == cat]
    if cat_results:
        cat_total = len(cat_results)
        cat_calidad = sum(1 for r in cat_results if r['calidad'])
        cat_pct = cat_calidad/cat_total*100 if cat_total > 0 else 0
        print(f"{cat:<15} {cat_total:<8} {cat_calidad:<10} {cat_pct:.1f}%")

print()

# Análisis de problemas
print("🔍 ANÁLISIS DE PROBLEMAS DETECTADOS:")
problemas_count = {}
for r in resultados:
    for prob in r['problemas']:
        problemas_count[prob] = problemas_count.get(prob, 0) + 1

if problemas_count:
    print(f"{'Problema':<25} {'Frecuencia':<12}")
    print("-"*80)
    for prob, count in sorted(problemas_count.items(), key=lambda x: x[1], reverse=True):
        print(f"{prob:<25} {count:<12} ({count/total*100:.1f}%)")
else:
    print("   ✅ No se detectaron problemas")

print()

# Ejemplos de respuestas problemáticas
problematicas = [r for r in resultados if not r['calidad']]
if problematicas:
    print("❌ EJEMPLOS DE RESPUESTAS PROBLEMÁTICAS (primeras 5):")
    print("-"*80)
    for r in problematicas[:5]:
        print(f"\nID: {r['id']}")
        print(f"Pregunta: {r['pregunta']}")
        print(f"Respuesta ({r['longitud_respuesta']} chars, conf={r['confidence']:.2f}):")
        print(f"{r['respuesta'][:150]}...")
        print(f"Problemas: {', '.join(r['problemas'])}")

print()

# Ejemplos de respuestas buenas
buenas = [r for r in resultados if r['calidad']][:3]
if buenas:
    print("✅ EJEMPLOS DE RESPUESTAS BUENAS (primeras 3):")
    print("-"*80)
    for r in buenas:
        print(f"\nID: {r['id']}")
        print(f"Pregunta: {r['pregunta']}")
        print(f"Respuesta ({r['longitud_respuesta']} chars, conf={r['confidence']:.2f}):")
        print(f"{r['respuesta'][:150]}...")

print()

# Guardar resultados detallados
output_file = f'results/benchmark_115_queries_{int(time.time())}.json'
import os
os.makedirs('results', exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'total_preguntas': total,
        'metricas_globales': {
            'calidad': f"{con_calidad}/{total}",
            'porcentaje_calidad': f"{con_calidad/total*100:.1f}%",
            'avg_confidence': avg_confidence,
            'min_confidence': min_confidence,
            'max_confidence': max_confidence,
            'tiempo_total': total_time,
            'avg_tiempo': avg_time
        },
        'resultados': resultados
    }, f, indent=2, ensure_ascii=False)

print(f"💾 Resultados guardados en: {output_file}\n")

# VEREDICTO FINAL
print("="*80)
if con_calidad >= 92:  # 80% o más
    print("🎉 ✅ SISTEMA FUNCIONA EXCELENTEMENTE")
    print(f"   {con_calidad}/{total} respuestas de calidad ({con_calidad/total*100:.1f}%)")
elif con_calidad >= 69:  # 60-80%
    print("⚠️  SISTEMA FUNCIONA ACEPTABLEMENTE")
    print(f"   {con_calidad}/{total} respuestas de calidad - Necesita mejoras")
else:
    print("❌ SISTEMA NECESITA MEJORAS URGENTES")
    print(f"   Solo {con_calidad}/{total} respuestas de calidad")

print("="*80)
print()

print("🔧 RECOMENDACIONES PARA MEJORAR EL PROMPT:")
print("-"*80)

# Análisis de patrones de fallo
if 'respuesta_negativa' in problemas_count and problemas_count['respuesta_negativa'] > 5:
    print("1. ⚠️  Muchas respuestas con 'no sé'")
    print("   → Mejorar prompt para ser más asertivo con la información disponible")

if 'respuesta_muy_corta' in problemas_count and problemas_count['respuesta_muy_corta'] > 10:
    print("2. ⚠️  Respuestas muy cortas")
    print("   → Añadir instrucción de dar respuestas completas y detalladas")

if avg_confidence > 0.9:
    print("3. ⚠️  Confidence muy alto y poco variable")
    print("   → Sistema demasiado confiado, revisar cálculo de confidence")

if con_calidad < 92:
    print("4. ⚠️  Calidad general mejorable")
    print("   → Revisar prompt del sistema y formato de respuestas")

print()


