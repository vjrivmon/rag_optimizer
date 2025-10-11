#!/usr/bin/env python3
"""
Fase 1: Análisis técnico detallado de problemas en el benchmark
Analiza timeouts, retrieval, y métricas de generación por modelo
"""

import json
import time
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import statistics
from pathlib import Path

class BenchmarkAnalyzer:
    def __init__(self, benchmark_file: str):
        self.benchmark_file = Path(benchmark_file)
        self.data = self.load_benchmark_data()

    def load_benchmark_data(self) -> List[Dict]:
        """Carga datos del benchmark"""
        with open(self.benchmark_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze_timeouts_and_truncations(self) -> Dict[str, Any]:
        """Analiza timeouts y truncamientos por modelo"""
        print("🔍 Analizando timeouts y truncaciones...")

        model_stats = defaultdict(lambda: {
            'total_questions': 0,
            'truncated_responses': 0,
            'no_info_responses': 0,
            'generation_times': [],
            'avg_generation_time': 0,
            'max_generation_time': 0,
            'timeout_suspects': []
        })

        for item in self.data:
            model = item['model_name']
            question_id = item['question_id']
            answer = item.get('answer', '')
            gen_time = item.get('generation_time', 0)

            stats = model_stats[model]
            stats['total_questions'] += 1
            stats['generation_times'].append(gen_time)

            # Detectar truncamientos
            if '[Respuesta truncada' in answer or len(answer) < 50:
                stats['truncated_responses'] += 1
                stats['timeout_suspects'].append({
                    'question_id': question_id,
                    'generation_time': gen_time,
                    'answer_length': len(answer),
                    'answer_preview': answer[:100]
                })

            # Detectar "No tengo información"
            if 'no tengo esa información' in answer.lower():
                stats['no_info_responses'] += 1

        # Calcular estadísticas
        for model, stats in model_stats.items():
            times = stats['generation_times']
            stats['avg_generation_time'] = statistics.mean(times) if times else 0
            stats['max_generation_time'] = max(times) if times else 0

            # Detectar sospechosos de timeout (>100s)
            stats['timeout_suspects'].extend([
                item for item in self.data
                if item['model_name'] == model and item.get('generation_time', 0) > 100
            ])

        return dict(model_stats)

    def analyze_question_difficulty(self) -> Dict[int, Dict]:
        """Analiza dificultad por pregunta"""
        print("📊 Analizando dificultad por pregunta...")

        question_stats = defaultdict(lambda: {
            'avg_score': 0,
            'scores': [],
            'failed_models': [],
            'successful_models': [],
            'model_scores': {},
            'question_text': '',
            'category': ''
        })

        for item in self.data:
            q_id = item['question_id']
            model = item['model_name']
            score = item.get('metrics', {}).get('combined_score', 0)

            stats = question_stats[q_id]
            stats['scores'].append(score)
            stats['model_scores'][model] = score
            stats['question_text'] = item.get('question', '')

            if score < 0.5:  # Consideramos fallo si score < 0.5
                stats['failed_models'].append(model)
            else:
                stats['successful_models'].append(model)

        # Calcular promedios y categorizar
        for q_id, stats in question_stats.items():
            scores = stats['scores']
            stats['avg_score'] = statistics.mean(scores) if scores else 0

            # Categorizar dificultad
            if stats['avg_score'] >= 0.8:
                stats['difficulty'] = 'easy'
            elif stats['avg_score'] >= 0.6:
                stats['difficulty'] = 'medium'
            else:
                stats['difficulty'] = 'hard'

        return dict(question_stats)

    def analyze_retrieval_quality(self) -> Dict[str, Any]:
        """Analiza calidad de retrieval por pregunta y modelo"""
        print("🔍 Analizando calidad de retrieval...")

        retrieval_issues = []

        for item in self.data:
            q_id = item['question_id']
            model = item['model_name']
            answer = item.get('answer', '')
            contexts = item.get('contexts', [])
            score = item.get('metrics', {}).get('combined_score', 0)

            # Casos problemáticos
            issue = {
                'question_id': q_id,
                'model': model,
                'score': score,
                'answer_length': len(answer),
                'num_contexts': len(contexts),
                'contexts_preview': [c[:100] + '...' if len(c) > 100 else c for c in contexts[:3]],
                'has_info_in_contexts': False,
                'uses_context_info': False,
                'issue_type': ''
            }

            # Verificar si hay info relevante en contexts
            relevant_keywords = self.get_relevant_keywords_for_question(q_id)
            issue['has_info_in_contexts'] = any(
                any(keyword.lower() in context.lower() for keyword in relevant_keywords)
                for context in contexts
            )

            # Verificar si la respuesta usa info de los contexts
            issue['uses_context_info'] = any(
                any(keyword.lower() in answer.lower() for keyword in relevant_keywords)
                for keyword in relevant_keywords
            )

            # Clasificar tipo de problema
            if 'no tengo esa información' in answer.lower() and issue['has_info_in_contexts']:
                issue['issue_type'] = 'info_available_not_used'
            elif '[Respuesta truncada' in answer:
                issue['issue_type'] = 'timeout_truncation'
            elif score < 0.3 and issue['has_info_in_contexts']:
                issue['issue_type'] = 'low_score_with_info'
            elif not issue['has_info_in_contexts']:
                issue['issue_type'] = 'poor_retrieval'

            if issue['issue_type']:
                retrieval_issues.append(issue)

        return {
            'total_issues': len(retrieval_issues),
            'issues_by_type': defaultdict(list),
            'issues_by_question': defaultdict(list),
            'issues_by_model': defaultdict(list),
            'detailed_issues': retrieval_issues
        }

    def get_relevant_keywords_for_question(self, question_id: int) -> List[str]:
        """Obtiene palabras clave relevantes para cada pregunta"""
        keywords_map = {
            6: ["miércoles", "sábado", "whatsapp", "formulario", "apuntarse", "inscribirse"],
            14: ["tres años", "sexto de primaria", "infantil", "primaria", "edades"],
            19: ["reyes", "navidad", "día del niño", "terra mítica", "verano", "actividades"],
            22: ["resis", "acollida", "residentes", "miércoles", "pasar tiempo", "alegría"],
            10: ["colegio", "niños", "deberes", "refuerzo escolar", "cuentos", "manualidades"],
            11: ["ceip antonio ferrandis", "coma", "valencia"],
            12: ["lunes", "martes", "miércoles", "jueves", "viernes", "15:30", "16:30"]
        }
        return keywords_map.get(question_id, [])

    def analyze_model_performance_patterns(self) -> Dict[str, Any]:
        """Analiza patrones de rendimiento por modelo"""
        print("📈 Analizando patrones de rendimiento por modelo...")

        model_patterns = {}

        for item in self.data:
            model = item['model_name']
            q_id = item['question_id']
            score = item.get('metrics', {}).get('combined_score', 0)
            gen_time = item.get('generation_time', 0)

            if model not in model_patterns:
                model_patterns[model] = {
                    'scores_by_question': {},
                    'times_by_question': {},
                    'problematic_questions': [],
                    'excellent_questions': [],
                    'avg_score': 0,
                    'avg_time': 0,
                    'consistency_score': 0
                }

            patterns = model_patterns[model]
            patterns['scores_by_question'][q_id] = score
            patterns['times_by_question'][q_id] = gen_time

            if score < 0.4:
                patterns['problematic_questions'].append(q_id)
            elif score > 0.9:
                patterns['excellent_questions'].append(q_id)

        # Calcular estadísticas finales
        for model, patterns in model_patterns.items():
            scores = list(patterns['scores_by_question'].values())
            times = list(patterns['times_by_question'].values())

            patterns['avg_score'] = statistics.mean(scores) if scores else 0
            patterns['avg_time'] = statistics.mean(times) if times else 0

            # Consistencia: 1 - desviación estándar normalizada
            if len(scores) > 1:
                std_dev = statistics.stdev(scores)
                patterns['consistency_score'] = max(0, 1 - (std_dev / 1.0))  # Normalizar a 0-1
            else:
                patterns['consistency_score'] = 1.0

        return model_patterns

    def generate_analysis_report(self) -> Dict[str, Any]:
        """Genera reporte completo de análisis"""
        print("📋 Generando reporte completo...")

        return {
            'benchmark_file': str(self.benchmark_file),
            'total_entries': len(self.data),
            'model_timeout_analysis': self.analyze_timeouts_and_truncations(),
            'question_difficulty_analysis': self.analyze_question_difficulty(),
            'retrieval_quality_analysis': self.analyze_retrieval_quality(),
            'model_performance_patterns': self.analyze_model_performance_patterns(),
            'problematic_questions': self.identify_most_problematic_questions(),
            'recommendations': self.generate_recommendations()
        }

    def identify_most_problematic_questions(self) -> List[Dict]:
        """Identifica las preguntas más problemáticas"""
        question_stats = self.analyze_question_difficulty()

        problematic = []
        for q_id, stats in question_stats.items():
            if stats['avg_score'] < 0.6 or len(stats['failed_models']) > 2:
                problematic.append({
                    'question_id': q_id,
                    'question_text': stats['question_text'],
                    'avg_score': stats['avg_score'],
                    'failed_models': stats['failed_models'],
                    'successful_models': stats['successful_models'],
                    'difficulty': stats['difficulty'],
                    'failure_rate': len(stats['failed_models']) / len(stats['scores'])
                })

        return sorted(problematic, key=lambda x: x['avg_score'])

    def generate_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []

        # Analizar timeouts
        timeout_analysis = self.analyze_timeouts_and_truncations()
        for model, stats in timeout_analysis.items():
            if stats['truncated_responses'] > 0:
                recommendations.append(
                    f"🚨 {model}: {stats['truncated_responses']} respuestas truncadas. "
                    f"Aumentar timeout o ajustar parámetros de generación."
                )

            if stats['avg_generation_time'] > 50:
                recommendations.append(
                    f"⏰ {model}: Tiempo promedio alto ({stats['avg_generation_time']:.1f}s). "
                    f"Considerar optimización de prompts o reducción de contexts."
                )

        # Analizar retrieval
        retrieval_analysis = self.analyze_retrieval_quality()
        if retrieval_analysis['total_issues'] > 0:
            info_not_used = len([i for i in retrieval_analysis['detailed_issues']
                               if i['issue_type'] == 'info_available_not_used'])
            if info_not_used > 0:
                recommendations.append(
                    f"🔍 {info_not_used} casos donde la información está disponible pero no se usa. "
                    f"Mejorar prompts para incentivar uso de contexts."
                )

        # Analizar preguntas problemáticas
        problematic_questions = self.identify_most_problematic_questions()
        if problematic_questions:
            recommendations.append(
                f"❓ Hay {len(problematic_questions)} preguntas consistentemente difíciles. "
                f"Considerar expansión de queries o ajuste de retrieval."
            )

        return recommendations

def main():
    """Función principal para ejecutar el análisis"""
    benchmark_file = "results/benchmark_20251011_012920.json"

    if not Path(benchmark_file).exists():
        print(f"❌ Error: No se encuentra el archivo {benchmark_file}")
        return

    analyzer = BenchmarkAnalyzer(benchmark_file)
    report = analyzer.generate_analysis_report()

    # Guardar reporte
    output_file = f"results/technical_analysis_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Análisis completo guardado en: {output_file}")

    # Mostrar resumen
    print("\n📊 RESUMEN DE ANÁLISIS TÉCNICO:")
    print("="*50)

    # Timeouts
    print("\n🚨 ANÁLISIS DE TIMEOUTS:")
    for model, stats in report['model_timeout_analysis'].items():
        if stats['truncated_responses'] > 0:
            print(f"  {model}: {stats['truncated_responses']} truncamientos")
        print(f"    Tiempo promedio: {stats['avg_generation_time']:.1f}s")
        print(f"    Tiempo máximo: {stats['max_generation_time']:.1f}s")

    # Preguntas problemáticas
    print(f"\n❓ PREGUNTAS MÁS PROBLEMÁTICAS:")
    for i, q in enumerate(report['problematic_questions'][:5]):
        print(f"  {i+1}. Q{q['question_id']}: Score {q['avg_score']:.3f}")
        print(f"     Fallos: {q['failed_models']}")

    # Retrieval issues
    retrieval = report['retrieval_quality_analysis']
    print(f"\n🔍 PROBLEMAS DE RETRIEVAL:")
    print(f"  Total de issues: {retrieval['total_issues']}")
    for issue_type, issues in retrieval['issues_by_type'].items():
        print(f"  {issue_type}: {len(issues)} casos")

    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    for i, rec in enumerate(report['recommendations'][:5]):
        print(f"  {i+1}. {rec}")

if __name__ == "__main__":
    main()