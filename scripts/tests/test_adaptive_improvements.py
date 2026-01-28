#!/usr/bin/env python3
"""
🧪 Testing de mejoras adaptativas para preguntas problemáticas
Testea las optimizaciones implementadas en EnhancedRAGEngineNew
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.core.model_wrapper import LLMWrapper

def test_problematic_questions():
    """Test específico para las preguntas problemáticas identificadas"""

    print("🧪 Testing de Mejoras Adaptativas - Preguntas Problemáticas")
    print("="*60)

    # Preguntas problemáticas con sus respuestas esperadas
    problematic_questions = {
        4: {
            'question': '¿Cada cuánto se hace la actividad de desayunos?',
            'expected_keywords': ['semana', 'semanal', 'frecuencia'],
            'description': 'P4 - FRECUENCIA DESAYUNOS (scores: 0.0-0.99)'
        },
        11: {
            'question': '¿Dónde es la actividad de coles?',
            'expected_keywords': ['ceip antonio ferrandis', 'la coma', 'valencia'],
            'description': 'P11 - COLES (scores: 0.0-1.0, 2 modelos con 0.0)'
        },
        25: {
            'question': '¿Qué significa Para-Mira-Ayuda?',
            'expected_keywords': ['para', 'mira', 'ayuda', 'filosofía', 'lema'],
            'description': 'P25 - PARA-MIRA-AYUDA (todos los modelos fallaron, max 0.34)'
        }
    }

    # Modelos a testear
    models_to_test = [
        'gemma2:27b',      # El mejor modelo
        'llama3.3:70b',   # Problemas con abreviaciones
        'qwen3:32b',      # Inconsistente
        'deepseek-r1:latest'  # El peor modelo
    ]

    # Configuración
    vector_store_path = "data/vectorstore/chroma_db"
    results = {}

    for model_name in models_to_test:
        print(f"\n🤖 Testeando modelo: {model_name}")
        print("-" * 50)

        try:
            # Inicializar modelo
            model = LLMWrapper(model_name, f"http://ollama.gti-ia.upv.es:11434")
            enhanced_rag = EnhancedRAGEngineNew(vector_store_path, model)

            model_results = {}

            for question_id, q_info in problematic_questions.items():
                print(f"\n   📝 {q_info['description']}")
                print(f"   Pregunta: {q_info['question']}")

                start_time = time.time()

                # Procesar con validación adaptativa
                result = enhanced_rag.process_query_with_validation(
                    question=q_info['question'],
                    question_id=question_id,
                    max_attempts=3,
                    min_confidence=0.6  # Bajar para testear
                )

                end_time = time.time()
                processing_time = end_time - start_time

                # Analizar resultado
                answer = result['answer']
                validation = result['validation']
                contexts = result['contexts']
                used_fallback = result.get('used_fallback', False)

                # Verificar keywords
                answer_lower = answer.lower()
                keywords_found = [kw for kw in q_info['expected_keywords'] if kw in answer_lower]
                keyword_coverage = len(keywords_found) / len(q_info['expected_keywords'])

                print(f"   ⏱️  Tiempo: {processing_time:.2f}s")
                print(f"   🎯 Confianza: {validation.confidence:.3f}")
                print(f"   ✅ Válida: {validation.is_valid}")
                print(f"   🔄 Fallback: {used_fallback}")
                print(f"   🔍 Keywords encontradas: {keywords_found}/{len(q_info['expected_keywords'])} ({keyword_coverage:.1%})")
                print(f"   📄 Contextos: {len(contexts)}")

                # Mostrar respuesta
                answer_preview = answer[:100] + "..." if len(answer) > 100 else answer
                print(f"   💬 Respuesta: '{answer_preview}'")

                # Guardar resultados
                model_results[question_id] = {
                    'question': q_info['question'],
                    'answer': answer,
                    'confidence': validation.confidence,
                    'is_valid': validation.is_valid,
                    'keyword_coverage': keyword_coverage,
                    'processing_time': processing_time,
                    'used_fallback': used_fallback,
                    'contexts_count': len(contexts),
                    'error_type': validation.error_type
                }

            results[model_name] = model_results

        except Exception as e:
            print(f"   ❌ Error con modelo {model_name}: {e}")
            results[model_name] = {'error': str(e)}

    # Resumen de resultados
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*60)

    summary = {
        'total_tests': 0,
        'successful_tests': 0,
        'high_confidence_tests': 0,
        'timeout_tests': 0,
        'fallback_tests': 0
    }

    for model_name, model_results in results.items():
        if 'error' in model_results:
            print(f"\n❌ {model_name}: ERROR - {model_results['error']}")
            continue

        print(f"\n🤖 {model_name}:")

        for question_id, result in model_results.items():
            summary['total_tests'] += 1

            confidence = result['confidence']
            is_valid = result['is_valid']
            keyword_coverage = result['keyword_coverage']
            used_fallback = result['used_fallback']

            # Evaluar éxito
            success = is_valid and confidence > 0.5 and keyword_coverage > 0.3
            high_confidence = confidence > 0.8
            timeout_occurred = result.get('error_type') == 'timeout'

            if success:
                summary['successful_tests'] += 1
            if high_confidence:
                summary['high_confidence_tests'] += 1
            if timeout_occurred:
                summary['timeout_tests'] += 1
            if used_fallback:
                summary['fallback_tests'] += 1

            # Iconos de estado
            status_icon = "✅" if success else ("⚠️" if confidence > 0.3 else "❌")
            confidence_icon = "🎯" if high_confidence else "📊"
            fallback_icon = "🔄" if used_fallback else "🎯"
            timeout_icon = "⏰" if timeout_occurred else "⏱️"

            print(f"   P{question_id}: {status_icon} {confidence:.2f} {confidence_icon} {keyword_coverage:.1%} 📍 {fallback_icon} {timeout_icon}")

    # Estadísticas finales
    print(f"\n📈 ESTADÍSTICAS FINALES:")
    print(f"   Total tests: {summary['total_tests']}")
    print(f"   Exitosos: {summary['successful_tests']} ({summary['successful_tests']/summary['total_tests']:.1%})")
    print(f"   Alta confianza: {summary['high_confidence_tests']} ({summary['high_confidence_tests']/summary['total_tests']:.1%})")
    print(f"   Con timeout: {summary['timeout_tests']} ({summary['timeout_tests']/summary['total_tests']:.1%})")
    print(f"   Con fallback: {summary['fallback_tests']} ({summary['fallback_tests']/summary['total_tests']:.1%})")

    # Verificar si las mejoras funcionaron
    success_rate = summary['successful_tests'] / summary['total_tests']
    if success_rate > 0.7:
        print(f"\n🎉 EXCELENTE: Tasa de éxito del {success_rate:.1%} - Las mejoras funcionaron muy bien!")
    elif success_rate > 0.5:
        print(f"\n✅ BUENO: Tasa de éxito del {success_rate:.1%} - Las mejoras son efectivas.")
    else:
        print(f"\n⚠️ NECESITA MEJORAS: Tasa de éxito del {success_rate:.1%} - Requiere más ajustes.")

    return results

if __name__ == "__main__":
    test_problematic_questions()