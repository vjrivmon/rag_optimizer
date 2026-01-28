#!/usr/bin/env python3
"""
Fase 3: Sistema de Debugging RAGAs - Análisis métrica por métrica
Analiza por qué RAGAs da las puntuaciones que da y si es demasiado estricto
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import statistics

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RAGAsMetricAnalysis:
    """Análisis detallado de una métrica RAGAs específica"""
    metric_name: str
    value: float
    expected_answer: str
    generated_answer: str
    contexts: List[str]
    question: str
    issues_found: List[str]
    improvement_suggestions: List[str]
    is_too_strict: bool
    confidence: float

class RAGAsDebugger:
    """Sistema especializado en debuggear métricas RAGAs"""

    def __init__(self):
        self.metric_descriptions = {
            'faithfulness': "¿La respuesta se basa fielmente en los contexts proporcionados?",
            'answer_relevancy': "¿Qué tan relevante es la respuesta para la pregunta?",
            'context_precision': "¿Qué tan precisos son los contexts recuperados para la pregunta?",
            'context_recall': "¿Qué tan completa es la respuesta en relación a los contexts?",
            'answer_correctness': "¿Qué tan correcta es la respuesta comparada con una respuesta de referencia?",
            'answer_similarity': "¿Qué tan similar es la respuesta a la respuesta esperada?"
        }

    def analyze_benchmark_results(self, benchmark_file: str) -> Dict[str, Any]:
        """Analiza resultados de benchmark en detalle"""
        logger.info("🔍 Iniciando análisis detallado de métricas RAGAs...")

        if not Path(benchmark_file).exists():
            raise FileNotFoundError(f"No se encuentra el archivo {benchmark_file}")

        with open(benchmark_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Análisis general
        overall_analysis = self.analyze_overall_metrics(data)

        # Análisis por modelo
        model_analysis = self.analyze_metrics_by_model(data)

        # Análisis por pregunta
        question_analysis = self.analyze_metrics_by_question(data)

        # Análisis de casos problemáticos
        problematic_cases = self.identify_problematic_cases(data)

        # Análisis de strictness
        strictness_analysis = self.analyze_ragas_strictness(data)

        return {
            'benchmark_file': benchmark_file,
            'total_entries': len(data),
            'overall_analysis': overall_analysis,
            'model_analysis': model_analysis,
            'question_analysis': question_analysis,
            'problematic_cases': problematic_cases,
            'strictness_analysis': strictness_analysis,
            'recommendations': self.generate_ragas_recommendations(strictness_analysis)
        }

    def analyze_overall_metrics(self, data: List[Dict]) -> Dict[str, Any]:
        """Análisis general de todas las métricas"""
        metrics_data = {
            'faithfulness': [],
            'answer_relevancy': [],
            'context_precision': [],
            'context_recall': [],
            'answer_correctness': [],
            'answer_similarity': [],
            'combined_score': []
        }

        for item in data:
            metrics = item.get('metrics', {})
            for metric in metrics_data:
                if metric in metrics:
                    metrics_data[metric].append(metrics[metric])

        analysis = {}
        for metric, values in metrics_data.items():
            if values:
                analysis[metric] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                    'min': min(values),
                    'max': max(values),
                    'count': len(values),
                    'zeros_count': values.count(0.0),
                    'zeros_percentage': (values.count(0.0) / len(values)) * 100
                }

        return analysis

    def analyze_metrics_by_model(self, data: List[Dict]) -> Dict[str, Dict]:
        """Analiza rendimiento por modelo"""
        model_data = {}

        for item in data:
            model = item['model_name']
            if model not in model_data:
                model_data[model] = []

            model_data[model].append(item)

        analysis = {}
        for model, items in model_data.items():
            model_metrics = {
                'faithfulness': [],
                'answer_relevancy': [],
                'context_precision': [],
                'context_recall': [],
                'answer_correctness': [],
                'answer_similarity': [],
                'combined_score': []
            }

            for item in items:
                metrics = item.get('metrics', {})
                for metric in model_metrics:
                    if metric in metrics:
                        model_metrics[metric].append(metrics[metric])

            analysis[model] = {
                'total_questions': len(items),
                'metrics_stats': {}
            }

            for metric, values in model_metrics.items():
                if values:
                    analysis[model]['metrics_stats'][metric] = {
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                        'min': min(values),
                        'max': max(values),
                        'zeros_count': values.count(0.0),
                        'zeros_percentage': (values.count(0.0) / len(values)) * 100
                    }

        return analysis

    def analyze_metrics_by_question(self, data: List[Dict]) -> Dict[int, Dict]:
        """Analiza rendimiento por pregunta"""
        question_data = {}

        for item in data:
            q_id = item['question_id']
            if q_id not in question_data:
                question_data[q_id] = []

            question_data[q_id].append(item)

        analysis = {}
        for q_id, items in question_data.items():
            question_metrics = {
                'faithfulness': [],
                'answer_relevancy': [],
                'context_precision': [],
                'context_recall': [],
                'answer_correctness': [],
                'answer_similarity': [],
                'combined_score': []
            }

            for item in items:
                metrics = item.get('metrics', {})
                for metric in question_metrics:
                    if metric in metrics:
                        question_metrics[metric].append(metrics[metric])

            analysis[q_id] = {
                'question_text': items[0].get('question', ''),
                'total_models': len(items),
                'metrics_stats': {}
            }

            for metric, values in question_metrics.items():
                if values:
                    analysis[q_id]['metrics_stats'][metric] = {
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                        'min': min(values),
                        'max': max(values),
                        'zeros_count': values.count(0.0),
                        'zeros_percentage': (values.count(0.0) / len(values)) * 100
                    }

        return analysis

    def identify_problematic_cases(self, data: List[Dict]) -> List[Dict]:
        """Identifica casos problemáticos específicos"""
        problematic_cases = []

        for item in data:
            metrics = item.get('metrics', {})
            combined_score = metrics.get('combined_score', 1.0)

            # Casos problemáticos
            issues = []

            if combined_score < 0.3:
                issues.append('very_low_combined_score')

            if metrics.get('faithfulness', 1.0) < 0.3:
                issues.append('low_faithfulness')

            if metrics.get('answer_relevancy', 1.0) < 0.3:
                issues.append('low_relevancy')

            if metrics.get('context_recall', 1.0) < 0.3:
                issues.append('low_recall')

            # Verificar si la respuesta parece razonable pero el score es bajo
            answer = item.get('answer', '')
            if answer and 'no tengo esa información' not in answer.lower():
                if combined_score < 0.5:
                    issues.append('reasonable_answer_low_score')

            if issues:
                problematic_cases.append({
                    'question_id': item['question_id'],
                    'model_name': item['model_name'],
                    'question': item.get('question', ''),
                    'answer': answer,
                    'combined_score': combined_score,
                    'metrics': metrics,
                    'issues': issues,
                    'contexts_count': len(item.get('contexts', [])),
                    'generation_time': item.get('generation_time', 0)
                })

        # Ordenar por severidad (score más bajo primero)
        problematic_cases.sort(key=lambda x: x['combined_score'])

        return problematic_cases

    def analyze_ragas_strictness(self, data: List[Dict]) -> Dict[str, Any]:
        """Analiza si RAGAs es demasiado estricto"""
        strictness_analysis = {
            'overall_strictness_score': 0,
            'metric_strictness': {},
            'question_strictness': {},
            'model_strictness': {},
            'evidence_of_strictness': []
        }

        # Analizar cada métrica
        all_metrics = ['faithfulness', 'answer_relevancy', 'context_precision',
                      'context_recall', 'answer_correctness', 'answer_similarity']

        for metric in all_metrics:
            values = []
            for item in data:
                if metric in item.get('metrics', {}):
                    values.append(item['metrics'][metric])

            if values:
                zeros_pct = (values.count(0.0) / len(values)) * 100
                low_scores_pct = (len([v for v in values if v < 0.3]) / len(values)) * 100

                strictness_analysis['metric_strictness'][metric] = {
                    'zeros_percentage': zeros_pct,
                    'low_scores_percentage': low_scores_pct,
                    'mean_score': statistics.mean(values),
                    'is_too_strict': zeros_pct > 20 or low_scores_pct > 40
                }

        # Análisis general de strictness
        total_cases = len(data)
        very_low_scores = len([
            item for item in data
            if item.get('metrics', {}).get('combined_score', 1.0) < 0.3
        ])

        strictness_analysis['overall_strictness_score'] = very_low_scores / total_cases if total_cases > 0 else 0

        # Buscar evidencia de strictness
        for item in data:
            answer = item.get('answer', '')
            combined_score = item.get('metrics', {}).get('combined_score', 1.0)

            # Respuestas razonables con scores bajos
            if (combined_score < 0.4 and
                answer and
                len(answer) > 20 and
                'no tengo' not in answer.lower() and
                'error' not in answer.lower()):

                strictness_analysis['evidence_of_strictness'].append({
                    'question_id': item['question_id'],
                    'model_name': item['model_name'],
                    'answer_preview': answer[:100] + '...',
                    'score': combined_score,
                    'metrics': item.get('metrics', {}),
                    'reason': 'reasonable_answer_low_score'
                })

        return strictness_analysis

    def debug_specific_case(self, item: Dict, expected_answer: str = None) -> RAGAsMetricAnalysis:
        """Debugguea un caso específico en detalle"""
        question = item.get('question', '')
        answer = item.get('answer', '')
        contexts = item.get('contexts', [])
        metrics = item.get('metrics', {})

        # Análisis de cada métrica
        issues_found = []
        improvement_suggestions = []

        # Faithfulness analysis
        faithfulness = metrics.get('faithfulness', 0)
        if faithfulness < 0.5:
            issues_found.append(f"Faithfulness bajo ({faithfulness:.3f}) - respuesta no se basa en contexts")
            improvement_suggestions.append("Forzar uso de información de contexts en el prompt")

        # Answer relevancy analysis
        relevancy = metrics.get('answer_relevancy', 0)
        if relevancy < 0.5:
            issues_found.append(f"Relevancia baja ({relevancy:.3f}) - respuesta no relevante")
            improvement_suggestions.append("Mejorar prompt para responder específicamente a la pregunta")

        # Context precision/recall analysis
        context_precision = metrics.get('context_precision', 0)
        context_recall = metrics.get('context_recall', 0)

        if context_precision < 0.5:
            issues_found.append(f"Context precision bajo ({context_precision:.3f}) - contexts no precisos")
            improvement_suggestions.append("Mejorar retrieval - ajustar similarity_threshold")

        if context_recall < 0.5:
            issues_found.append(f"Context recall bajo ({context_recall:.3f}) - respuesta incompleta")
            improvement_suggestions.append("Incluir más contexts o mejorar ránking")

        # Answer correctness/similarity analysis
        if expected_answer:
            correctness = metrics.get('answer_correctness', 0)
            similarity = metrics.get('answer_similarity', 0)

            if correctness < 0.5:
                issues_found.append(f"Correctness bajo ({correctness:.3f}) - respuesta incorrecta")
                improvement_suggestions.append("Mejorar calidad de información en contexts")

            if similarity < 0.5:
                issues_found.append(f"Similarity bajo ({similarity:.3f}) - respuesta diferente a esperada")
                improvement_suggestions.append("Ajustar prompts para generar respuestas más similares")

        # Determinar si RAGAs es demasiado estricto
        is_too_strict = self._is_ragas_too_strict_for_case(answer, metrics, contexts)

        return RAGAsMetricAnalysis(
            metric_name="combined_analysis",
            value=metrics.get('combined_score', 0),
            expected_answer=expected_answer or "",
            generated_answer=answer,
            contexts=contexts,
            question=question,
            issues_found=issues_found,
            improvement_suggestions=improvement_suggestions,
            is_too_strict=is_too_strict,
            confidence=0.8  # Placeholder
        )

    def _is_ragas_too_strict_for_case(self, answer: str, metrics: Dict, contexts: List[str]) -> bool:
        """Determina si RAGAs es demasiado estricto para un caso específico"""
        combined_score = metrics.get('combined_score', 1.0)

        # Si la respuesta parece razonable pero el score es bajo
        if (combined_score < 0.4 and
            answer and
            len(answer) > 30 and
            'no tengo' not in answer.lower() and
            'error' not in answer.lower() and
            '[Respuesta truncada' not in answer):

            # Verificar si usa información de los contexts
            answer_words = set(answer.lower().split())
            for context in contexts[:3]:  # Revisar primeros 3 contexts
                context_words = set(context.lower().split())
                overlap = len(answer_words & context_words)
                if overlap > 3:  # Si comparte palabras con contexts
                    return True

        return False

    def generate_ragas_recommendations(self, strictness_analysis: Dict) -> List[str]:
        """Genera recomendaciones basadas en análisis de strictness"""
        recommendations = []

        overall_score = strictness_analysis['overall_strictness_score']
        evidence = strictness_analysis['evidence_of_strictness']

        if overall_score > 0.3:
            recommendations.append(
                f"🚨 RAGAs parece demasiado estricto: {overall_score:.1%} de casos con scores muy bajos"
            )

        if len(evidence) > 5:
            recommendations.append(
                f"⚠️ Hay {len(evidence)} casos con respuestas razonables pero scores bajos"
            )

        # Analizar métricas específicas
        for metric, analysis in strictness_analysis['metric_strictness'].items():
            if analysis['is_too_strict']:
                recommendations.append(
                    f"📊 Métrica '{metric}' parece demasiado estricta "
                    f"({analysis['zeros_percentage']:.1f}% zeros, "
                    f"{analysis['low_scores_percentage']:.1f}% scores bajos)"
                )

        # Recomendaciones específicas
        if len(evidence) > 0:
            recommendations.append(
                "💡 Considerar implementar evaluación híbrida que combine RAGAs con análisis cualitativo"
            )

            recommendations.append(
                "🔧 Para respuestas con scores bajos pero razonables, considerar re-evaluación manual"
            )

        return recommendations

    def create_debugging_report(self, analysis_results: Dict) -> str:
        """Crea un reporte legible de debugging"""
        report = []
        report.append("🔍 REPORTE DE DEBUGGING RAGAs")
        report.append("=" * 60)

        # Resumen general
        overall = analysis_results['overall_analysis']
        report.append("\n📊 ANÁLISIS GENERAL DE MÉTRICAS:")

        if 'combined_score' in overall:
            combined = overall['combined_score']
            report.append(f"   Score combinado - Media: {combined['mean']:.3f}, "
                         f"Zeros: {combined['zeros_percentage']:.1f}%")

        for metric, stats in overall.items():
            if metric != 'combined_score':
                report.append(f"   {metric} - Media: {stats['mean']:.3f}, "
                             f"Zeros: {stats['zeros_percentage']:.1f}%")

        # Análisis de strictness
        strictness = analysis_results['strictness_analysis']
        report.append(f"\n🚨 ANÁLISIS DE STRICTNESS:")
        report.append(f"   Score de strictness general: {strictness['overall_strictness_score']:.3f}")

        evidence = strictness['evidence_of_strictness']
        report.append(f"   Casos con respuestas razonables pero scores bajos: {len(evidence)}")

        if evidence:
            report.append("\n   Ejemplos de posible strictness excesiva:")
            for i, case in enumerate(evidence[:3], 1):
                report.append(f"   {i}. Q{case['question_id']} - {case['model_name']}: "
                             f"Score {case['score']:.3f}")
                report.append(f"      Respuesta: {case['answer_preview']}")

        # Recomendaciones
        recommendations = analysis_results['recommendations']
        if recommendations:
            report.append(f"\n💡 RECOMENDACIONES:")
            for i, rec in enumerate(recommendations, 1):
                report.append(f"   {i}. {rec}")

        return "\n".join(report)

def main():
    """Función principal para debugging"""
    benchmark_file = "results/benchmark_20251011_012920.json"

    if not Path(benchmark_file).exists():
        logger.error(f"❌ No se encuentra el archivo {benchmark_file}")
        return 1

    debugger = RAGAsDebugger()
    logger.info("🔍 Iniciando debugging RAGAs...")

    # Analizar benchmark
    analysis_results = debugger.analyze_benchmark_results(benchmark_file)

    # Guardar análisis completo
    output_file = f"results/ragas_debugging_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ Análisis guardado en: {output_file}")

    # Generar reporte legible
    report = debugger.create_debugging_report(analysis_results)

    # Guardar reporte legible
    report_file = f"results/ragas_debugging_report_{int(time.time())}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"📄 Reporte guardado en: {report_file}")

    # Mostrar resumen
    print("\n" + report)

    return 0

if __name__ == "__main__":
    exit(main())