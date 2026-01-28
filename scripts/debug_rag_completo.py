#!/usr/bin/env python3
"""
Script de Debug Exhaustivo del Sistema RAG
Muestra EXACTAMENTE qué chunks se recuperan y cómo se procesa
"""

import sys
sys.path.insert(0, '.')

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew

print("="*80)
print("🔍 DEBUG EXHAUSTIVO DEL SISTEMA RAG")
print("="*80)
print()

# Inicializar modelo y RAG
print("1️⃣ Inicializando sistema...")
model = LLMWrapper("gemma2:27b", "https://ollama.gti-ia.upv.es:443/api/generate")
rag = EnhancedRAGEngineNew('data/vectorstore/chroma_db', model)
print("✅ Sistema inicializado")
print()

# Test con "¿Qué es DNI?"
question = "¿Qué es DNI?"
question_id = 1

print("2️⃣ Procesando pregunta:", question)
print("-"*80)

# Procesar con el RAG avanzado
result = rag.process_query_with_validation(question, question_id)

print()
print("="*80)
print("📊 RESULTADO DEL PROCESAMIENTO")
print("="*80)
print()

# Mostrar estructura del resultado
print("🔑 Claves del resultado:", list(result.keys()))
print()

# Mostrar respuesta
print("💬 RESPUESTA:")
print("-"*80)
print(result['answer'])
print("-"*80)
print(f"Longitud: {len(result['answer'])} caracteres")
print()

# Mostrar validation
if 'validation' in result:
    validation = result['validation']
    print("✅ VALIDATION:")
    print(f"   • is_valid: {validation.is_valid}")
    print(f"   • confidence: {validation.confidence}")
    print(f"   • error_type: {validation.error_type}")
    print()

# Mostrar contexts
if 'contexts' in result:
    contexts = result['contexts']
    print(f"📚 CONTEXTS ({len(contexts)} chunks):")
    print("-"*80)
    for i, ctx in enumerate(contexts[:5], 1):
        content = ctx if isinstance(ctx, str) else ctx.get('content', str(ctx))
        print(f"\nChunk {i}:")
        print(f"Contenido: {content[:200]}...")
        
        # Verificar si contiene info de DNI
        if "Damos Nuestra Ilusión" in content:
            print("✅ ¡Contiene 'Damos Nuestra Ilusión'!")
        else:
            print("❌ NO contiene 'Damos Nuestra Ilusión'")
    print()

# Mostrar retrieval stats
if 'retrieval_stats' in result:
    stats = result['retrieval_stats']
    print("📊 RETRIEVAL STATS:")
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    print()

# Mostrar config usada
if 'config_used' in result:
    config = result['config_used']
    print("⚙️ CONFIG USADA:")
    print(f"   • name: {config.name}")
    print(f"   • top_k: {config.top_k}")
    print(f"   • similarity_threshold: {config.similarity_threshold}")
    print(f"   • semantic_weight: {config.semantic_weight}")
    print()

print("="*80)
print("🎯 ANÁLISIS FINAL")
print("="*80)
print()

# Verificaciones
checks = []

# 1. Respuesta tiene "Damos Nuestra Ilusión"
if "Damos Nuestra Ilusión" in result['answer']:
    checks.append("✅ Respuesta contiene 'Damos Nuestra Ilusión'")
else:
    checks.append("❌ Respuesta NO contiene 'Damos Nuestra Ilusión'")

# 2. Respuesta es suficientemente larga
if len(result['answer']) > 100:
    checks.append(f"✅ Respuesta suficientemente larga ({len(result['answer'])} chars)")
else:
    checks.append(f"⚠️ Respuesta corta ({len(result['answer'])} chars)")

# 3. Confidence dinámico
if 'validation' in result:
    conf = result['validation'].confidence
    if conf != 0.5 and conf != 0.7:
        checks.append(f"✅ Confidence dinámico ({conf:.3f})")
    else:
        checks.append(f"⚠️ Confidence parece estático ({conf:.3f})")

# 4. Chunks recuperados
if 'contexts' in result:
    num_contexts = len(result['contexts'])
    if num_contexts >= 8:
        checks.append(f"✅ Suficientes chunks ({num_contexts})")
    else:
        checks.append(f"⚠️ Pocos chunks ({num_contexts})")

# 5. Algún chunk tiene la info correcta
has_correct_info = False
if 'contexts' in result:
    for ctx in result['contexts']:
        content = ctx if isinstance(ctx, str) else ctx.get('content', str(ctx))
        if "Damos Nuestra Ilusión" in content:
            has_correct_info = True
            break
    
    if has_correct_info:
        checks.append("✅ Al menos un chunk tiene info correcta")
    else:
        checks.append("❌ Ningún chunk tiene info correcta")

for check in checks:
    print(check)

print()
print("="*80)
print("✅ DEBUG COMPLETADO")
print("="*80)

