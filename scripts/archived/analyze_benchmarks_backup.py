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

def calculate_model_averages(models_data: Dict[str, List[Dict]]) -> Dict[str, Dict[str, float]]:
    """Calculate average metrics for each model."""
    model_averages = {}

    for model_name, entries in models_data.items():
        metrics = {
            'faithfulness': [],
            'answer_relevancy': [],
            'context_precision': [],
            'context_recall': [],
            'answer_correctness': [],
            'answer_similarity': [],
            'combined_score': [],
            'generation_time': []
        }

        for entry in entries:
            entry_metrics = entry['metrics']
            for metric in metrics:
                if metric == 'generation_time':
                    metrics[metric].append(entry['generation_time'])
                else:
                    metrics[metric].append(entry_metrics[metric])

        # Calculate averages
        model_averages[model_name] = {}
        for metric, values in metrics.items():
            if values:
                model_averages[model_name][f'avg_{metric}'] = statistics.mean(values)
                model_averages[model_name][f'std_{metric}'] = statistics.stdev(values) if len(values) > 1 else 0.0
                model_averages[model_name][f'min_{metric}'] = min(values)
                model_averages[model_name][f'max_{metric}'] = max(values)

        model_averages[model_name]['total_entries'] = len(entries)

    return model_averages

def calculate_question_averages(questions_data: Dict[int, List[Dict]]) -> Dict[int, Dict[str, float]]:
    """Calculate average metrics for each question."""
    question_averages = {}

    for question_id, entries in questions_data.items():
        metrics = {
            'faithfulness': [],
            'answer_relevancy': [],
            'context_precision': [],
            'context_recall': [],
            'answer_correctness': [],
            'answer_similarity': [],
            'combined_score': []
        }

        for entry in entries:
            entry_metrics = entry['metrics']
            for metric in metrics:
                metrics[metric].append(entry_metrics[metric])

        # Calculate averages
        question_averages[question_id] = {}
        for metric, values in metrics.items():
            if values:
                question_averages[question_id][f'avg_{metric}'] = statistics.mean(values)
                question_averages[question_id][f'std_{metric}'] = statistics.stdev(values) if len(values) > 1 else 0.0

        question_averages[question_id]['total_entries'] = len(entries)

    return question_averages

def identify_problematic_questions(questions_data: Dict[int, List[Dict]], threshold: float = 0.5) -> List[Tuple[int, float, str]]:
    """Identify questions with consistently low scores."""
    problematic = []

    for question_id, entries in questions_data.items():
        avg_scores = [entry['metrics']['combined_score'] for entry in entries]
        avg_score = statistics.mean(avg_scores)

        if avg_score < threshold:
            # Find which model performed worst
            worst_entry = min(entries, key=lambda x: x['metrics']['combined_score'])
            problematic.append((question_id, avg_score, worst_entry['model_name']))

    return sorted(problematic, key=lambda x: x[1])

def analyze_generation_patterns(data: List[Dict]) -> Dict[str, Any]:
    """Analyze generation time patterns."""
    generation_times = {}

    for entry in data:
        model = entry['model_name']
        if model not in generation_times:
            generation_times[model] = []
        generation_times[model].append(entry['generation_time'])

    analysis = {}
    for model, times in generation_times.items():
        analysis[model] = {
            'avg_time': statistics.mean(times),
            'std_time': statistics.stdev(times) if len(times) > 1 else 0.0,
            'min_time': min(times),
            'max_time': max(times),
            'total_entries': len(times)
        }

    return analysis

def compare_benchmarks(file1_data: List[Dict], file2_data: List[Dict]) -> Dict[str, Any]:
    """Compare two benchmark files and identify improvements/regressions."""
    comparison = {
        'improvements': [],
        'regressions': [],
        'model_changes': {},
        'question_changes': {}
    }

    # Group by model and question for comparison
    file1_by_model_question = {}
    file2_by_model_question = {}

    for entry in file1_data:
        key = (entry['model_name'], entry['question_id'])
        file1_by_model_question[key] = entry

    for entry in file2_data:
        key = (entry['model_name'], entry['question_id'])
        file2_by_model_question[key] = entry

    # Compare common entries
    common_keys = set(file1_by_model_question.keys()) & set(file2_by_model_question.keys())

    for key in common_keys:
        file1_score = file1_by_model_question[key]['metrics']['combined_score']
        file2_score = file2_by_model_question[key]['metrics']['combined_score']

        if file2_score > file1_score + 0.05:  # Significant improvement
            comparison['improvements'].append({
                'model': key[0],
                'question_id': key[1],
                'file1_score': file1_score,
                'file2_score': file2_score,
                'improvement': file2_score - file1_score
            })
        elif file2_score < file1_score - 0.05:  # Significant regression
            comparison['regressions'].append({
                'model': key[0],
                'question_id': key[1],
                'file1_score': file1_score,
                'file2_score': file2_score,
                'regression': file1_score - file2_score
            })

    return comparison

