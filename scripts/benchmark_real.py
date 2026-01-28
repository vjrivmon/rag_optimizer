#!/usr/bin/env python3
"""
Benchmark REAL del Sistema RAG
Prueba con 10 preguntas críticas y muestra resultados REALES
"""

import sys
sys.path.insert(0, '.')

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
import time

# Preguntas críticas para probar
PREGUNTAS_TEST = [
    ("¿Qué es DNI?", "Damos Nuestra Ilusión"),
    ("¿Cuál es el lema de DNI?", "PARA. MIRA. AYUDA"),
    ("¿A qué hora son los desayunos solidarios?", "8 de la mañana"),
    ("¿Dónde es el refuerzo escolar?", "CEIP Antonio Ferrandis"),
    ("¿Qué días se visita a los abuelitos?", "miércoles"),
    ("¿Cuántos voluntarios activos tiene DNI?", "400"),
    ("¿Qué significa PARA MIRA AYUDA?", "detente"),
    ("¿Cómo me apunto a los desayunos?", "formulario"),
    ("¿Dónde es el punto de encuentro para desayunos?", "Porta de la Mar"),
    ("¿Qué proyectos tiene DNI?", "desayunos")
]

print("="*80)
print("🧪 BENCHMARK REAL DEL SISTEMA RAG")
print("="*80)
print(f"\nProbando {len(PREGUNTAS_TEST)} preguntas críticas...\n")

# Inicializar
print("🔧 Inicializando sistema...")
model = LLMWrapper("gemma2:27b", "https://ollama.gti-ia.upv.es:443/api/generate")
rag = EnhancedRAGEngineNew('data/vectorstore/chroma_db', model)
print("✅ Sistema listo\n")

resultados = []
start_total = time.time()

for i, (pregunta, keyword_esperada) in enumerate(PREGUNTAS_TEST, 1):
    print(f"{'='*80}")
    print(f"🔍 PREGUNTA {i}/10: {pregunta}")
    print(f"{'='*80}")
    
    start = time.time()
    
    try:
        result = rag.process_query_with_validation(pregunta, i)
        elapsed = time.time() - start
        
        answer = result.get('answer', '')
        confidence = result.get('validation').confidence if 'validation' in result else 0.0
        contexts = result.get('contexts', [])
        
        # Verificar si contiene keyword esperada
        tiene_keyword = keyword_esperada.lower() in answer.lower()
        
        # Verificar si algún chunk tiene la info
        chunk_correcto = False
        for ctx in contexts[:3]:
            content = ctx if isinstance(ctx, str) else ctx.get('content', str(ctx))
            if keyword_esperada.lower() in content.lower():
                chunk_correcto = True
                break
        
        print(f"\n💬 RESPUESTA ({len(answer)} chars):")
        print(f"{answer[:200]}...")
        print(f"\n📊 MÉTRICAS:")
        print(f"   • Confidence: {confidence:.3f}")
        print(f"   • Tiempo: {elapsed:.2f}s")
        print(f"   • Chunks recuperados: {len(contexts)}")
        print(f"   • Keyword '{keyword_esperada}': {'✅ SÍ' if tiene_keyword else '❌ NO'}")
        print(f"   • Chunk correcto: {'✅ SÍ' if chunk_correcto else '❌ NO'}")
        
        resultado = {
            'pregunta': pregunta,
            'keyword': keyword_esperada,
            'tiene_keyword': tiene_keyword,
            'chunk_correcto': chunk_correcto,
            'confidence': confidence,
            'tiempo': elapsed,
            'respuesta_len': len(answer),
            'num_chunks': len(contexts),
            'success': tiene_keyword and confidence > 0.5
        }
        
        resultados.append(resultado)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        resultados.append({
            'pregunta': pregunta,
            'keyword': keyword_esperada,
            'tiene_keyword': False,
            'chunk_correcto': False,
            'confidence': 0.0,
            'tiempo': time.time() - start,
            'respuesta_len': 0,
            'num_chunks': 0,
            'success': False,
            'error': str(e)
        })
    
    print()

total_time = time.time() - start_total

# RESUMEN FINAL
print("\n" + "="*80)
print("📊 RESUMEN DEL BENCHMARK")
print("="*80)
print()

# Métricas globales
total = len(resultados)
exitosas = sum(1 for r in resultados if r['success'])
con_keyword = sum(1 for r in resultados if r['tiene_keyword'])
con_chunk_correcto = sum(1 for r in resultados if r['chunk_correcto'])

avg_confidence = sum(r['confidence'] for r in resultados) / total
avg_time = sum(r['tiempo'] for r in resultados) / total
avg_response_len = sum(r['respuesta_len'] for r in resultados) / total

print("📈 MÉTRICAS GLOBALES:")
print(f"   • Preguntas exitosas: {exitosas}/{total} ({exitosas/total*100:.1f}%)")
print(f"   • Con keyword correcta: {con_keyword}/{total} ({con_keyword/total*100:.1f}%)")
print(f"   • Con chunk correcto: {con_chunk_correcto}/{total} ({con_chunk_correcto/total*100:.1f}%)")
print(f"   • Confidence promedio: {avg_confidence:.3f}")
print(f"   • Tiempo promedio: {avg_time:.2f}s")
print(f"   • Longitud respuesta promedio: {avg_response_len:.0f} chars")
print(f"   • Tiempo total: {total_time:.2f}s")
print()

# Detalles por pregunta
print("📋 DETALLE POR PREGUNTA:")
print(f"{'#':<3} {'Keyword':<12} {'Chunk':<8} {'Conf':<6} {'Tiempo':<7}")
print("-"*80)

for i, r in enumerate(resultados, 1):
    keyword_icon = "✅" if r['tiene_keyword'] else "❌"
    chunk_icon = "✅" if r['chunk_correcto'] else "❌"
    
    print(f"{i:<3} {keyword_icon} {r['keyword']:<10} {chunk_icon} {r['confidence']:.3f}  {r['tiempo']:.2f}s")

print()

# VEREDICTO FINAL
print("="*80)
if exitosas >= 8:  # 80% o más
    print("🎉 ✅ SISTEMA FUNCIONA CORRECTAMENTE")
    print(f"   {exitosas}/{total} preguntas respondidas correctamente")
elif exitosas >= 6:  # 60-80%
    print("⚠️  SISTEMA FUNCIONA PARCIALMENTE")
    print(f"   {exitosas}/{total} preguntas correctas - Necesita mejoras")
else:
    print("❌ SISTEMA TIENE PROBLEMAS SERIOS")
    print(f"   Solo {exitosas}/{total} preguntas correctas")

print("="*80)

