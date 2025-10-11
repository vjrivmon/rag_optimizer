#!/usr/bin/env python3
"""
🔍 Investigación profunda de la volatilidad en los benchmarks
Analiza por qué ciertas preguntas tienen scores de 0.0 en modelos específicos
"""

import json
import numpy as np
from typing import Dict, List, Any
from collections import defaultdict

def load_latest_benchmark():
    """Carga el benchmark más reciente"""
    import glob
    import os

    # Buscar el benchmark más reciente
    benchmark_files = glob.glob("results/benchmark_*.json")
    benchmark_files.sort(reverse=True)  # Más reciente primero

    if not benchmark_files:
        print("❌ No se encontraron archivos de benchmark")
        return None

    latest_file = benchmark_files[0]
    print(f"📁 Analizando benchmark más reciente: {latest_file}")

    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data, latest_file

def analyze_zero_scores(data: List[Dict]):
    """Analiza sistemáticamente los scores de 0.0"""
    print("\n🚨 ANÁLISIS DE SCORES DE 0.0")
    print("=" * 60)

    zero_score_cases = []

    for record in data:
        combined_score = record.get('metrics', {}).get('combined_score', 0)
        if combined_score == 0.0:
            zero_score_cases.append({
                'question_id': record['question_id'],
                'model_name': record['model_name'],
                'question': record['question'],
                'answer': record.get('answer', ''),
                'answer_length': len(record.get('answer', '')),
                'contexts_count': len(record.get('contexts', [])),
                'generation_time': record.get('generation_time', 0),
                'faithfulness': record.get('metrics', {}).get('faithfulness', 0),
                'answer_relevancy': record.get('metrics', {}).get('answer_relevancy', 0),
                'context_precision': record.get('metrics', {}).get('context_precision', 0),
                'context_recall': record.get('metrics', {}).get('context_recall', 0),
                'answer_correctness': record.get('metrics', {}).get('answer_correctness', 0),
                'answer_similarity': record.get('metrics', {}).get('answer_similarity', 0)
            })

    print(f"📊 Total casos con score 0.0: {len(zero_score_cases)}")

    # Agrupar por pregunta
    questions_with_zeros = defaultdict(list)
    for case in zero_score_cases:
        questions_with_zeros[case['question_id']].append(case)

    # Mostrar preguntas problemáticas
    print(f"\n🎯 Preguntas con más problemas (scores 0.0):")
    for q_id in sorted(questions_with_zeros.keys(), key=lambda x: len(questions_with_zeros[x]), reverse=True):
        cases = questions_with_zeros[q_id]
        print(f"\n  Pregunta {q_id}: {len(cases)} modelos con score 0.0")
        print(f"  Pregunta: '{cases[0]['question']}'")

        for case in cases:
            print(f"    🔸 {case['model_name']}:")
            print(f"       - Respuesta: '{case['answer'][:100]}...'")
            print(f"       - Longitud: {case['answer_length']} caracteres")
            print(f"       - Contextos: {case['contexts_count']}")
            print(f"       - Tiempo: {case['generation_time']:.2f}s")

            # Analizar métricas individuales
            metrics = {
                'faithfulness': case['faithfulness'],
                'answer_relevancy': case['answer_relevancy'],
                'context_precision': case['context_precision'],
                'context_recall': case['context_recall'],
                'answer_correctness': case['answer_correctness'],
                'answer_similarity': case['answer_similarity']
            }

            zero_metrics = [k for k, v in metrics.items() if v == 0.0]
            non_zero_metrics = [f"{k}={v:.3f}" for k, v in metrics.items() if v > 0]

            if zero_metrics:
                print(f"       - Métricas en 0.0: {', '.join(zero_metrics)}")
            if non_zero_metrics:
                print(f"       - Métricas con valor: {', '.join(non_zero_metrics)}")

    return zero_score_cases, questions_with_zeros