def generate_insights(model_averages: Dict, question_averages: Dict,
                     problematic_questions: List, generation_analysis: Dict,
                     comparison: Dict) -> Dict[str, Any]:
    """Generate key insights from the analysis."""
    insights = {
        'best_performing_model': None,
        'worst_performing_model': None,
        'most_difficult_questions': [],
        'fastest_model': None,
        'slowest_model': None,
        'key_recommendations': []
    }

    # Find best and worst performing models
    model_scores = {model: data['avg_combined_score'] for model, data in model_averages.items()}
    if model_scores:
        insights['best_performing_model'] = max(model_scores.items(), key=lambda x: x[1])
        insights['worst_performing_model'] = min(model_scores.items(), key=lambda x: x[1])

    # Find most difficult questions
    question_scores = {qid: data['avg_combined_score'] for qid, data in question_averages.items()}
    if question_scores:
        sorted_questions = sorted(question_scores.items(), key=lambda x: x[1])
        insights['most_difficult_questions'] = sorted_questions[:5]

    # Find fastest and slowest models
    model_times = {model: data['avg_time'] for model, data in generation_analysis.items()}
    if model_times:
        insights['fastest_model'] = min(model_times.items(), key=lambda x: x[1])
        insights['slowest_model'] = max(model_times.items(), key=lambda x: x[1])

    # Generate recommendations
    insights['key_recommendations'] = generate_recommendations(
        model_averages, problematic_questions, comparison
    )

    return insights

def generate_recommendations(model_averages: Dict, problematic_questions: List, comparison: Dict) -> List[str]:
    """Generate specific recommendations based on analysis."""
    recommendations = []

    # Model-specific recommendations
    for model, data in model_averages.items():
        if data['avg_combined_score'] < 0.6:
            recommendations.append(f"Consider optimizing parameters for {model} (avg score: {data['avg_combined_score']:.3f})")

        if data['avg_context_recall'] < 0.7:
            recommendations.append(f"Improve context retrieval for {model} (context recall: {data['avg_context_recall']:.3f})")

    # Question-specific recommendations
    if problematic_questions:
        worst_question = problematic_questions[0]
        recommendations.append(f"Focus on Question {worst_question[0]} (avg score: {worst_question[1]:.3f}) - may need better context or query expansion")

    # System-level recommendations
    if comparison['improvements']:
        recommendations.append(f"System shows {len(comparison['improvements'])} improvements - identify what changed")

    if comparison['regressions']:
        recommendations.append(f"System shows {len(comparison['regressions'])} regressions - investigate causes")

    return recommendations

