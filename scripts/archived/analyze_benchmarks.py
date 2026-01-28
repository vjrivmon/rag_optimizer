#!/usr/bin/env python3
"""
📊 Análisis Comparativo de Benchmarks RAG v2.0
Compara dos benchmarks para identificar patrones de rendimiento y problemas persistentes
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import numpy as np

def load_benchmark(file_path: str) -> Dict:
    """Carga y valida un archivo de benchmark"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📁 Cargado: {file_path}")
    print(f"📊 Total registros: {len(data)}")

    # Estructurar datos por modelo y pregunta
    structured = defaultdict(lambda: defaultdict(dict))
    for record in data:
        q_id = record['question_id']
        model = record['model_name']
        structured[model][q_id] = record

    return structured

def calculate_model_averages(benchmark_data: Dict) -> Dict[str, Dict[str, float]]:
    """Calcula promedios por modelo para todas las métricas"""
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

def compare_benchmarks(benchmark1_data: Dict, benchmark2_data: Dict) -> Dict:
    """Compara dos benchmarks y calcula diferencias"""
    comparison = {
        'models': {},
        'summary': {},
        'question_analysis': {}
    }

    # Análisis por modelo
    all_models = set(benchmark1_data.keys()) | set(benchmark2_data.keys())

    for model in all_models:
        model1 = benchmark1_data.get(model, {})
        model2 = benchmark2_data.get(model, {})

        stats1 = calculate_model_averages({model: model1})[model] if model1 else None
        stats2 = calculate_model_averages({model: model2})[model] if model2 else None

        comparison['models'][model] = {
            'benchmark1_stats': stats1,
            'benchmark2_stats': stats2,
            'improvements': {}
        }

        if stats1 and stats2:
            for metric in ['avg_faithfulness', 'avg_answer_relevancy', 'avg_context_precision',
                          'avg_context_recall', 'avg_answer_correctness', 'avg_answer_similarity', 'avg_combined_score']:
                val1 = stats1.get(metric, 0)
                val2 = stats2.get(metric, 0)

                improvement = ((val2 - val1) / val1 * 100) if val1 > 0 else 0
                comparison['models'][model]['improvements'][metric] = improvement

    return comparison

def analyze_question_patterns(benchmark1_data: Dict, benchmark2_data: Dict) -> Dict:
    """Analiza patrones a nivel de preguntas"""
    question_analysis = {
        'consistent_failures': [],
        'significant_improvements': [],
        'significant_declines': [],
        'by_category': defaultdict(list)
    }

    # Cargar preguntas originales para contexto
    try:
        with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
            original_questions = {q['id']: q for q in json.load(f)}
    except:
        original_questions = {}

    # Encontrar preguntas comunes
    all_questions = set()
    for model_data in benchmark1_data.values():
        all_questions.update(model_data.keys())
    for model_data in benchmark2_data.values():
        all_questions.update(model_data.keys())

    for q_id in sorted(all_questions):
        question_info = original_questions.get(q_id, {})

        # Analizar rendimiento promedio por pregunta
        scores1 = []
        scores2 = []

        for model in benchmark1_data:
            if q_id in benchmark1_data[model]:
                metrics = benchmark1_data[model][q_id].get('metrics', {})
                scores1.append(metrics.get('combined_score', 0))

        for model in benchmark2_data:
            if q_id in benchmark2_data[model]:
                metrics = benchmark2_data[model][q_id].get('metrics', {})
                scores2.append(metrics.get('combined_score', 0))

        if scores1 and scores2:
            avg1 = np.mean(scores1)
            avg2 = np.mean(scores2)
            improvement = ((avg2 - avg1) / avg1 * 100) if avg1 > 0 else 0

            q_analysis = {
                'question_id': q_id,
                'question': question_info.get('question', f'Question {q_id}'),
                'category': question_info.get('category', 'UNKNOWN'),
                'difficulty': question_info.get('difficulty', 'unknown'),
                'avg_score_b1': avg1,
                'avg_score_b2': avg2,
                'improvement_percent': improvement,
                'scores_b1': scores1,
                'scores_b2': scores2
            }

            # Clasificar según rendimiento
            if avg1 < 0.3 and avg2 < 0.3:
                question_analysis['consistent_failures'].append(q_analysis)
            elif improvement > 15:
                question_analysis['significant_improvements'].append(q_analysis)
            elif improvement < -15:
                question_analysis['significant_declines'].append(q_analysis)

            question_analysis['by_category'][question_info.get('category', 'UNKNOWN')].append(q_analysis)

    return question_analysis