def analyze_answer_patterns(zero_cases: List[Dict]):
    """Analiza patrones en las respuestas con score 0.0"""
    print(f"\n📝 PATRONES EN RESPUESTAS CON SCORE 0.0")
    print("=" * 60)

    # Clasificar tipos de problemas
    empty_answers = [case for case in zero_cases if len(case['answer'].strip()) == 0]
    truncated_answers = [case for case in zero_cases if 'truncada' in case['answer'].lower()]
    thinking_only = [case for case in zero_cases if case['answer_length'] < 20 and ('hmm' in case['answer'].lower() or 'let me' in case['answer'].lower())]
    error_messages = [case for case in zero_cases if 'error' in case['answer'].lower() or 'fail' in case['answer'].lower()]
    normal_length = [case for case in zero_cases if case['answer_length'] > 50 and case not in empty_answers + truncated_answers + thinking_only + error_messages]

    print(f"📊 Clasificación de problemas:")
    print(f"  - Respuestas vacías: {len(empty_answers)}")
    print(f"  - Respuestas truncadas: {len(truncated_answers)}")
    print(f"  - Solo thinking tags: {len(thinking_only)}")
    print(f"  - Mensajes de error: {len(error_messages)}")
    print(f"  - Longitud normal pero score 0.0: {len(normal_length)}")

    # Analizar por modelo
    models_with_problems = defaultdict(list)
    for case in zero_cases:
        models_with_problems[case['model_name']].append(case)

    print(f"\n🤖 Problemas por modelo:")
    for model, cases in models_with_problems.items():
        print(f"\n  {model}: {len(cases)} casos con score 0.0")

        for category, category_cases in [
            ("vacías", empty_answers),
            ("truncadas", truncated_answers),
            ("solo thinking", thinking_only),
            ("errores", error_messages),
            ("normales", normal_length)
        ]:
            model_category_cases = [case for case in cases if case in category_cases]
            if model_category_cases:
                print(f"    - {category}: {len(model_category_cases)}")

def investigate_specific_questions():
    """Investiga las preguntas específicas mencionadas por el usuario"""
    print(f"\n🎯 INVESTIGACIÓN DE PREGUNTAS ESPECÍFICAS")
    print("=" * 60)

    # Cargar preguntas originales
    try:
        with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
            questions = {q['id']: q for q in json.load(f)}
    except:
        print("❌ No se pudo cargar el dataset de evaluación")
        return

    # Preguntas mencionadas por el usuario
    target_questions = [1, 8, 10, 12, 13]

    for q_id in target_questions:
        if q_id in questions:
            q_info = questions[q_id]
            print(f"\n📝 Pregunta {q_id} ({q_info['category']} - {q_info['difficulty']}):")
            print(f"  Question: '{q_info['question']}'")
            print(f"  Expected: '{q_info['expected_answer']}'")
            print(f"  Keywords: {q_info['keywords']}")

def analyze_retrieval_vs_generation(zero_cases: List[Dict]):
    """Analiza si los problemas son de retrieval o de generación"""
    print(f"\n🔍 ANÁLISIS: RETRIEVAL vs GENERACIÓN")
    print("=" * 60)

    retrieval_problems = []
    generation_problems = []

    for case in zero_cases:
        # Indicadores de problemas de retrieval
        has_contexts = case['contexts_count'] > 0
        has_answer_content = case['answer_length'] > 20
        has_thinking = 'hmm' in case['answer'].lower() or 'let me' in case['answer'].lower()

        # Si tiene contextos pero no puede generar respuesta buena
        if has_contexts and has_answer_content and not has_thinking:
            generation_problems.append(case)
        # Si no tiene contextos o la respuesta es muy corta
        elif not has_contexts or case['answer_length'] < 20:
            retrieval_problems.append(case)

    print(f"📊 Distribución de problemas:")
    print(f"  - Problemas de retrieval (sin contexto): {len(retrieval_problems)}")
    print(f"  - Problemas de generación (con contexto): {len(generation_problems)}")

    # Mostrar ejemplos
    if retrieval_problems:
        print(f"\n🔍 Ejemplos de problemas de retrieval:")
        for case in retrieval_problems[:3]:
            print(f"  - {case['model_name']} Q{case['question_id']}: {case['contexts_count']} contextos, respuesta de {case['answer_length']} chars")

    if generation_problems:
        print(f"\n💬 Ejemplos de problemas de generación:")
        for case in generation_problems[:3]:
            print(f"  - {case['model_name']} Q{case['question_id']}: {case['contexts_count']} contextos, pero score 0.0")