def print_analysis_summary(model_averages: Dict, question_averages: Dict,
                          problematic_questions: List, generation_analysis: Dict,
                          insights: Dict, comparison: Dict):
    """Print a comprehensive analysis summary."""
    print("="*80)
    print("RAG v2.0 BENCHMARK ANALYSIS SUMMARY")
    print("="*80)

    print("\n📊 MODEL PERFORMANCE ANALYSIS")
    print("-" * 50)
    for model, data in sorted(model_averages.items(), key=lambda x: x[1]['avg_combined_score'], reverse=True):
        print(f"\n{model}:")
        print(f"  Combined Score: {data['avg_combined_score']:.3f} ± {data['std_combined_score']:.3f}")
        print(f"  Faithfulness: {data['avg_faithfulness']:.3f}")
        print(f"  Answer Relevancy: {data['avg_answer_relevancy']:.3f}")
        print(f"  Context Precision: {data['avg_context_precision']:.3f}")
        print(f"  Context Recall: {data['avg_context_recall']:.3f}")
        print(f"  Answer Correctness: {data['avg_answer_correctness']:.3f}")
        print(f"  Answer Similarity: {data['avg_answer_similarity']:.3f}")

    print("\n⏱️  GENERATION TIME ANALYSIS")
    print("-" * 50)
    for model, data in sorted(generation_analysis.items(), key=lambda x: x[1]['avg_time']):
        print(f"{model}: {data['avg_time']:.1f}s ± {data['std_time']:.1f}s (min: {data['min_time']:.1f}s, max: {data['max_time']:.1f}s)")

    print("\n❌ PROBLEMATIC QUESTIONS (Score < 0.5)")
    print("-" * 50)
    for qid, avg_score, worst_model in problematic_questions:
        print(f"Question {qid}: avg score {avg_score:.3f} (worst: {worst_model})")

    print("\n🎯 KEY INSIGHTS")
    print("-" * 50)
    if insights['best_performing_model']:
        print(f"Best Model: {insights['best_performing_model'][0]} (score: {insights['best_performing_model'][1]:.3f})")
    if insights['worst_performing_model']:
        print(f"Worst Model: {insights['worst_performing_model'][0]} (score: {insights['worst_performing_model'][1]:.3f})")
    if insights['fastest_model']:
        print(f"Fastest Model: {insights['fastest_model'][0]} ({insights['fastest_model'][1]:.1f}s)")
    if insights['slowest_model']:
        print(f"Slowest Model: {insights['slowest_model'][0]} ({insights['slowest_model'][1]:.1f}s)")

    print("\n📈 MOST DIFFICULT QUESTIONS")
    print("-" * 50)
    for qid, avg_score in insights['most_difficult_questions']:
        print(f"Question {qid}: avg score {avg_score:.3f}")

    print("\n💡 KEY RECOMMENDATIONS")
    print("-" * 50)
    for i, rec in enumerate(insights['key_recommendations'], 1):
        print(f"{i}. {rec}")

    print("\n🔄 BENCHMARK COMPARISON")
    print("-" * 50)
    print(f"Improvements: {len(comparison['improvements'])}")
    print(f"Regressions: {len(comparison['regressions'])}")

    if comparison['improvements']:
        print("\nTop 5 Improvements:")
        for imp in sorted(comparison['improvements'], key=lambda x: x['improvement'], reverse=True)[:5]:
            print(f"  {imp['model']} Q{imp['question_id']}: {imp['file1_score']:.3f} → {imp['file2_score']:.3f} (+{imp['improvement']:.3f})")

    if comparison['regressions']:
        print("\nTop 5 Regressions:")
        for reg in sorted(comparison['regressions'], key=lambda x: x['regression'], reverse=True)[:5]:
            print(f"  {reg['model']} Q{reg['question_id']}: {reg['file1_score']:.3f} → {reg['file2_score']:.3f} (-{reg['regression']:.3f})")

def main():
    """Main analysis function."""
    file1 = "/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer/results/benchmark_20251010_215005.json"
    file2 = "/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer/results/benchmark_20251010_224326.json"

    print("Loading benchmark data...")
    file1_data = load_benchmark_data(file1)
    file2_data = load_benchmark_data(file2)

    print(f"File 1: {len(file1_data)} entries")
    print(f"File 2: {len(file2_data)} entries")

    # Analyze file 2 (latest)
    print("\nAnalyzing latest benchmark...")
    models_data = extract_metrics_by_model(file2_data)
    questions_data = extract_metrics_by_question(file2_data)

    model_averages = calculate_model_averages(models_data)
    question_averages = calculate_question_averages(questions_data)
    problematic_questions = identify_problematic_questions(questions_data)
    generation_analysis = analyze_generation_patterns(file2_data)

    # Compare benchmarks
    print("Comparing benchmarks...")
    comparison = compare_benchmarks(file1_data, file2_data)

    # Generate insights
    insights = generate_insights(model_averages, question_averages,
                                problematic_questions, generation_analysis, comparison)

    # Print summary
    print_analysis_summary(model_averages, question_averages,
                          problematic_questions, generation_analysis,
                          insights, comparison)

    # Save detailed analysis
    output_file = "/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer/benchmark_analysis_results.json"
    results = {
        'file_analyzed': file2,
        'model_averages': model_averages,
        'question_averages': question_averages,
        'problematic_questions': problematic_questions,
        'generation_analysis': generation_analysis,
        'insights': insights,
        'benchmark_comparison': comparison,
        'analysis_timestamp': pd.Timestamp.now().isoformat()
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Detailed analysis saved to: {output_file}")

if __name__ == "__main__":
    main()