def analyze_specific_answers(benchmark1_data: Dict, benchmark2_data: Dict) -> Dict:
    """Analiza respuestas específicas a preguntas problemáticas"""
    analysis = {
        'problematic_questions': [],
        'answer_patterns': {},
        'citation_analysis': {}
    }

    # Preguntas críticas a revisar
    critical_questions = [2, 4, 6]  # Preguntas problemáticas conocidas

    for q_id in critical_questions:
        q_analysis = {
            'question_id': q_id,
            'benchmark1_answers': {},
            'benchmark2_answers': {},
            'patterns_found': []
        }

        for model_name, questions in benchmark1_data.items():
            if q_id in questions:
                record = questions[q_id]
                q_analysis['benchmark1_answers'][model_name] = {
                    'answer': record.get('answer', ''),
                    'score': record.get('metrics', {}).get('combined_score', 0),
                    'contexts_count': len(record.get('contexts', [])),
                    'has_citations': '[' in record.get('answer', ''),
                    'generation_time': record.get('generation_time', 0)
                }

        for model_name, questions in benchmark2_data.items():
            if q_id in questions:
                record = questions[q_id]
                q_analysis['benchmark2_answers'][model_name] = {
                    'answer': record.get('answer', ''),
                    'score': record.get('metrics', {}).get('combined_score', 0),
                    'contexts_count': len(record.get('contexts', [])),
                    'has_citations': '[' in record.get('answer', ''),
                    'generation_time': record.get('generation_time', 0)
                }

        analysis['problematic_questions'].append(q_analysis)

    return analysis

