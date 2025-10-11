#!/usr/bin/env python3
"""
🧪 Test Enhanced RAG Engine v2.1
Valida las mejoras implementadas para eliminar desplomes como P22
"""

import json
import time
from typing import Dict, List, Any

# Imports del proyecto
from src.core.enhanced_rag_engine import EnhancedRAGEngine
from src.core.model_wrapper import LLMWrapper

def test_p22_improvement():
    """Test específico para validar la mejora de P22"""
    print("🎯 Test P22: ¿Qué se hace en la actividad de resis?")
    print("=" * 60)

    # Inicializar Enhanced RAG Engine
    enhanced_rag = EnhancedRAGEngine(
        vector_store_path="data/vectorstore/chroma_db",
        use_hybrid=True
    )

    # Test de recuperación
    query = "¿Qué se hace en la actividad de resis?"

    print(f"\n📊 1. Enhanced RAG - Retrieval con fallback:")
    start_time = time.time()
    results = enhanced_rag.retrieve_with_fallback(query)
    end_time = time.time()

    print(f"⏱️ Tiempo de recuperación: {end_time - start_time:.2f}s")
    print(f"📋 Resultados recuperados: {len(results)}")

    # Analizar resultados
    has_resis_in_top3 = any("resis" in r['content'].lower() for r in results[:3])
    has_resis_in_top5 = any("resis" in r['content'].lower() for r in results[:5])

    print(f"✅ Resis en Top-3: {'SÍ' if has_resis_in_top3 else 'NO'}")
    print(f"✅ Resis en Top-5: {'SÍ' if has_resis_in_top5 else 'NO'}")

    # Encontrar posición del chunk RESIS
    resis_position = None
    for i, r in enumerate(results):
        if "resis" in r['content'].lower():
            resis_position = i + 1
            print(f"🎯 Chunk RESIS encontrado en posición: {resis_position}")
            print(f"📄 Content: {r['content'][:200]}...")
            break

    if not resis_position:
        print("❌ Chunk RESIS NO encontrado")
        return False

    # Calcular confianza
    confidence = enhanced_rag.get_confidence_score(results, query)
    print(f"📈 Score de confianza: {confidence:.3f}")

    return resis_position <= 5 and confidence > 0.5

def test_multiple_problematic_queries():
    """Test varias queries problemáticas"""
    print(f"\n🔍 Test Múltiples Queries Problemáticas")
    print("=" * 60)

    enhanced_rag = EnhancedRAGEngine(
        vector_store_path="data/vectorstore/chroma_db",
        use_hybrid=True
    )

    # Queries conocidas problemáticas
    problematic_queries = [
        {
            "id": 22,
            "query": "¿Qué se hace en la actividad de resis?",
            "expected_terms": ["resis", "acollida", "residencia"]
        },
        {
            "id": 4,
            "query": "¿Cada cuánto se hace la actividad de desayunos?",
            "expected_terms": ["desayuno", "frecuencia", "semana"]
        },
        {
            "id": 6,
            "query": "¿Cómo me apunto a desayunos solidarios?",
            "expected_terms": ["apuntar", "inscribir", "formulario"]
        }
    ]

    results = {}

    for q_info in problematic_queries:
        q_id = q_info["id"]
        query = q_info["query"]
        expected_terms = q_info["expected_terms"]

        print(f"\n📝 Query P{q_id}: {query}")

        # Test retrieval
        retrieval_results = enhanced_rag.retrieve_with_fallback(query)

        # Validar resultados
        has_expected_terms = any(
            any(term in r['content'].lower() for term in expected_terms)
            for r in retrieval_results[:3]
        )

        confidence = enhanced_rag.get_confidence_score(retrieval_results, query)

        results[f"P{q_id}"] = {
            "success": has_expected_terms and confidence > 0.4,
            "confidence": confidence,
            "results_count": len(retrieval_results),
            "has_expected_terms": has_expected_terms
        }

        print(f"  ✅ Términos esperados: {'SÍ' if has_expected_terms else 'NO'}")
        print(f"  📈 Confianza: {confidence:.3f}")
        print(f"  📋 Resultados: {len(retrieval_results)}")

    return results

