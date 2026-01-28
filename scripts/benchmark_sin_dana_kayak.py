#!/usr/bin/env python3
"""
Benchmark de VALIDACIÓN: Sin DANA ni Kayak
Verifica que el sistema solo responde sobre Coles, Resis y Desayunos
"""

import sys
sys.path.insert(0, '.')

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
import time
import json

print("="*80)
print("🧪 BENCHMARK VALIDACIÓN - Sin DANA ni Kayak")
print("="*80)
print()

# 30 preguntas críticas de validación
preguntas_validacion = {
    # RESIS (nuevas) - 10 preguntas
    "resis": [
        "¿Cómo se llama la residencia?",
        "¿Dónde está la residencia?",
        "¿Cuándo se va a la residencia?",
        "¿Qué actividades se hacen con los abuelitos?",
        "¿Cuántos abuelitos hay en la residencia?",
        "¿Quién es el responsable de RESIS?",
        "¿Necesito formación para ir a la residencia?",
        "¿Puedo ir de prueba a la residencia?",
        "¿Qué días hay actividades con ancianos?",
        "¿Se necesita compromiso para ir a la residencia?",
    ],
    
    # COLES - 7 preguntas
    "coles": [
        "¿Qué es COLES?",
        "¿Dónde es el refuerzo escolar?",
        "¿Qué días hay refuerzo escolar?",
        "¿Necesito experiencia para dar refuerzo escolar?",
        "¿Con cuántos niños trabajo en COLES?",
        "¿Qué materias se enseñan en COLES?",
        "¿Cuánto dura una sesión de refuerzo escolar?",
    ],
    
    # DESAYUNOS - 7 preguntas
    "desayunos": [
        "¿A qué hora son los desayunos solidarios?",
        "¿Dónde es el punto de encuentro para desayunos?",
        "¿Qué se lleva a los desayunos?",
        "¿Cuántos voluntarios van a desayunos?",
        "¿Puedo ir solo a los desayunos?",
        "¿Cada cuánto hay desayunos solidarios?",
        "¿Qué hacemos en los desayunos además de dar comida?",
    ],
    
    # EXCLUSIÓN (NO debe responder) - 6 preguntas
    "exclusion": [
        "¿Qué es el proyecto de la DANA?",
        "¿Cómo ayudo a los afectados por la DANA?",
        "¿Cuándo es la recogida de plásticos en kayak?",
        "¿Dónde están los kayaks?",
        "¿Qué es Rehabilitar Valencia?",
        "¿Cómo me apunto al kayak?",
    ],
}

print(f"📋 30 preguntas de validación:")
print(f"   • RESIS (nuevas): 10")
print(f"   • COLES: 7")
print(f"   • DESAYUNOS: 7")
print(f"   • EXCLUSIÓN (DANA/kayak): 6")
print()

# Inicializar
print("🔧 Inicializando sistema...")
model = LLMWrapper("gemma2:27b", "https://ollama.gti-ia.upv.es:443/api/generate")
rag = EnhancedRAGEngineNew('data/vectorstore/chroma_db', model)
print("✅ Sistema listo\n")

resultados = {}
start_total = time.time()

for categoria, preguntas in preguntas_validacion.items():
    print(f"\n{'='*80}")
    print(f"📂 CATEGORÍA: {categoria.upper()} ({len(preguntas)} preguntas)")
    print(f"{'='*80}\n")
    
    resultados[categoria] = []
    
    for i, pregunta in enumerate(preguntas, 1):
        print(f"   [{i}/{len(preguntas)}] {pregunta[:60]}...")
        
        start = time.time()
        
        try:
            result = rag.process_query_with_validation(pregunta, i)
            elapsed = time.time() - start
            
            answer = result.get('answer', '')
            confidence = result.get('validation').confidence if 'validation' in result else 0.0
            contexts = result.get('contexts', [])
            
            # Análisis de contenido
            answer_lower = answer.lower()
            
            # Detectar si menciona DANA o kayak (NO debe aparecer)
            menciona_dana = 'dana' in answer_lower or 'horta sud' in answer_lower or 'rehabilitar valencia' in answer_lower
            menciona_kayak = 'kayak' in answer_lower or 'plástico' in answer_lower or 'marina de valencia' in answer_lower
            
            # Calidad según categoría
            if categoria == "exclusion":
                # Para preguntas de exclusión, NO debe dar información específica de DANA/kayak
                # Debe redirigir o decir que no tiene info
                es_correcta = (
                    not menciona_dana and 
                    not menciona_kayak and
                    (
                        'no tengo información' in answer_lower or 
                        'no dispongo' in answer_lower or
                        'contacta' in answer_lower or
                        'whatsapp' in answer_lower or
                        len(answer) < 200  # Respuesta corta de redirección
                    )
                )
            else:
                # Para preguntas válidas, debe tener contenido y NO mencionar DANA/kayak
                es_correcta = (
                    len(answer) > 50 and 
                    confidence > 0.6 and
                    not menciona_dana and
                    not menciona_kayak
                )
            
            resultado = {
                'pregunta': pregunta,
                'respuesta': answer,
                'confidence': confidence,
                'tiempo': elapsed,
                'longitud': len(answer),
                'menciona_dana': menciona_dana,
                'menciona_kayak': menciona_kayak,
                'es_correcta': es_correcta,
                'num_chunks': len(contexts)
            }
            
            resultados[categoria].append(resultado)
            
            # Mostrar preview
            status = "✅" if es_correcta else "❌"
            warnings = []
            if menciona_dana:
                warnings.append("⚠️ DANA")
            if menciona_kayak:
                warnings.append("⚠️ Kayak")
            
            warnings_str = " ".join(warnings) if warnings else ""
            print(f"      {status} Conf: {confidence:.2f} | {len(answer)} chars | {elapsed:.1f}s {warnings_str}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            resultados[categoria].append({
                'pregunta': pregunta,
                'respuesta': '',
                'confidence': 0.0,
                'tiempo': time.time() - start,
                'longitud': 0,
                'menciona_dana': False,
                'menciona_kayak': False,
                'es_correcta': False,
                'num_chunks': 0,
                'error': str(e)
            })