def generate_report(comparison: Dict, question_analysis: Dict, specific_answers: Dict) -> str:
    """Genera reporte completo de análisis"""
    report = []
    report.append("# 📊 Análisis Comparativo de Benchmarks RAG v2.0")
    report.append(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Resumen Ejecutivo
    report.append("## 🎯 Resumen Ejecutivo")
    report.append("")

    # Calcular mejoras generales
    all_improvements = []
    for model_data in comparison['models'].values():
        if model_data['improvements']:
            all_improvements.append(model_data['improvements'].get('avg_combined_score', 0))

    if all_improvements:
        avg_improvement = np.mean(all_improvements)
        report.append(f"**Mejora promedio del sistema:** {avg_improvement:+.1f}%")

        if avg_improvement > 5:
            report.append("✅ **Sistema mejorando:** Las optimizaciones de RAG v2.0 están mostrando impacto positivo")
        elif avg_improvement < -5:
            report.append("⚠️ **Sistema regresando:** Se necesitan ajustes urgentes en la configuración")
        else:
            report.append("➖ **Sistema estable:** Cambios mínimos en el rendimiento general")

    report.append("")

    # Análisis por Modelo
    report.append("## 🤖 Análisis por Modelo")
    report.append("")

    for model_name, model_data in comparison['models'].items():
        report.append(f"### {model_name}")
        stats2 = model_data['benchmark2_stats']
        if not stats2:
            report.append("- ❌ *Datos no disponibles en benchmark 2*")
            continue

        report.append(f"- **Score promedio:** {stats2.get('avg_combined_score', 0):.3f}")
        report.append(f"- **Tiempo generación:** {stats2.get('avg_generation_times', 0):.1f}s")
        report.append(f"- **Preguntas procesadas:** {stats2.get('total_questions', 0)}")

        # Top y bottom métricas
        metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']
        best_metric = max(metrics, key=lambda m: stats2.get(f'avg_{m}', 0))
        worst_metric = min(metrics, key=lambda m: stats2.get(f'avg_{m}', 0))

        report.append(f"- **Métrica fuerte:** {best_metric} ({stats2.get(f'avg_{best_metric}', 0):.3f})")
        report.append(f"- **Métrica débil:** {worst_metric} ({stats2.get(f'avg_{worst_metric}', 0):.3f})")

        # Mejora respecto a benchmark anterior
        if model_data['improvements'].get('avg_combined_score'):
            improvement = model_data['improvements']['avg_combined_score']
            icon = "📈" if improvement > 5 else "📉" if improvement < -5 else "➖"
            report.append(f"- **Cambio vs anterior:** {icon} {improvement:+.1f}%")

        report.append("")

    # Preguntas Problemáticas
    report.append("## 🚨 Preguntas Problemáticas Crónicas")
    report.append("")

    consistent_failures = sorted(question_analysis['consistent_failures'],
                               key=lambda x: x['avg_score_b2'])[:5]

    if consistent_failures:
        report.append("Las siguientes preguntas siguen fallando consistentemente:")
        report.append("")

        for q in consistent_failures:
            report.append(f"**P{q['question_id']} ({q['category']}):** {q['question']}")
            report.append(f"- Score actual: {q['avg_score_b2']:.3f}")
            report.append(f"- Dificultad: {q['difficulty']}")
            report.append("")
    else:
        report.append("✅ **No hay preguntas crónicamente problemáticas**")
        report.append("")

    # Mejoras Significativas
    if question_analysis['significant_improvements']:
        report.append("## 📈 Preguntas con Mejoras Significativas")
        report.append("")

        for q in sorted(question_analysis['significant_improvements'],
                       key=lambda x: x['improvement_percent'], reverse=True)[:3]:
            report.append(f"**P{q['question_id']}:** {q['question']}")
            report.append(f"- Mejora: {q['improvement_percent']:+.1f}% ({q['avg_score_b1']:.3f} → {q['avg_score_b2']:.3f})")
            report.append("")

    # Análisis Específico de Preguntas Críticas
    report.append("## 🔍 Análisis Detallado de Preguntas Críticas")
    report.append("")

    for q_analysis in specific_answers['problematic_questions']:
        q_id = q_analysis['question_id']
        report.append(f"### Pregunta {q_id}")

        # Comparar respuestas entre benchmarks
        for model in ['gemma2:27b', 'llama3.3:70b', 'deepseek-r1:latest', 'qwen3:32b']:
            if model in q_analysis['benchmark1_answers'] and model in q_analysis['benchmark2_answers']:
                ans1 = q_analysis['benchmark1_answers'][model]
                ans2 = q_analysis['benchmark2_answers'][model]

                improvement = ans2['score'] - ans1['score']
                icon = "📈" if improvement > 0.1 else "📉" if improvement < -0.1 else "➖"

                report.append(f"**{model}:** {icon} {ans1['score']:.3f} → {ans2['score']:.3f}")

                # Analizar calidad de respuesta
                if ans2['has_citations'] and not ans1['has_citations']:
                    report.append("  - ✅ Ahora incluye citas")
                elif not ans2['has_citations'] and ans1['has_citations']:
                    report.append("  - ⚠️ Perdió citas")

                if len(ans2['answer']) > len(ans1['answer']) * 1.5:
                    report.append("  - 📝 Respuesta más detallada")
                elif len(ans2['answer']) < len(ans1['answer']) * 0.7:
                    report.append("  - 📝 Respuesta más concisa")

        report.append("")

    # Patrones por Categoría
    report.append("## 📂 Análisis por Categoría")
    report.append("")

    for category, questions in question_analysis['by_category'].items():
        if category == 'UNKNOWN':
            continue

        avg_scores = [q['avg_score_b2'] for q in questions]
        avg_score = np.mean(avg_scores)

        report.append(f"**{category}:** {avg_score:.3f} promedio ({len(questions)} preguntas)")

        # Encontrar mejor y peor pregunta de la categoría
        best_q = max(questions, key=lambda x: x['avg_score_b2'])
        worst_q = min(questions, key=lambda x: x['avg_score_b2'])

        report.append(f"  - Mejor: P{best_q['question_id']} ({best_q['avg_score_b2']:.3f})")
        report.append(f"  - Peor: P{worst_q['question_id']} ({worst_q['avg_score_b2']:.3f})")
        report.append("")

    # Patrones Identificados
    report.append("## 🔍 Patrones Identificados")
    report.append("")

    # Analizar patrones de fallo
    failure_patterns = []
    for q in question_analysis['consistent_failures']:
        if q['category'] == 'DESAYUNOS' and 'dónde' in q['question'].lower():
            failure_patterns.append("Ubicaciones geográficas específicas")
        elif q['category'] == 'DESAYUNOS' and 'cuándo' in q['question'].lower() or 'cuánto' in q['question'].lower():
            failure_patterns.append("Frecuencias y temporización")
        elif q['category'] == 'REFUERZO' and 'cómo' in q['question'].lower():
            failure_patterns.append("Procesos de inscripción")

    if failure_patterns:
        report.append("**Tipos de información problemática:**")
        for pattern in set(failure_patterns):
            count = failure_patterns.count(pattern)
            report.append(f"- {pattern} ({count} casos)")
        report.append("")

    # Verificar mejoras RAG v2.0
    report.append("## ✅ Efectividad de Mejoras RAG v2.0")
    report.append("")

    # Calcular tasa de citas
    total_with_citations_b2 = 0
    total_answers_b2 = 0

    for q_analysis in specific_answers['problematic_questions']:
        for model, ans_data in q_analysis['benchmark2_answers'].items():
            total_answers_b2 += 1
            if ans_data['has_citations']:
                total_with_citations_b2 += 1

    if total_answers_b2 > 0:
        citation_rate = (total_with_citations_b2 / total_answers_b2) * 100
        report.append(f"**Tasa de citación:** {citation_rate:.1f}% ({total_with_citations_b2}/{total_answers_b2})")

        if citation_rate > 70:
            report.append("✅ **Sistema de citas funcionando bien**")
        elif citation_rate > 40:
            report.append("⚠️ **Sistema de citas parcialmente efectivo**")
        else:
            report.append("❌ **Sistema de citas necesita mejora**")

    report.append("")

    # Plan de Acción
    report.append("## 🎯 Plan de Acción Recomendado")
    report.append("")

    # Quick wins
    report.append("### Quick Wins (1-2 días)")
    report.append("")

    if consistent_failures:
        worst_question = consistent_failures[0]
        if 'dónde' in worst_question['question'].lower() or 'ubicación' in worst_question['question'].lower():
            report.append("- **Mejorar recuperación de ubicaciones:** Añadir entidades geográficas al metadata")
        if 'cuándo' in worst_question['question'].lower() or 'frecuencia' in worst_question['question'].lower():
            report.append("- **Optimizar temporización:** Añadir extractores de fechas/horarios")

    report.append("- **Revisar chunks clave:** Verificar calidad de contexto para preguntas problemáticas")
    report.append("- **Ajustar umbrales:** Optimizar similarity_threshold para recuperación precisa")
    report.append("")

    # Mejoras de Mediano Plazo
    report.append("### Mejoras de Mediano Plazo (1 semana)")
    report.append("")
    report.append("- **Query Expansion mejorada:** Entrenar expansor específico para preguntas problemáticas")
    report.append("- **Reranking especializado:** Priorizar chunks con información específica (lugares, fechas)")
    report.append("- **Self-consistency verification:** Implementar para preguntas críticas")
    report.append("")

    # Optimizaciones de Largo Plazo
    report.append("### Optimizaciones de Largo Plazo (2-3 semanas)")
    report.append("")
    report.append("- **Fine-tuning de modelos:** Entrenar con datos específicos DNI")
    report.append("- **Hierarchical retrieval:** Implementar búsqueda por categorías")
    report.append("- **Knowledge graph:** Construir grafo de relaciones entre conceptos DNI")
    report.append("")

    # Conclusiones
    report.append("## 📝 Conclusiones")
    report.append("")

    if all_improvements and avg_improvement > 0:
        report.append("✅ **Sistema evolucionando positivamente:** Las mejoras de RAG v2.0 están mostrando impacto.")
    elif all_improvements and avg_improvement < -5:
        report.append("⚠️ **Sistema regresando:** Se requiere revisión urgente de configuración.")
    else:
        report.append("➖ **Sistema estable:** Es necesario enfocarse en problemas específicos.")

    if len(consistent_failures) > 3:
        report.append(f"🔍 **Problemas persistentes:** {len(consistent_failures)} preguntas necesitan atención especializada.")
    else:
        report.append("✅ **Buena cobertura:** La mayoría de preguntas están siendo resueltas adecuadamente.")

    report.append("")
    report.append("---")
    report.append(f"*Reporte generado por Sistema de Análisis de Benchmarks RAG v2.0*")

    return "\n".join(report)

def main():
    """Función principal de análisis"""
    print("🚀 Iniciando análisis comparativo de benchmarks...")

    # Archivos a analizar
    benchmark1_path = "results/benchmark_20251010_195254.json"
    benchmark2_path = "results/benchmark_20251010_224326.json"

    # Validar archivos
    if not os.path.exists(benchmark1_path):
        print(f"❌ No se encuentra: {benchmark1_path}")
        return

    if not os.path.exists(benchmark2_path):
        print(f"❌ No se encuentra: {benchmark2_path}")
        return

    print(f"📊 Analizando:")
    print(f"  - Benchmark 1: {benchmark1_path}")
    print(f"  - Benchmark 2: {benchmark2_path}")
    print("")

    # Cargar datos
    benchmark1_data = load_benchmark(benchmark1_path)
    benchmark2_data = load_benchmark(benchmark2_path)

    # Realizar análisis
    print("🔍 Realizando análisis comparativo...")
    comparison = compare_benchmarks(benchmark1_data, benchmark2_data)
    question_analysis = analyze_question_patterns(benchmark1_data, benchmark2_data)
    specific_answers = analyze_specific_answers(benchmark1_data, benchmark2_data)

    # Generar reporte
    print("📝 Generando reporte...")
    report = generate_report(comparison, question_analysis, specific_answers)

    # Guardar reporte
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"results/comparative_analysis_{timestamp}.md"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ Análisis completado!")
    print(f"📄 Reporte guardado en: {report_path}")
    print("")

    # Mostrar resumen rápido
    print("📊 Resumen Rápido:")
    for model_name, model_data in comparison['models'].items():
        if model_data['improvements'].get('avg_combined_score'):
            improvement = model_data['improvements']['avg_combined_score']
            icon = "📈" if improvement > 5 else "📉" if improvement < -5 else "➖"
            print(f"  {model_name}: {icon} {improvement:+.1f}%")

    failures = len(question_analysis['consistent_failures'])
    improvements = len(question_analysis['significant_improvements'])

    print(f"  Preguntas crónicas: {failures}")
    print(f"  Mejoras significativas: {improvements}")

    if failures > 0:
        print("\n🚨 Preguntas que necesitan atención:")
        for q in sorted(question_analysis['consistent_failures'], key=lambda x: x['avg_score_b2'])[:3]:
            print(f"  - P{q['question_id']}: {q['question']} (Score: {q['avg_score_b2']:.3f})")

if __name__ == "__main__":
    main()