def compare_with_original():
    """Compara Enhanced RAG vs Original RAG"""
    print(f"\n⚖️ Comparación: Enhanced RAG vs Original RAG")
    print("=" * 60)

    # Enhanced RAG
    enhanced_rag = EnhancedRAGEngine(
        vector_store_path="data/vectorstore/chroma_db",
        use_hybrid=True
    )

    # Original RAG
    from src.core.rag_engine import ConfigurableRAGEngine
    original_rag = ConfigurableRAGEngine(
        vector_store_path="data/vectorstore/chroma_db",
        use_hybrid=True
    )

    test_query = "¿Qué se hace en la actividad de resis?"

    print(f"Query: {test_query}")
    print("")

    # Test Original RAG
    print("🔍 Original RAG:")
    start_time = time.time()
    original_results = original_rag.retrieve(test_query)
    original_time = time.time() - start_time

    original_has_resis = any("resis" in r['content'].lower() for r in original_results[:5])
    original_confidence = len(original_results) / 10.0  # Simple proxy

    print(f"  Tiempo: {original_time:.2f}s")
    print(f"  Resultados: {len(original_results)}")
    print(f"  Tiene RESIS: {'SÍ' if original_has_resis else 'NO'}")
    print(f"  Confianza: {original_confidence:.3f}")

    print("")

    # Test Enhanced RAG
    print("🚀 Enhanced RAG:")
    start_time = time.time()
    enhanced_results = enhanced_rag.retrieve_with_fallback(test_query)
    enhanced_time = time.time() - start_time

    enhanced_has_resis = any("resis" in r['content'].lower() for r in enhanced_results[:5])
    enhanced_confidence = enhanced_rag.get_confidence_score(enhanced_results, test_query)

    print(f"  Tiempo: {enhanced_time:.2f}s")
    print(f"  Resultados: {len(enhanced_results)}")
    print(f"  Tiene RESIS: {'SÍ' if enhanced_has_resis else 'NO'}")
    print(f"  Confianza: {enhanced_confidence:.3f}")

    # Comparación
    print("")
    print("📊 Mejoras:")
    improvement_time = ((original_time - enhanced_time) / original_time) * 100 if original_time > 0 else 0
    improvement_confidence = ((enhanced_confidence - original_confidence) / original_confidence) * 100 if original_confidence > 0 else 0

    print(f"  ⏱️ Tiempo: {improvement_time:+.1f}%")
    print(f"  📈 Confianza: {improvement_confidence:+.1f}%")
    print(f"  ✅ RESIS recuperado: {'MEJORÓ' if enhanced_has_resis and not original_has_resis else 'IGUAL' if enhanced_has_resis == original_has_resis else 'EMPEORÓ'}")

    return {
        "original": {
            "has_resis": original_has_resis,
            "confidence": original_confidence,
            "time": original_time
        },
        "enhanced": {
            "has_resis": enhanced_has_resis,
            "confidence": enhanced_confidence,
            "time": enhanced_time
        }
    }

def test_query_expansion():
    """Test la funcionalidad de query expansion"""
    print(f"\n🔄 Test Query Expansion")
    print("=" * 60)

    enhanced_rag = EnhancedRAGEngine(
        vector_store_path="data/vectorstore/chroma_db",
        use_hybrid=True
    )

    test_queries = [
        "¿Qué se hace en resis?",
        "actividades de desayunos",
        "voluntariado coles cómo participar",
        "dónde resis ubicación"
    ]

    for query in test_queries:
        expanded = enhanced_rag.expand_query(query)
        print(f"Original:  '{query}'")
        print(f"Expandida: '{expanded}'")
        print("")

def main():
    """Función principal de tests"""
    print("🧪 Test Suite - Enhanced RAG Engine v2.1")
    print("=" * 70)

    all_results = {}

    # Test 1: P22 Improvement
    print("1️⃣ Test P22 Improvement")
    p22_success = test_p22_improvement()
    all_results['p22_improvement'] = p22_success

    # Test 2: Multiple Problematic Queries
    print(f"\n2️⃣ Test Multiple Problematic Queries")
    multi_results = test_multiple_problematic_queries()
    all_results['multiple_queries'] = multi_results

    # Test 3: Comparison with Original
    print(f"\n3️⃣ Comparison with Original RAG")
    comparison_results = compare_with_original()
    all_results['comparison'] = comparison_results

    # Test 4: Query Expansion
    print(f"\n4️⃣ Test Query Expansion")
    test_query_expansion()

    # Resumen Final
    print(f"\n" + "="*70)
    print("📋 RESUMEN FINAL DE TESTS")
    print("="*70)

    print(f"✅ P22 Improvement: {'PASS' if p22_success else 'FAIL'}")

    multi_success_rate = sum(1 for r in multi_results.values() if r['success']) / len(multi_results)
    print(f"📊 Multiple Queries Success Rate: {multi_success_rate:.1%}")

    enhanced_better = comparison_results['enhanced']['has_resis'] and not comparison_results['original']['has_resis']
    print(f"🚀 Enhanced vs Original: {'BETTER' if enhanced_better else 'EQUAL or WORSE'}")

    # Guardar resultados
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    results_file = f"results/enhanced_rag_test_{timestamp}.json"

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Resultados guardados en: {results_file}")

    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    if p22_success:
        print("✅ Enhanced RAG resuelve el problema P22 - ¡Implementar!")
    else:
        print("❌ Enhanced RAG NO resuelve P22 - Requiere más ajustes")

    if multi_success_rate > 0.8:
        print("✅ Buen rendimiento en múltiples queries problemáticas")
    else:
        print("⚠️ Necesita más optimización para queries variadas")

    if enhanced_better:
        print("🚀 Enhanced RAG es superior al original - ¡Desplegar!")
    else:
        print("➖ Enhanced RAG necesita más mejoras")

if __name__ == "__main__":
    main()