total_time = time.time() - start_total

print(f"\n{'='*80}")
print("📊 RESULTADOS DE VALIDACIÓN")
print(f"{'='*80}\n")

# Análisis por categoría
total_correctas = 0
total_preguntas = 0

for categoria, resultados_cat in resultados.items():
    correctas = sum(1 for r in resultados_cat if r['es_correcta'])
    total = len(resultados_cat)
    total_correctas += correctas
    total_preguntas += total
    
    menciones_dana = sum(1 for r in resultados_cat if r['menciona_dana'])
    menciones_kayak = sum(1 for r in resultados_cat if r['menciona_kayak'])
    
    print(f"📂 {categoria.upper()}:")
    print(f"   ✅ Correctas: {correctas}/{total} ({correctas/total*100:.1f}%)")
    if menciones_dana > 0:
        print(f"   ⚠️  Menciones DANA: {menciones_dana}")
    if menciones_kayak > 0:
        print(f"   ⚠️  Menciones Kayak: {menciones_kayak}")
    print()

# Resumen global
print(f"{'='*80}")
print("🎯 RESUMEN GLOBAL:")
print(f"{'='*80}\n")
print(f"   • Total correctas: {total_correctas}/{total_preguntas} ({total_correctas/total_preguntas*100:.1f}%)")
print(f"   • Tiempo total: {total_time:.1f}s")
print(f"   • Tiempo promedio: {total_time/total_preguntas:.2f}s")
print()

# Verificación crítica: NO debe mencionar DANA ni kayak
total_menciones_dana = sum(sum(1 for r in cat if r['menciona_dana']) for cat in resultados.values())
total_menciones_kayak = sum(sum(1 for r in cat if r['menciona_kayak']) for cat in resultados.values())

print("🔍 VERIFICACIÓN CRÍTICA:")
if total_menciones_dana == 0 and total_menciones_kayak == 0:
    print("   ✅ NO se mencionó DANA ni kayak en ninguna respuesta")
else:
    print(f"   ❌ Se encontraron menciones:")
    if total_menciones_dana > 0:
        print(f"      • DANA: {total_menciones_dana} veces")
    if total_menciones_kayak > 0:
        print(f"      • Kayak: {total_menciones_kayak} veces")

print()

# Guardar resultados
output_file = f'results/benchmark_sin_dana_kayak_{int(time.time())}.json'
import os
os.makedirs('results', exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'total_preguntas': total_preguntas,
        'total_correctas': total_correctas,
        'porcentaje': f"{total_correctas/total_preguntas*100:.1f}%",
        'menciones_dana': total_menciones_dana,
        'menciones_kayak': total_menciones_kayak,
        'tiempo_total': total_time,
        'resultados_por_categoria': resultados
    }, f, indent=2, ensure_ascii=False)

print(f"💾 Resultados guardados en: {output_file}\n")

# VEREDICTO FINAL
print(f"{'='*80}")
if total_correctas >= 27 and total_menciones_dana == 0 and total_menciones_kayak == 0:  # 90%+
    print("🎉 ✅ SISTEMA LIMPIO Y FUNCIONAL")
    print(f"   {total_correctas}/{total_preguntas} correctas")
    print("   NO hay menciones de DANA ni kayak ✅")
elif total_correctas >= 24:  # 80%+
    print("⚠️  SISTEMA FUNCIONA - NECESITA AJUSTES MENORES")
    print(f"   {total_correctas}/{total_preguntas} correctas")
else:
    print("❌ SISTEMA NECESITA REVISIÓN")
    print(f"   Solo {total_correctas}/{total_preguntas} correctas")

if total_menciones_dana > 0 or total_menciones_kayak > 0:
    print(f"   ⚠️  AÚN HAY MENCIONES DE TEMAS EXCLUIDOS")

print(f"{'='*80}")

