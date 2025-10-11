#!/usr/bin/env python3
"""
Análisis detallado de preguntas problemáticas específicas: 6, 14, 19, 22
"""

import json
from pathlib import Path
from typing import Dict, List, Any

class ProblematicQuestionsAnalyzer:
    def __init__(self, benchmark_file: str):
        self.benchmark_file = Path(benchmark_file)
        self.data = self.load_benchmark_data()
        self.problematic_ids = [6, 14, 19, 22]

    def load_benchmark_data(self) -> List[Dict]:
        """Carga datos del benchmark"""
        with open(self.benchmark_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze_question(self, question_id: int) -> Dict[str, Any]:
        """Analiza una pregunta específica en detalle"""
        print(f"\n🔍 Analizando pregunta {question_id}...")

        question_data = [
            item for item in self.data
            if item['question_id'] == question_id
        ]

        if not question_data:
            return {"error": f"Question {question_id} not found"}

        # Obtener expected_answer del dataset
        expected_answer = self.get_expected_answer(question_id)

        analysis = {
            'question_id': question_id,
            'question_text': question_data[0]['question'],
            'expected_answer': expected_answer,
            'models': {},
            'common_contexts': set(),
            'issues_found': []
        }

        for item in question_data:
            model = item['model_name']
            answer = item['answer']
            contexts = item['contexts']
            metrics = item['metrics']

            # Análisis por modelo
            model_analysis = {
                'answer': answer,
                'answer_length': len(answer),
                'is_truncated': '[Respuesta truncada' in answer,
                'has_no_info': 'no tengo esa información' in answer.lower(),
                'contexts_count': len(contexts),
                'contexts_preview': [c[:150] + '...' if len(c) > 150 else c for c in contexts[:3]],
                'metrics': metrics,
                'generation_time': item.get('generation_time', 0),
                'uses_expected_keywords': self.check_keyword_usage(answer, expected_answer),
                'relevant_info_in_contexts': self.check_relevant_info_in_contexts(contexts, question_id),
                'issues': []
            }

            # Identificar problemas específicos
            if model_analysis['is_truncated']:
                model_analysis['issues'].append('timeout_truncation')

            if model_analysis['has_no_info'] and model_analysis['relevant_info_in_contexts']:
                model_analysis['issues'].append('info_available_not_used')

            if not model_analysis['relevant_info_in_contexts']:
                model_analysis['issues'].append('poor_retrieval')

            if metrics.get('combined_score', 0) < 0.3 and model_analysis['relevant_info_in_contexts']:
                model_analysis['issues'].append('low_score_with_available_info')

            analysis['models'][model] = model_analysis

            # Recolectar contexts comunes
            analysis['common_contexts'].update(contexts)

        analysis['common_contexts'] = list(analysis['common_contexts'])[:5]  # Top 5

        # Análisis comparativo
        analysis['comparative_analysis'] = self.comparative_analysis(analysis['models'])
        analysis['recommendations'] = self.generate_question_recommendations(question_id, analysis)

        return analysis

    def get_expected_answer(self, question_id: int) -> str:
        """Obtiene la respuesta esperada del dataset de evaluación"""
        dataset_file = Path("data/evaluation_dataset.json")
        if not dataset_file.exists():
            return "Dataset no encontrado"

        with open(dataset_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
            for item in dataset:
                if item['id'] == question_id:
                    return item['expected_answer']

        return f"Respuesta esperada no encontrada para pregunta {question_id}"

    def check_keyword_usage(self, answer: str, expected_answer: str) -> Dict[str, bool]:
        """Verifica si la respuesta usa palabras clave de la respuesta esperada"""
        # Extraer palabras clave importantes
        expected_keywords = set()
        for word in expected_answer.lower().split():
            if len(word) > 4:  # Palabras más largas de 4 caracteres
                expected_keywords.add(word)

        answer_lower = answer.lower()
        keyword_usage = {}

        for keyword in expected_keywords:
            keyword_usage[keyword] = keyword in answer_lower

        return keyword_usage

    def check_relevant_info_in_contexts(self, contexts: List[str], question_id: int) -> bool:
        """Verifica si hay información relevante en los contexts para la pregunta"""
        relevant_keywords = self.get_relevant_keywords(question_id)

        for context in contexts:
            context_lower = context.lower()
            if any(keyword in context_lower for keyword in relevant_keywords):
                return True

        return False

    def get_relevant_keywords(self, question_id: int) -> List[str]:
        """Obtiene palabras clave relevantes para cada pregunta"""
        keywords_map = {
            6: ["miércoles", "sábado", "whatsapp", "formulario", "apuntarse", "inscribirse", "comunidad"],
            14: ["tres años", "sexto de primaria", "infantil", "primaria", "edades", "niños"],
            19: ["reyes", "navidad", "día del niño", "terra mítica", "verano", "actividades", "puntuales"],
            22: ["resis", "acollida", "residentes", "miércoles", "pasar tiempo", "alegría", "jóvenes"],
            10: ["colegio", "niños", "deberes", "refuerzo escolar", "cuentos", "manualidades"],
            11: ["ceip antonio ferrandis", "coma", "valencia"],
            12: ["lunes", "martes", "miércoles", "jueves", "viernes", "15:30", "16:30"]
        }
        return keywords_map.get(question_id, [])

    def comparative_analysis(self, models_data: Dict[str, Dict]) -> Dict[str, Any]:
        """Análisis comparativo entre modelos para esta pregunta"""
        scores = {model: data['metrics'].get('combined_score', 0) for model, data in models_data.items()}
        times = {model: data['generation_time'] for model, data in models_data.items()}

        best_model = max(scores, key=scores.get)
        worst_model = min(scores, key=scores.get)

        return {
            'best_model': {
                'name': best_model,
                'score': scores[best_model],
                'time': times[best_model]
            },
            'worst_model': {
                'name': worst_model,
                'score': scores[worst_model],
                'time': times[worst_model]
            },
            'score_range': max(scores.values()) - min(scores.values()),
            'all_scores': scores,
            'all_times': times
        }

    def generate_question_recommendations(self, question_id: int, analysis: Dict) -> List[str]:
        """Genera recomendaciones específicas para la pregunta"""
        recommendations = []

        # Analizar problemas comunes
        models_with_issues = [
            model for model, data in analysis['models'].items()
            if data['issues']
        ]

        if models_with_issues:
            recommendations.append(
                f"🔧 {len(models_with_issues)} modelos tienen problemas en Q{question_id}. "
                f"Revisar retrieval y prompts."
            )

        # Analizar información no utilizada
        info_not_used = [
            model for model, data in analysis['models'].items()
            if 'info_available_not_used' in data['issues']
        ]

        if info_not_used:
            recommendations.append(
                f"💡 {len(info_not_used)} modelos no usan información disponible. "
                f"Mejorar instrucciones de prompts."
            )

        # Analizar timeouts
        truncated = [
            model for model, data in analysis['models'].items()
            if data['is_truncated']
        ]

        if truncated:
            recommendations.append(
                f"⏰ {len(truncated)} modelos con truncamiento. "
                f"Aumentar timeout o simplificar prompts."
            )

        # Recomendaciones específicas por pregunta
        if question_id == 6:
            recommendations.append(
                "P6: Verificar que contexts incluyan info sobre formulario de WhatsApp."
            )
        elif question_id == 14:
            recommendations.append(
                "P14: Asegurar que contexts mencionen rangos de edad específicos."
            )
        elif question_id == 19:
            recommendations.append(
                "P19: Incluir más contexts sobre actividades especiales con niños."
            )
        elif question_id == 22:
            recommendations.append(
                "P22: CRÍTICO - La información sobre resis no se está recuperando bien."
            )

        return recommendations

    def analyze_all_problematic_questions(self) -> Dict[str, Any]:
        """Analiza todas las preguntas problemáticas"""
        print("🚨 Analizando preguntas problemáticas: 6, 14, 19, 22")

        results = {}
        for q_id in self.problematic_ids:
            results[f"Q{q_id}"] = self.analyze_question(q_id)

        # Análisis global
        global_analysis = {
            'total_models_analyzed': len(set(item['model_name'] for item in self.data)),
            'common_issues': self.identify_common_issues(results),
            'global_recommendations': self.generate_global_recommendations(results),
            'priority_actions': self.identify_priority_actions(results)
        }

        return {
            'questions_analysis': results,
            'global_analysis': global_analysis
        }

    def identify_common_issues(self, results: Dict[str, Any]) -> Dict[str, int]:
        """Identifica problemas comunes entre todas las preguntas"""
        issue_counts = {}

        for q_data in results.values():
            for model_data in q_data['models'].values():
                for issue in model_data['issues']:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1

        return issue_counts

    def generate_global_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones globales basadas en el análisis"""
        recommendations = []

        # Recolectar todos los problemas
        all_issues = []
        for q_data in results.values():
            for model_data in q_data['models'].values():
                all_issues.extend(model_data['issues'])

        # Analizar frecuencias
        from collections import Counter
        issue_counter = Counter(all_issues)

        # Top problemas
        if 'info_available_not_used' in issue_counter:
            recommendations.append(
                f"🔍 PRIORIDAD ALTA: {issue_counter['info_available_not_used']} casos "
                f"donde la información está disponible pero no se usa. "
                f"Implementar prompts más directivos."
            )

        if 'timeout_truncation' in issue_counter:
            recommendations.append(
                f"⏰ MEDIA: {issue_counter['timeout_truncation']} timeouts. "
                f"Ajustar timeouts o simplificar prompts."
            )

        if 'poor_retrieval' in issue_counter:
            recommendations.append(
                f"📚 MEDIA: {issue_counter['poor_retrieval']} casos con pobre retrieval. "
                f"Revisar chunks y similarity_threshold."
            )

        return recommendations

    def identify_priority_actions(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifica acciones prioritarias ordenadas por impacto"""
        actions = []

        # Q22 parece ser el peor
        q22_data = results.get('Q22', {})
        if q22_data:
            avg_score = sum(
                data['metrics'].get('combined_score', 0)
                for data in q22_data['models'].values()
            ) / len(q22_data['models'])

            actions.append({
                'priority': 1,
                'action': 'Fix Q22 - Resis Activity',
                'description': f'Pregunta 22 tiene score promedio {avg_score:.3f}. '
                               f'Necesita atención urgente en retrieval.',
                'estimated_impact': 'high'
            })

        # Timeouts de qwen3
        qwen_timeout_count = sum(
            1 for q_data in results.values()
            for model_name, model_data in q_data['models'].items()
            if 'qwen3' in model_name and model_data['is_truncated']
        )

        if qwen_timeout_count > 0:
            actions.append({
                'priority': 2,
                'action': 'Fix qwen3 Timeouts',
                'description': f'qwen3 tiene {qwen_timeout_count} timeouts en preguntas críticas.',
                'estimated_impact': 'medium'
            })

        # Mejora general de prompts
        info_not_used_count = sum(
            1 for q_data in results.values()
            for model_data in q_data['models'].values()
            if 'info_available_not_used' in model_data['issues']
        )

        if info_not_used_count > 0:
            actions.append({
                'priority': 3,
                'action': 'Improve Prompts for Context Usage',
                'description': f'{info_not_used_count} casos donde hay info disponible pero no se usa.',
                'estimated_impact': 'high'
            })

        return sorted(actions, key=lambda x: x['priority'])

def main():
    """Función principal"""
    benchmark_file = "results/benchmark_20251011_012920.json"

    if not Path(benchmark_file).exists():
        print(f"❌ Error: No se encuentra {benchmark_file}")
        return

    analyzer = ProblematicQuestionsAnalyzer(benchmark_file)
    results = analyzer.analyze_all_problematic_questions()

    # Guardar resultados
    output_file = f"results/problematic_questions_analysis_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Análisis guardado en: {output_file}")

    # Mostrar resumen ejecutivo
    print("\n🎯 RESUMEN EJECUTIVO - PREGUNTAS PROBLEMÁTICAS")
    print("=" * 60)

    # Análisis por pregunta
    for q_key, q_data in results['questions_analysis'].items():
        print(f"\n📍 {q_key}: {q_data['question_text'][:60]}...")

        comp = q_data['comparative_analysis']
        print(f"   🏆 Mejor: {comp['best_model']['name']} ({comp['best_model']['score']:.3f})")
        print(f"   ⚠️ Peor: {comp['worst_model']['name']} ({comp['worst_model']['score']:.3f})")

        # Problemas principales
        issues = []
        for model, data in q_data['models'].items():
            if data['is_truncated']:
                issues.append(f"{model}: truncado")
            elif data['has_no_info'] and data['relevant_info_in_contexts']:
                issues.append(f"{model}: info no usada")

        if issues:
            print(f"   🚨 Problemas: {', '.join(issues)}")

    # Acciones prioritarias
    print(f"\n🎯 ACCIONES PRIORITARIAS:")
    for i, action in enumerate(results['global_analysis']['priority_actions'], 1):
        print(f"   {i}. {action['action']} (Prioridad: {action['priority']})")
        print(f"      {action['description']}")

    # Recomendaciones globales
    print(f"\n💡 RECOMENDACIONES GLOBALES:")
    for i, rec in enumerate(results['global_analysis']['global_recommendations'], 1):
        print(f"   {i}. {rec}")

if __name__ == "__main__":
    import time
    main()