def analyze_context_quality(zero_cases: List[Dict]):
    """Analiza la calidad de los contextos recuperados"""
    print(f"\n📚 ANÁLISIS DE CALIDAD DE CONTEXTOS")
    print("=" * 60)

    # Agrupar por pregunta para comparar contextos
    questions_contexts = defaultdict(list)
    for case in zero_cases:
        questions_contexts[case['question_id']].append(case)

    for q_id, cases in questions_contexts.items():
        if len(cases) > 1:  # Solo analizar preguntas con múltiples modelos con problemas
            print(f"\n📝 Pregunta {q_id}:")

            for case in cases:
                print(f"  {case['model_name']}:")
                print(f"    - Contextos: {case['contexts_count']}")
                print(f"    - Tiempo retrieval: {case['generation_time']:.2f}s")

                # Analizar métricas de retrieval
                context_metrics = {
                    'context_precision': case['context_precision'],
                    'context_recall': case['context_recall']
                }

                if context_metrics['context_precision'] == 0.0:
                    print(f"    - ⚠️ Context Precision = 0.0 (contextos irrelevantes)")
                if context_metrics['context_recall'] == 0.0:
                    print(f"    - ⚠️ Context Recall = 0.0 (información faltante)")

def generate_recommendations(zero_cases: List[Dict], questions_with_zeros: Dict):
    """Genera recomendaciones específicas basadas en el análisis"""
    print(f"\n💡 RECOMENDACIONES ESPECÍFICAS")
    print("=" * 60)

    # Contar problemas por tipo
    total_cases = len(zero_cases)
    empty_count = len([case for case in zero_cases if len(case['answer'].strip()) == 0])
    truncated_count = len([case for case in zero_cases if 'truncada' in case['answer'].lower()])

    print(f"🎯 Plan de Acción Priorizado:")

    if empty_count > 0:
        print(f"\n1. 🔥 URGENTE - Resolver respuestas vacías ({empty_count} casos)")
        print(f"   - Verificar que clean_thinking_tags() está funcionando")
        print(f"   - Añadir validación post-limpieza")
        print(f"   - Implementar fallback si respuesta vacía")

    if truncated_count > 0:
        print(f"\n2. 🔥 URGENTE - Resolver respuestas truncadas ({truncated_count} casos)")
        print(f"   - La corrección de thinking tags debería resolver esto")
        print(f"   - Testear con Deepseek-R1 específicamente")

    # Recomendaciones por modelo
    models_with_problems = defaultdict(int)
    for case in zero_cases:
        models_with_problems[case['model_name']] += 1

    print(f"\n3. 📊 Optimización por modelo:")
    for model, count in sorted(models_with_problems.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {model}: {count} casos - Investigar patrón específico")

    # Recomendaciones por pregunta
    print(f"\n4. 🎯 Mejoras por pregunta:")
    for q_id, cases in sorted(questions_with_zeros.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        if len(cases) > 2:  # Preguntas con problemas múltiples
            print(f"   - P{q_id}: {len(cases)} modelos afectados - Revisar retrieval para esta pregunta")

def main():
    """Función principal"""
    print("🔍 Investigación Profunda de Volatilidad en Benchmarks")
    print("=" * 70)

    # Cargar datos
    result = load_latest_benchmark()
    if not result:
        return

    data, filename = result

    # Análisis principal
    zero_cases, questions_with_zeros = analyze_zero_scores(data)
    analyze_answer_patterns(zero_cases)
    investigate_specific_questions()
    analyze_retrieval_vs_generation(zero_cases)
    analyze_context_quality(zero_cases)

    # Generar recomendaciones
    generate_recommendations(zero_cases, questions_with_zeros)

    print(f"\n📊 RESUMEN FINAL:")
    print(f"✅ Análisis completado del archivo: {filename}")
    print(f"📈 Total de casos con score 0.0: {len(zero_cases)}")
    print(f"🎯 Preguntas más problemáticas: {len([q for q, cases in questions_with_zeros.items() if len(cases) > 2])}")
    print(f"🤖 Modelos más afectados: {len(set(case['model_name'] for case in zero_cases))}")

if __name__ == "__main__":
    main()