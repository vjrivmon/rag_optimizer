#!/usr/bin/env python3
"""
🧪 Script de Test para Enhanced RAG Engine con Validación

Prueba el nuevo sistema de validación inteligente con las preguntas problemáticas 11 y 20
para asegurar que se logran scores > 0.8 consistentemente.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import time
from typing import Dict, List, Any

# Imports del proyecto
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.core.model_wrapper import LLMWrapper

# Configuración
VECTOR_STORE_PATH = "data/vectorstore/chroma_db"
DATASET_PATH = "data/evaluation_dataset.json"

# Configuración de modelos para prueba
TEST_MODELS = [
    {"name": "gemma2:27b", "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"},
    {"name": "qwen3:32b", "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"}
]

def test_enhanced_validation():
    """Test completo del sistema de validación mejorada"""

    print("🧪 TESTING ENHANCED RAG ENGINE CON VALIDACIÓN INTELIGENTE")
    print("=" * 80)

    # Cargar dataset
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # Extraer preguntas problemáticas
    p11_data = next(q for q in dataset if q['id'] == 11)
    p20_data = next(q for q in dataset if q['id'] == 20)

    test_questions = [
        (p11_data['id'], p11_data['question'], p11_data['expected_answer']),
        (p20_data['id'], p20_data['question'], p20_data['expected_answer'])
    ]

    print(f"📋 Preguntas a testear:")
    for qid, question, expected in test_questions:
        print(f"   P{qid}: {question}")
        print(f"   Expected: {expected}")
        print()

    # Test con cada modelo
    all_results = []

    for model_config in TEST_MODELS:
        model_name = model_config['name']
        print(f"\n🤖 TESTEANDO MODELO: {model_name}")
        print("=" * 60)

        try:
            # Inicializar modelo y enhanced engine
            model = LLMWrapper(model_name, model_config['endpoint'])
            enhanced_engine = EnhancedRAGEngineNew(VECTOR_STORE_PATH, model)

            model_results = {
                'model_name': model_name,
                'questions': []
            }

            # Test cada pregunta problemática
            for qid, question, expected in test_questions:
                print(f"\n🎯 Testeando P{qid}: '{question}'")
                print("-" * 50)

                start_time = time.time()

                # Procesar con validación inteligente
                result = enhanced_engine.process_query_with_validation(
                    question=question,
                    question_id=qid,
                    max_attempts=3,
                    min_confidence=0.8
                )

                processing_time = time.time() - start_time

                # Analizar resultado
                validation = result['validation']
                answer = result['answer']
                config_used = result['config_used']
                retrieval_stats = result['retrieval_stats']

                # Evaluar calidad
                quality_score = evaluate_answer_quality(answer, expected, qid)

                print(f"✅ Resultado en {processing_time:.2f}s:")
                print(f"   Config usada: {config_used.name}")
                print(f"   Chunks recuperados: {retrieval_stats['num_chunks']}")
                print(f"   Chunks relevantes: {retrieval_stats['relevant_chunks']}")
                print(f"   Validación - Is Valid: {validation.is_valid}")
                print(f"   Validación - Confidence: {validation.confidence:.2f}")
                print(f"   Quality Score: {quality_score:.2f}")
                print(f"   Answer: {answer}")

                if validation.error_type:
                    print(f"   ⚠️ Error type: {validation.error_type}")

                if result.get('used_fallback'):
                    print(f"   🔄 Usó fallback: {result['used_fallback']}")

                # Guardar resultado
                question_result = {
                    'question_id': qid,
                    'question': question,
                    'expected_answer': expected,
                    'generated_answer': answer,
                    'validation': {
                        'is_valid': validation.is_valid,
                        'confidence': validation.confidence,
                        'error_type': validation.error_type,
                        'details': validation.details
                    },
                    'config_used': {
                        'name': config_used.name,
                        'top_k': config_used.top_k,
                        'similarity_threshold': config_used.similarity_threshold
                    },
                    'retrieval_stats': retrieval_stats,
                    'quality_score': quality_score,
                    'processing_time': processing_time,
                    'used_fallback': result.get('used_fallback', False)
                }

                model_results['questions'].append(question_result)

                # Verificar si cumple el objetivo
                if validation.confidence >= 0.8 and quality_score >= 0.8:
                    print(f"   🎉 OBJETIVO CUMPLIDO: Score ≥ 0.8")
                else:
                    print(f"   ❌ OBJETIVO NO CUMPLIDO: Score < 0.8")

            all_results.append(model_results)

        except Exception as e:
            print(f"❌ Error con modelo {model_name}: {str(e)}")
            continue

    # Generar resumen final
    generate_summary_report(all_results)

    return all_results

def evaluate_answer_quality(answer: str, expected: str, question_id: int) -> float:
    """Evalúa la calidad de la respuesta comparando con la esperada"""

    answer_lower = answer.lower()
    expected_lower = expected.lower()

    if question_id == 11:  # COLES
        # Buscar información clave
        has_ceip = 'ceip antonio ferrandis' in answer_lower or 'antonio ferrandis' in answer_lower
        has_valencia = 'valencia' in answer_lower
        has_coma = 'la coma' in answer_lower

        # Calcular score basado en presencia de información clave
        score = 0.0
        if has_ceip:
            score += 0.7
        if has_valencia:
            score += 0.2
        if has_coma:
            score += 0.1

        # Penalizar respuestas incorrectas
        if 'la acollida' in answer_lower or 'resis' in answer_lower:
            score = 0.0

    elif question_id == 20:  # RESIS
        # Buscar información clave
        has_acollida = 'la acollida' in answer_lower
        has_crevillente = 'crevillente' in answer_lower
        has_blasco = 'blasco ibáñez' in answer_lower

        # Calcular score basado en presencia de información clave
        score = 0.0
        if has_acollida:
            score += 0.6
        if has_crevillente:
            score += 0.3
        if has_blasco:
            score += 0.1

        # Penalizar respuestas incorrectas
        if 'ceip' in answer_lower or 'coles' in answer_lower:
            score = 0.0
    else:
        # Comparación simple de similitud para otras preguntas
        common_words = set(answer_lower.split()) & set(expected_lower.split())
        total_words = set(expected_lower.split())
        score = len(common_words) / len(total_words) if total_words else 0.0

    return min(score, 1.0)

def generate_summary_report(all_results: List[Dict[str, Any]]):
    """Genera reporte resumen de los resultados"""

    print("\n" + "📊 RESUMEN DE RESULTADOS" + "\n" + "=" * 80)

    total_tests = 0
    successful_tests = 0
    model_performance = {}

    for model_result in all_results:
        model_name = model_result['model_name']
        questions = model_result['questions']

        print(f"\n🤖 {model_name}:")
        print("-" * 40)

        model_success = 0
        model_total = len(questions)

        for q_result in questions:
            qid = q_result['question_id']
            confidence = q_result['validation']['confidence']
            quality = q_result['quality_score']

            # Considerar exitoso si ambos scores >= 0.8
            is_successful = confidence >= 0.8 and quality >= 0.8

            status = "✅" if is_successful else "❌"
            print(f"   P{qid}: {status} Confidence={confidence:.2f}, Quality={quality:.2f}")

            if is_successful:
                successful_tests += 1
                model_success += 1

            total_tests += 1

        model_performance[model_name] = {
            'success_rate': model_success / model_total if model_total > 0 else 0,
            'successful': model_success,
            'total': model_total
        }

        success_rate = model_success / model_total * 100 if model_total > 0 else 0
        print(f"   Tasa éxito: {success_rate:.1f}% ({model_success}/{model_total})")

    # Resumen global
    global_success_rate = successful_tests / total_tests * 100 if total_tests > 0 else 0
    print(f"\n🏆 RESUMEN GLOBAL:")
    print(f"   Tests totales: {total_tests}")
    print(f"   Tests exitosos: {successful_tests}")
    print(f"   Tasa éxito global: {global_success_rate:.1f}%")

    # Verificar si se cumple el objetivo
    if global_success_rate >= 80:
        print(f"   🎉 OBJETIVO CUMPLIDO: Tasa éxito ≥ 80%")
    else:
        print(f"   ❌ OBJETIVO NO CUMPLIDO: Tasa éxito < 80%")
        print(f"   💡 Se necesitan más optimizaciones")

    # Guardar resultados a archivo
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_file = f"results/enhanced_validation_test_{timestamp}.json"

    # Asegurar que existe el directorio
    os.makedirs("results", exist_ok=True)

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'global_success_rate': global_success_rate,
                'model_performance': model_performance
            },
            'detailed_results': all_results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Resultados guardados en: {results_file}")

def main():
    """Función principal"""
    try:
        results = test_enhanced_validation()
        return results
    except KeyboardInterrupt:
        print("\n⚠️ Test interrumpido por el usuario")
        return None
    except Exception as e:
        print(f"\n❌ Error durante el test: {str(e)}")
        return None

if __name__ == "__main__":
    main()