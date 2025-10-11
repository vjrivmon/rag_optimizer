#!/usr/bin/env python3
"""
Fase 2: Test de optimizaciones mejoradas en preguntas problemáticas
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Añadir paths para imports
sys.path.append('src')

try:
    from core.enhanced_model_wrapper import EnhancedModelManager
    from core.enhanced_rag_engine_new import create_enhanced_rag_engine
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    sys.exit(1)

class OptimizationTester:
    def __init__(self):
        self.model_manager = None
        self.rag_engine = None
        self.test_results = []

    def setup(self):
        """Inicializa componentes"""
        try:
            logger.info("🔧 Inicializando Enhanced Model Manager...")
            self.model_manager = EnhancedModelManager()

            logger.info("🔧 Inicializando Enhanced RAG Engine...")
            self.rag_engine = create_enhanced_rag_engine()

            logger.info("✅ Componentes inicializados correctamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error en inicialización: {e}")
            return False

    def test_problematic_questions(self) -> List[Dict[str, Any]]:
        """Test las preguntas problemáticas identificadas en Fase 1"""
        logger.info("🎯 Testeando preguntas problemáticas...")

        # Preguntas problemáticas con sus expected answers
        test_questions = [
            {
                "id": 6,
                "question": "¿Cómo me apunto a desayunos solidarios?",
                "expected_keywords": ["miércoles", "sábado", "whatsapp", "formulario"],
                "critical": True
            },
            {
                "id": 14,
                "question": "¿Qué edad tienen los niños en coles?",
                "expected_keywords": ["tres años", "sexto de primaria", "infantil"],
                "critical": False
            },
            {
                "id": 19,
                "question": "¿Qué otras actividades se hacen relacionadas con niños?",
                "expected_keywords": ["reyes", "navidad", "día del niño", "terra mítica"],
                "critical": True
            },
            {
                "id": 22,
                "question": "¿Qué se hace en la actividad de resis?",
                "expected_keywords": ["resis", "acollida", "residentes", "pasar tiempo"],
                "critical": True  # LA MÁS CRÍTICA
            }
        ]

        results = []

        for test_case in test_questions:
            logger.info(f"\n📍 Testeando P{test_case['id']}: {test_case['question'][:50]}...")

            # Generar respuestas con todos los modelos
            start_time = time.time()
            model_results = self.model_manager.generate_all_responses(
                test_case['question'],
                test_case['id']
            )
            total_time = time.time() - start_time

            # Analizar resultados
            question_result = self.analyze_question_results(
                test_case, model_results, total_time
            )

            results.append(question_result)

            # Mostrar resumen rápido
            self.print_quick_summary(question_result)

        return results

    def analyze_question_results(self, test_case: Dict, model_results: List[Dict], total_time: float) -> Dict[str, Any]:
        """Analiza los resultados para una pregunta específica"""
        question_id = test_case['id']
        expected_keywords = test_case['expected_keywords']

        analysis = {
            'question_id': question_id,
            'question': test_case['question'],
            'expected_keywords': expected_keywords,
            'total_generation_time': total_time,
            'model_results': {},
            'success_metrics': {
                'models_with_keywords': 0,
                'models_with_timeouts': 0,
                'models_with_no_info': 0,
                'models_with_errors': 0
            },
            'optimization_effectiveness': {}
        }

        for result in model_results:
            model_name = result['model_name']
            answer = result.get('answer', '')
            gen_time = result.get('generation_time', 0)
            config_used = result.get('config_used', {})

            # Análisis por modelo
            model_analysis = {
                'answer': answer,
                'answer_length': len(answer),
                'generation_time': gen_time,
                'is_timeout': '[Respuesta truncada' in answer,
                'has_no_info': 'no tengo esa información' in answer.lower(),
                'keyword_matches': self.check_keyword_usage(answer, expected_keywords),
                'optimization_type': config_used.get('optimization_type', 'None'),
                'timeout_used': config_used.get('applied_optimizations', {}).get('timeout', 120),
                'temperature_used': config_used.get('applied_optimizations', {}).get('temperature', 0.7)
            }

            analysis['model_results'][model_name] = model_analysis

            # Actualizar métricas de éxito
            if model_analysis['keyword_matches'] > 0:
                analysis['success_metrics']['models_with_keywords'] += 1
            if model_analysis['is_timeout']:
                analysis['success_metrics']['models_with_timeouts'] += 1
            if model_analysis['has_no_info']:
                analysis['success_metrics']['models_with_no_info'] += 1
            if result.get('error', False):
                analysis['success_metrics']['models_with_errors'] += 1

        # Calcular efectividad de optimizaciones
        analysis['optimization_effectiveness'] = self.calculate_optimization_effectiveness(
            analysis, test_case.get('critical', False)
        )

        return analysis

    def check_keyword_usage(self, answer: str, keywords: List[str]) -> int:
        """Verifica cuántas palabras clave esperadas aparecen en la respuesta"""
        answer_lower = answer.lower()
        matches = 0

        for keyword in keywords:
            if keyword in answer_lower:
                matches += 1

        return matches

    def calculate_optimization_effectiveness(self, analysis: Dict, is_critical: bool) -> Dict[str, Any]:
        """Calcula la efectividad de las optimizaciones"""
        total_models = len(analysis['model_results'])
        success_metrics = analysis['success_metrics']

        # Calcular tasas de éxito
        keyword_success_rate = success_metrics['models_with_keywords'] / total_models if total_models > 0 else 0
        timeout_rate = success_metrics['models_with_timeouts'] / total_models if total_models > 0 else 0
        no_info_rate = success_metrics['models_with_no_info'] / total_models if total_models > 0 else 0
        error_rate = success_metrics['models_with_errors'] / total_models if total_models > 0 else 0

        # Calcular score de efectividad
        if is_critical:
            # Para preguntas críticas, penalizar más fuertemente los fallos
            effectiveness_score = keyword_success_rate - (timeout_rate * 0.8) - (no_info_rate * 0.6) - (error_rate * 1.0)
        else:
            # Para preguntas no críticas, ser más indulgente
            effectiveness_score = keyword_success_rate - (timeout_rate * 0.5) - (no_info_rate * 0.3) - (error_rate * 0.8)

        # Determinar nivel de éxito
        if effectiveness_score >= 0.8:
            success_level = "EXCELLENT"
        elif effectiveness_score >= 0.6:
            success_level = "GOOD"
        elif effectiveness_score >= 0.4:
            success_level = "FAIR"
        elif effectiveness_score >= 0.2:
            success_level = "POOR"
        else:
            success_level = "CRITICAL_FAILURE"

        return {
            'effectiveness_score': max(0, effectiveness_score),  # No negativos
            'success_level': success_level,
            'keyword_success_rate': keyword_success_rate,
            'timeout_rate': timeout_rate,
            'no_info_rate': no_info_rate,
            'error_rate': error_rate,
            'is_critical': is_critical
        }

    def print_quick_summary(self, question_result: Dict[str, Any]):
        """Imprime resumen rápido de los resultados"""
        q_id = question_result['question_id']
        effectiveness = question_result['optimization_effectiveness']
        success_metrics = question_result['success_metrics']

        print(f"\n📊 P{q_id} - {effectiveness['success_level']} (Score: {effectiveness['effectiveness_score']:.3f})")
        print(f"   ✅ Keywords: {success_metrics['models_with_keywords']}/4 modelos")
        print(f"   ⏱️ Timeouts: {success_metrics['models_with_timeouts']}/4 modelos")
        print(f"   ❌ No info: {success_metrics['models_with_no_info']}/4 modelos")

        # Detalles por modelo
        for model, result in question_result['model_results'].items():
            status = []
            if result['keyword_matches'] > 0:
                status.append(f"✅{result['keyword_matches']}kw")
            if result['is_timeout']:
                status.append("⏰TO")
            if result['has_no_info']:
                status.append("❌NI")
            if not status:
                status.append("❓")

            print(f"   {model}: {' | '.join(status)} ({result['generation_time']:.1f}s)")

    def test_rag_engine_optimizations(self) -> Dict[str, Any]:
        """Test específico de optimizaciones del RAG engine"""
        logger.info("🔍 Testeando optimizaciones del RAG engine...")

        test_queries = [
            "resis actividad acollida",
            "apuntarse desayunos formulario miércoles",
            "niños edad primaria infantil",
            "actividades niños reyes terra mítica"
        ]

        results = {}

        for query in test_queries:
            try:
                # Test con diferentes configuraciones
                docs_standard = self.rag_engine.retrieve(query)
                docs_optimized_q22 = self.rag_engine.retrieve_with_optimization(query, 22, "gemma2:27b")

                results[query] = {
                    'standard_retrieval': {
                        'count': len(docs_standard),
                        'preview': [doc['content'][:50] + '...' for doc in docs_standard[:2]]
                    },
                    'optimized_retrieval': {
                        'count': len(docs_optimized_q22),
                        'preview': [doc['content'][:50] + '...' for doc in docs_optimized_q22[:2]]
                    },
                    'improvement': len(docs_optimized_q22) - len(docs_standard)
                }

            except Exception as e:
                logger.error(f"Error testeando query '{query}': {e}")
                results[query] = {'error': str(e)}

        return results

    def generate_comprehensive_report(self, question_results: List[Dict], rag_results: Dict) -> Dict[str, Any]:
        """Genera reporte comprensivo de todos los tests"""
        logger.info("📋 Generando reporte comprensivo...")

        # Estadísticas globales
        total_questions = len(question_results)
        critical_questions = [q for q in question_results if q.get('critical', False)]

        # Calcular mejoras generales
        overall_effectiveness = sum(
            q['optimization_effectiveness']['effectiveness_score']
            for q in question_results
        ) / total_questions if total_questions > 0 else 0

        critical_effectiveness = sum(
            q['optimization_effectiveness']['effectiveness_score']
            for q in critical_questions
        ) / len(critical_questions) if critical_questions else 0

        # Análisis por modelo
        model_analysis = {}
        for result in question_results:
            for model, data in result['model_results'].items():
                if model not in model_analysis:
                    model_analysis[model] = {
                        'total_timeouts': 0,
                        'total_no_info': 0,
                        'total_keyword_matches': 0,
                        'avg_generation_time': 0,
                        'tests_count': 0
                    }

                stats = model_analysis[model]
                if data['is_timeout']:
                    stats['total_timeouts'] += 1
                if data['has_no_info']:
                    stats['total_no_info'] += 1
                stats['total_keyword_matches'] += data['keyword_matches']
                stats['avg_generation_time'] += data['generation_time']
                stats['tests_count'] += 1

        # Calcular promedios por modelo
        for model, stats in model_analysis.items():
            if stats['tests_count'] > 0:
                stats['avg_generation_time'] /= stats['tests_count']
                stats['keyword_success_rate'] = stats['total_keyword_matches'] / (stats['tests_count'] * 4)  # 4 keywords avg
                stats['timeout_rate'] = stats['total_timeouts'] / stats['tests_count']
                stats['no_info_rate'] = stats['total_no_info'] / stats['tests_count']

        report = {
            'test_metadata': {
                'timestamp': time.time(),
                'total_questions_tested': total_questions,
                'critical_questions': len(critical_questions),
                'models_tested': list(model_analysis.keys())
            },
            'overall_results': {
                'effectiveness_score': overall_effectiveness,
                'critical_effectiveness': critical_effectiveness,
                'success_level': self.determine_overall_success(overall_effectiveness)
            },
            'question_results': question_results,
            'rag_engine_results': rag_results,
            'model_analysis': model_analysis,
            'recommendations': self.generate_recommendations(question_results, model_analysis),
            'next_steps': self.generate_next_steps(overall_effectiveness, critical_effectiveness)
        }

        return report

    def determine_overall_success(self, effectiveness_score: float) -> str:
        """Determina el nivel de éxito general"""
        if effectiveness_score >= 0.8:
            return "EXCELLENT_OPTIMIZATION"
        elif effectiveness_score >= 0.6:
            return "GOOD_OPTIMIZATION"
        elif effectiveness_score >= 0.4:
            return "MODERATE_IMPROVEMENT"
        elif effectiveness_score >= 0.2:
            return "MINOR_IMPROVEMENT"
        else:
            return "NEEDS_SIGNIFICANT_WORK"

    def generate_recommendations(self, question_results: List[Dict], model_analysis: Dict) -> List[str]:
        """Genera recomendaciones basadas en resultados"""
        recommendations = []

        # Analizar problemas persistentes
        timeout_issues = [model for model, stats in model_analysis.items() if stats['timeout_rate'] > 0.25]
        no_info_issues = [model for model, stats in model_analysis.items() if stats['no_info_rate'] > 0.25]

        if timeout_issues:
            recommendations.append(
                f"⏰ Timeouts persistentes en {', '.join(timeout_issues)}. "
                f"Considerar aumentar timeouts o reducir contexts más agresivamente."
            )

        if no_info_issues:
            recommendations.append(
                f"❓ Problemas 'no tengo información' en {', '.join(no_info_issues)}. "
                f"Refinar instrucciones de prompts forzando uso de contexts."
            )

        # Analizar preguntas específicas
        for result in question_results:
            q_id = result['question_id']
            effectiveness = result['optimization_effectiveness']

            if effectiveness['effectiveness_score'] < 0.4:
                recommendations.append(
                    f"🎯 P{q_id}: Efectividad baja ({effectiveness['effectiveness_score']:.3f}). "
                    f"Requiere revisión específica de retrieval y prompts."
                )

        # Recomendaciones positivas
        if all(stats['timeout_rate'] < 0.1 for stats in model_analysis.values()):
            recommendations.append(
                "✅ Excelente: Todos los modelos con baja tasa de timeouts."
            )

        return recommendations

    def generate_next_steps(self, overall_effectiveness: float, critical_effectiveness: float) -> List[str]:
        """Genera próximos pasos recomendados"""
        next_steps = []

        if overall_effectiveness >= 0.7 and critical_effectiveness >= 0.7:
            next_steps.extend([
                "🚀 Listo para Fase 3: Implementar debugging RAGAs",
                "📊 Proceder con AB testing comparativo",
                "🔧 Optimizar parámetros de retrieval avanzados"
            ])
        elif overall_effectiveness >= 0.5:
            next_steps.extend([
                "🔧 Refinar optimizaciones en modelos con bajo rendimiento",
                "📈 Implementar mejoras adicionales en prompts",
                "⚡ Optimizar timeouts para modelos lentos"
            ])
        else:
            next_steps.extend([
                "🚨 Revisar fundamentalmente las optimizaciones",
                "🔍 Investigar problemas de retrieval a nivel más profundo",
                "📝 Rediseñar sistema de prompts desde cero"
            ])

        return next_steps

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Ejecuta test comprensivo completo"""
        logger.info("🚀 Iniciando test comprensivo de optimizaciones...")

        if not self.setup():
            return {'error': 'Failed to setup test environment'}

        try:
            # Test preguntas problemáticas
            question_results = self.test_problematic_questions()

            # Test RAG engine
            rag_results = self.test_rag_engine_optimizations()

            # Generar reporte
            report = self.generate_comprehensive_report(question_results, rag_results)

            # Guardar reporte
            output_file = f"results/enhanced_optimization_test_{int(time.time())}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Test completado. Reporte guardado en: {output_file}")

            # Mostrar resumen final
            self.print_final_summary(report)

            return report

        except Exception as e:
            logger.error(f"❌ Error en test comprensivo: {e}")
            return {'error': str(e)}

    def print_final_summary(self, report: Dict[str, Any]):
        """Imprime resumen final del test"""
        print("\n" + "="*80)
        print("🎯 RESUMEN FINAL DE OPTIMIZACIONES - FASE 2")
        print("="*80)

        overall = report['overall_results']
        metadata = report['test_metadata']

        print(f"\n📊 MÉTRICAS GLOBALES:")
        print(f"   Efectividad General: {overall['effectiveness_score']:.3f}")
        print(f"   Efectividad Crítica: {overall['critical_effectiveness']:.3f}")
        print(f"   Nivel de Éxito: {overall['success_level']}")
        print(f"   Preguntas Testeadas: {metadata['total_questions_tested']}")
        print(f"   Modelos Evaluados: {', '.join(metadata['models_tested'])}")

        print(f"\n🏆 MEJORES MODELOS:")
        model_analysis = report['model_analysis']
        sorted_models = sorted(
            model_analysis.items(),
            key=lambda x: (x[1]['timeout_rate'] * -1, x[1]['keyword_success_rate']),
            reverse=True
        )

        for i, (model, stats) in enumerate(sorted_models, 1):
            print(f"   {i}. {model}:")
            print(f"      ✅ Keywords: {stats['keyword_success_rate']:.3f}")
            print(f"      ⏰ Timeouts: {stats['timeout_rate']:.3f}")
            print(f"      ⏱️ Tiempo: {stats['avg_generation_time']:.1f}s")

        print(f"\n📋 RECOMENDACIONES:")
        for i, rec in enumerate(report['recommendations'][:5], 1):
            print(f"   {i}. {rec}")

        print(f"\n🔮 PRÓXIMOS PASOS:")
        for i, step in enumerate(report['next_steps'], 1):
            print(f"   {i}. {step}")

def main():
    """Función principal"""
    print("🚀 Fase 2: Test de Optimizaciones Mejoradas")
    print("=" * 60)

    tester = OptimizationTester()
    report = tester.run_comprehensive_test()

    if 'error' in report:
        print(f"\n❌ Error en ejecución: {report['error']}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())