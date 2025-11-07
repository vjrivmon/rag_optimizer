#!/usr/bin/env python3
"""
Test RÁPIDO: Solo preguntas de EXCLUSIÓN (DANA/kayak)
"""

import sys
sys.path.insert(0, '.')

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew

print("="*80)
print("🧪 TEST EXCLUSIÓN - DANA y Kayak")
print("="*80)
print()

preguntas_exclusion = [
    "¿Qué es el proyecto de la DANA?",
    "¿Cómo ayudo a los afectados por la DANA?",
    "¿Cuándo es la recogida de plásticos en kayak?",
    "¿Dónde están los kayaks?",
    "¿Qué es Rehabilitar Valencia?",
    "¿Cómo me apunto al kayak?",
]

model = LLMWrapper("gemma2:27b", "https://ollama.gti-ia.upv.es:443/api/generate")
rag = EnhancedRAGEngineNew('data/vectorstore/chroma_db', model)

print(f"📋 {len(preguntas_exclusion)} preguntas sobre temas EXCLUIDOS\n")

menciones_dana = 0
menciones_kayak = 0

for i, pregunta in enumerate(preguntas_exclusion, 1):
    print(f"\n{'='*80}")
    print(f"[{i}/{len(preguntas_exclusion)}] {pregunta}")
    print(f"{'='*80}\n")
    
    result = rag.process_query_with_validation(pregunta, i)
    answer = result.get('answer', '')
    
    answer_lower = answer.lower()
    tiene_dana = 'dana' in answer_lower or 'horta sud' in answer_lower or 'rehabilitar valencia' in answer_lower
    tiene_kayak = 'kayak' in answer_lower or 'plástico' in answer_lower
    
    if tiene_dana:
        menciones_dana += 1
    if tiene_kayak:
        menciones_kayak += 1
    
    print(f"RESPUESTA ({len(answer)} chars):")
    print(answer)
    print()
    
    print(f"ANÁLISIS:")
    if tiene_dana:
        print("   ❌ Menciona DANA")
    if tiene_kayak:
        print("   ❌ Menciona Kayak")
    if not tiene_dana and not tiene_kayak:
        print("   ✅ NO menciona temas excluidos")

print("\n" + "="*80)
print("🎯 RESULTADO FINAL")
print("="*80)
print()

if menciones_dana == 0 and menciones_kayak == 0:
    print("🎉 ✅ ÉXITO TOTAL")
    print("   El sistema NO menciona DANA ni kayak")
else:
    print("❌ FALLO")
    if menciones_dana > 0:
        print(f"   • DANA mencionado {menciones_dana} veces")
    if menciones_kayak > 0:
        print(f"   • Kayak mencionado {menciones_kayak} veces")

print("="*80)

