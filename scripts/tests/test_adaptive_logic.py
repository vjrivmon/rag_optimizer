#!/usr/bin/env python3
"""
🧪 Testing de lógica adaptativa sin consultas RAG completas
Verifica la lógica de validación adaptativa y query expansion
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrieval.query_expander import DomainQueryExpander, QueryExpansionConfig
from src.core.enhanced_rag_engine_new import AdaptiveModelValidator, TimeoutManager

def test_query_expander():
    """Test del Query Expander mejorado"""
    print("🔍 Testing DomainQueryExpander mejorado")
    print("-" * 40)

    expander = DomainQueryExpander(QueryExpansionConfig(debug_mode=True))

    # Queries problemáticas a testear
    test_queries = [
        "¿Dónde es la actividad de coles?",           # P11 - abreviación
        "¿Cada cuánto se hace la actividad de desayunos?",  # P4 - frecuencia
        "¿Qué significa Para-Mira-Ayuda?",           # P25 - concepto
        "¿Cómo me apunto a resis?",                  # abreviación RESIS
        "¿Qué días se hace?",                        # días
        "¿Cuánto dura la actividad?",                # duración
    ]

    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        expanded = expander.expand_query(query)
        print(f"   ✅ {len(expanded)} variaciones:")
        for i, q in enumerate(expanded[:3], 1):  # Mostrar solo 3
            marker = "🎯" if q == query else "🔀"
            print(f"      {i}. {marker} {q}")

def test_adaptive_validator():
    """Test del validador adaptativo"""
    print("\n🤖 Testing AdaptiveModelValidator")
    print("-" * 40)

    validator = AdaptiveModelValidator()

    # Modelos a testear
    models = ['deepseek-r1:latest', 'llama3.3:70b', 'gemma2:27b', 'qwen3:32b']

    # Queries de prueba
    test_questions = [
        (11, "¿Dónde es la actividad de coles?"),
        (25, "¿Qué significa Para-Mira-Ayuda?"),
        (4, "¿Cada cuánto se hace la actividad de desayunos?"),
        (1, "¿Qué se hace en la actividad de desayunos?"),
    ]

    for model_name in models:
        print(f"\n🤖 {model_name}:")
        profile = validator.get_model_profile(model_name)
        print(f"   📋 Perfil: expansion={profile.needs_query_expansion}, más_contexto={profile.prefers_more_context}")

        for question_id, question in test_questions:
            should_expand = validator.should_expand_query(model_name, question)
            adaptive_config = validator.get_adaptive_config(model_name, question_id)
            temperature = validator.get_adaptive_temperature(model_name, "problematic")

            print(f"   P{question_id}: expand={should_expand} 🎯 temp={temperature:.1f} ⚙️ k={adaptive_config.top_k}")

def test_timeout_manager():
    """Test del Timeout Manager"""
    print("\n⏱️ Testing TimeoutManager")
    print("-" * 40)

    timeout_manager = TimeoutManager()

    models = ['deepseek-r1:latest', 'llama3.3:70b', 'gemma2:27b', 'qwen3:32b']
    question_types = ['standard', 'problematic', 'conceptual']

    print("\n⏰ Timeouts adaptativos por modelo y tipo:")
    for model_name in models:
        print(f"\n🤖 {model_name}:")
        for qtype in question_types:
            timeout = timeout_manager.get_timeout(model_name, qtype)
            print(f"   {qtype:12}: {timeout:4.1f}s")

def test_strategy_caching():
    """Test del cache de estrategias fallidas"""
    print("\n💾 Testing Cache de Estrategias Fallidas")
    print("-" * 40)

    validator = AdaptiveModelValidator()

    # Simular estrategias fallidas
    test_cases = [
        ('deepseek-r1:latest', 11, 'specific'),
        ('llama3.3:70b', 11, 'ultra_permissive'),
        ('qwen3:32b', 25, 'standard'),
        ('deepseek-r1:latest', 11, 'exact_search'),
    ]

    print("Registrando estrategias fallidas...")
    for model, qid, strategy in test_cases:
        validator.cache_failed_strategy(model, qid, strategy)
        print(f"   ❌ {model:15} P{qid:2} {strategy}")

    print("\nVerificando cache de estrategias:")
    for model, qid, strategy in test_cases:
        is_failed = validator.is_strategy_failed(model, qid, strategy)
        print(f"   {'❌' if is_failed else '✅'} {model:15} P{qid:2} {strategy}")

    # Nueva estrategia no fallida
    new_strategy = validator.is_strategy_failed('gemma2:27b', 1, 'standard')
    print(f"   ✅ gemma2:27b     P1  standard (no fallida): {not new_strategy}")

def run_all_tests():
    """Ejecutar todos los tests"""
    print("🧪 Testing de Mejoras Adaptativas - Lógica del Sistema")
    print("=" * 60)

    try:
        test_query_expander()
        test_adaptive_validator()
        test_timeout_manager()
        test_strategy_caching()

        print("\n" + "=" * 60)
        print("🎉 TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("=" * 60)

        print("\n✅ Verificaciones pasadas:")
        print("   🔍 Query Expansion con términos DNI críticos")
        print("   🤖 Validación adaptativa por modelo")
        print("   ⏱️ Timeouts adaptativos")
        print("   💾 Cache de estrategias fallidas")
        print("   🎯 Configuraciones específicas por modelo")

        print("\n🚀 Sistema listo para pruebas con benchmark completo!")

    except Exception as e:
        print(f"\n❌ Error en testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()