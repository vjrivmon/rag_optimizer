#!/usr/bin/env python3
"""
📊 Análisis Comparativo de 3 Benchmarks RAG v2.0
Compara benchmark_195254, benchmark_224326, y benchmark_000329 para identificar patrones y problemas
"""

import json
import os
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

def load_benchmark(file_path: str) -> Dict:
    """Carga y estructura datos del benchmark"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📁 Cargado: {os.path.basename(file_path)}")
    print(f"📊 Total registros: {len(data)}")

    # Estructurar datos por modelo y pregunta
    structured = defaultdict(lambda: defaultdict(dict))
    for record in data:
        q_id = record['question_id']
        model = record['model_name']
        structured[model][q_id] = record

    return structured

def calculate_model_averages(benchmark_data: Dict) -> Dict[str, Dict[str, float]]:
    """Calcula promedios por modelo"""
    model_stats = {}

    for model_name, questions in benchmark_data.items():
        stats = {
            'total_questions': len(questions),
            'generation_times': [],
            'faithfulness': [],
            'answer_relevancy': [],
            'context_precision': [],
            'context_recall': [],
            'answer_correctness': [],
            'answer_similarity': [],
            'combined_score': []
        }

        for q_id, record in questions.items():
            metrics = record.get('metrics', {})
            stats['generation_times'].append(record.get('generation_time', 0))

            for metric in ['faithfulness', 'answer_relevancy', 'context_precision',
                          'context_recall', 'answer_correctness', 'answer_similarity', 'combined_score']:
                stats[metric].append(metrics.get(metric, 0))

        # Calcular promedios
        for key in ['generation_times'] + list(stats.keys())[1:]:
            if key == 'total_questions':
                continue
            values = stats[key]
            stats[f'avg_{key}'] = np.mean(values) if values else 0
            stats[f'std_{key}'] = np.std(values) if values else 0
            stats[f'min_{key}'] = np.min(values) if values else 0
            stats[f'max_{key}'] = np.max(values) if values else 0

        model_stats[model_name] = stats

    return model_stats

def detect_answer_issues(benchmark_data: Dict) -> Dict[str, List]:
    """Detecta problemas en las respuestas"""
    issues = {
        'truncated_answers': [],
        'empty_answers': [],
        'only_thinking': [],
        'too_short': [],
        'too_long': []
    }

    for model_name, questions in benchmark_data.items():
        for q_id, record in questions.items():
            answer = record.get('answer', '')

            # Detectar problemas específicos
            if 'truncada' in answer.lower():
                issues['truncated_answers'].append((model_name, q_id, answer[:100]))

            if not answer or answer.strip() == '':
                issues['empty_answers'].append((model_name, q_id))

            if 'thinking' in answer.lower() and len(answer) < 200:
                issues['only_thinking'].append((model_name, q_id, answer[:100]))

            if len(answer) < 50:
                issues['too_short'].append((model_name, q_id, len(answer)))

            if len(answer) > 2000:
                issues['too_long'].append((model_name, q_id, len(answer)))

    return issues

def analyze_answer_quality(benchmark_data: Dict, benchmark_name: str) -> Dict:
    """Analiza la calidad de las respuestas"""
    quality_analysis = {
        'benchmark_name': benchmark_name,
        'model_analysis': {},
        'total_issues': 0,
        'problematic_models': []
    }

    # Detectar problemas
    issues = detect_answer_issues(benchmark_data)
    quality_analysis.update(issues)
    quality_analysis['total_issues'] = sum(len(issue_list) for issue_list in issues.values())

    # Análisis por modelo
    for model_name, questions in benchmark_data.items():
        model_issues = {
            'total_questions': len(questions),
            'truncated_count': 0,
            'empty_count': 0,
            'thinking_only_count': 0,
            'avg_score': 0,
            'generation_times': []
        }

        # Contar problemas y calcular métricas
        scores = []
        for q_id, record in questions.items():
            answer = record.get('answer', '')
            metrics = record.get('metrics', {})

            # Contar problemas
            if 'truncada' in answer.lower():
                model_issues['truncated_count'] += 1
            if not answer or answer.strip() == '':
                model_issues['empty_count'] += 1
            if 'thinking' in answer.lower() and len(answer) < 200:
                model_issues['thinking_only_count'] += 1

            # Recolectar scores y tiempos
            scores.append(metrics.get('combined_score', 0))
            model_issues['generation_times'].append(record.get('generation_time', 0))

        model_issues['avg_score'] = np.mean(scores) if scores else 0
        model_issues['avg_generation_time'] = np.mean(model_issues['generation_times']) if model_issues['generation_times'] else 0

        # Calcular porcentaje de problemas
        total_problems = model_issues['truncated_count'] + model_issues['empty_count'] + model_issues['thinking_only_count']
        model_issues['problem_percentage'] = (total_problems / model_issues['total_questions']) * 100 if model_issues['total_questions'] > 0 else 0

        if model_issues['problem_percentage'] > 10:  # Más del 10% de problemas
            quality_analysis['problematic_models'].append({
                'model': model_name,
                'problem_percentage': model_issues['problem_percentage'],
                'issues': {
                    'truncated': model_issues['truncated_count'],
                    'empty': model_issues['empty_count'],
                    'thinking_only': model_issues['thinking_only_count']
                }
            })

        quality_analysis['model_analysis'][model_name] = model_issues

    return quality_analysis

def compare_three_benchmarks():
    """Compara los tres benchmarks"""
    print("🚀 Análisis Comparativo de 3 Benchmarks RAG v2.0")
    print("=" * 70)

    # Archivos a analizar
    benchmarks = [
        ("results/benchmark_20251010_195254.json", "Benchmark 1 (19:52)"),
        ("results/benchmark_20251010_224326.json", "Benchmark 2 (22:43)"),
        ("results/benchmark_20251011_000329.json", "Benchmark 3 (00:03)")
    ]

    results = {}

    for file_path, name in benchmarks:
        if not os.path.exists(file_path):
            print(f"❌ No se encuentra: {file_path}")
            continue

        print(f"\n📊 Analizando: {name}")
        print("-" * 50)

        # Cargar datos
        benchmark_data = load_benchmark(file_path)

        # Calcular estadísticas
        model_averages = calculate_model_averages(benchmark_data)
        quality_analysis = analyze_answer_quality(benchmark_data, name)

        results[name] = {
            'model_averages': model_averages,
            'quality_analysis': quality_analysis
        }

        # Mostrar resumen rápido
        print("Model Performance Summary:")
        for model_name, stats in model_averages.items():
            avg_score = stats.get('avg_combined_score', 0)
            avg_time = stats.get('avg_generation_times', 0)
            problem_pct = quality_analysis['model_analysis'].get(model_name, {}).get('problem_percentage', 0)

            status = "🟢" if problem_pct == 0 else "🟡" if problem_pct < 20 else "🔴"
            print(f"  {status} {model_name}: Score={avg_score:.3f}, Time={avg_time:.1f}s, Problems={problem_pct:.1f}%")

        # Mostrar modelos problemáticos
        if quality_analysis['problematic_models']:
            print(f"\n⚠️ Modelos Problemáticos:")
            for model_info in quality_analysis['problematic_models']:
                print(f"  - {model_info['model']}: {model_info['problem_percentage']:.1f}% problemas")
                for issue_type, count in model_info['issues'].items():
                    if count > 0:
                        print(f"    * {issue_type}: {count}")

    return results

def identify_trends(results: Dict):
    """Identifica tendencias y cambios entre benchmarks"""
    print(f"\n" + "=" * 70)
    print("🔍 ANÁLISIS DE TENDENCIAS")
    print("=" * 70)

    # Extraer datos de cada benchmark
    benchmark_names = list(results.keys())

    # Analizar cambios por modelo
    models = ['deepseek-r1:latest', 'gemma2:27b', 'llama3.3:70b', 'qwen3:32b']

    print("\n📈 Evolución por Modelo:")
    print("-" * 50)

    for model in models:
        print(f"\n🤖 {model}:")

        scores_across_benchmarks = []
        problems_across_benchmarks = []

        for benchmark_name in benchmark_names:
            model_stats = results[benchmark_name]['model_averages'].get(model, {})
            quality_stats = results[benchmark_name]['quality_analysis']['model_analysis'].get(model, {})

            score = model_stats.get('avg_combined_score', 0)
            problems = quality_stats.get('problem_percentage', 0)

            scores_across_benchmarks.append(score)
            problems_across_benchmarks.append(problems)

            short_name = benchmark_name.split('(')[1].strip(')')
            status = "✅" if problems == 0 else "⚠️" if problems < 20 else "❌"
            print(f"  {status} {short_name}: Score={score:.3f}, Problems={problems:.1f}%")

        # Detectar cambios dramáticos
        if len(scores_across_benchmarks) >= 2:
            last_score = scores_across_benchmarks[-1]
            prev_score = scores_across_benchmarks[-2]
            score_change = last_score - prev_score

            last_problems = problems_across_benchmarks[-1]
            prev_problems = problems_across_benchmarks[-2]
            problem_change = last_problems - prev_problems

            # Cambios significativos
            if abs(score_change) > 0.2:
                trend = "📈" if score_change > 0 else "📉"
                print(f"  {trend} Cambio dramático: {score_change:+.3f} puntos")

            if problem_change > 30:
                print(f"  🚨 Aumento masivo de problemas: +{problem_change:.1f}%")
            elif problem_change < -30:
                print(f"  ✅ Mejora masiva de problemas: {problem_change:+.1f}%")

    # Identificar el problema principal del último benchmark
    print(f"\n🚨 PROBLEMAS CRÍTICOS IDENTIFICADOS:")
    last_benchmark = benchmark_names[-1]
    last_quality = results[last_benchmark]['quality_analysis']

    if last_quality['problematic_models']:
        print(f"\nEn {last_benchmark}:")
        for model_info in last_quality['problematic_models']:
            model_name = model_info['model']
            print(f"\n  🤖 {model_name}:")
            print(f"    📊 Porcentaje de problemas: {model_info['problem_percentage']:.1f}%")

            # Detallar problemas
            for issue_type, count in model_info['issues'].items():
                if count > 0:
                    print(f"      - {issue_type}: {count} respuestas")

            # Mostrar ejemplos si hay truncadas
            if model_info['issues']['truncated'] > 0:
                print(f"      📝 Ejemplo de respuesta truncada:")
                for issue in last_quality['truncated_answers']:
                    if issue[0] == model_name:
                        print(f"        P{issue[1]}: {issue[2]}...")
                        break

def generate_recommendations(results: Dict):
    """Genera recomendaciones basadas en el análisis"""
    print(f"\n" + "=" * 70)
    print("💡 RECOMENDACIONES ESPECÍFICAS")
    print("=" * 70)

    last_benchmark = list(results.keys())[-1]
    last_quality = results[last_benchmark]['quality_analysis']

    # Recomendaciones por problema
    recommendations = []

    if last_quality['truncated_answers']:
        recommendations.append({
            'priority': '🔥 CRÍTICA',
            'problem': 'Respuestas truncadas de Deepseek-R1',
            'description': f'{len(last_quality["truncated_answers"])} respuestas están truncadas, probablemente por limpieza incorrecta de thinking tags',
            'solution': 'Arreglar la función clean_thinking_tags() para que preserve el contenido real de las respuestas',
            'code_location': 'benchmark_v2.py líneas 62-94'
        })

    if last_quality['only_thinking']:
        recommendations.append({
            'priority': '🔥 CRÍTICA',
            'problem': 'Respuestas con solo thinking tags',
            'description': f'{len(last_quality["only_thinking"])} respuestas contienen únicamente etiquetas de razonamiento',
            'solution': 'Mejorar el patrón de regex para detectar y eliminar thinking tags sin eliminar el contenido',
            'code_location': 'benchmark_v2.py líneas 84-91'
        })

    # Recomendaciones de optimización
    benchmark_names = list(results.keys())
    if len(benchmark_names) >= 2:
        # Comparar rendimiento entre benchmarks
        first_benchmark = benchmark_names[0]
        last_benchmark = benchmark_names[-1]

        print(f"\n🎯 ANÁLISIS DE OPTIMIZACIÓN:")
        print(f"Comparando {first_benchmark} vs {last_benchmark}")
        print("-" * 50)

        models = ['deepseek-r1:latest', 'gemma2:27b', 'llama3.3:70b', 'qwen3:32b']

        for model in models:
            first_score = results[first_benchmark]['model_averages'].get(model, {}).get('avg_combined_score', 0)
            last_score = results[last_benchmark]['model_averages'].get(model, {}).get('avg_combined_score', 0)

            change = last_score - first_score

            if change > 0.1:
                print(f"  ✅ {model}: +{change:.3f} (mejora)")
            elif change < -0.1:
                print(f"  ❌ {model}: {change:.3f} (empeoró)")
            else:
                print(f"  ➖ {model}: {change:+.3f} (estable)")

    # Mostrar recomendaciones
    print(f"\n📋 PLAN DE ACCIÓN PRIORIZADO:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['priority']} - {rec['problem']}")
        print(f"   📝 Descripción: {rec['description']}")
        print(f"   💡 Solución: {rec['solution']}")
        print(f"   📍 Ubicación: {rec['code_location']}")

    # Recomendaciones adicionales
    print(f"\n🔧 MEJORAS ADICIONALES SUGERIDAS:")
    print("1. Implementar validación de respuestas después de la limpieza de tags")
    print("2. Añadir fallback si una respuesta queda vacía después de limpieza")
    print("3. Crear sistema de monitoreo que detecte automáticamente这些问题")
    print("4. Optimizar parámetros de temperatura para cada modelo específicamente")

def main():
    """Función principal"""
    print("🚀 Iniciando análisis comparativo de 3 benchmarks...")

    # Analizar benchmarks
    results = compare_three_benchmarks()

    # Identificar tendencias
    identify_trends(results)

    # Generar recomendaciones
    generate_recommendations(results)

    # Guardar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"results/three_benchmark_analysis_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Análisis completo guardado en: {output_file}")
    print(f"\n🎯 RESUMEN EJECUTIVO:")
    print("El último benchmark muestra problemas críticos con Deepseek-R1 debido a limpieza incorrecta de thinking tags.")
    print("Esto causa que todas las métricas del modelo sean 0.0, afectando drásticamente el rendimiento general.")
    print("Se requiere corrección urgente de la función clean_thinking_tags().")

if __name__ == "__main__":
    main()