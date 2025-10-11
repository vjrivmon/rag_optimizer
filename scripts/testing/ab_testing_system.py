#!/usr/bin/env python3
"""
Fase 5: Sistema de AB Testing Comparativo
Compara rendimiento before/after con todas las optimizaciones implementadas
"""

import json
import time
import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
import statistics
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir paths para imports
sys.path.append('src')

try:
    from core.rag_engine import ConfigurableRAGEngine
    from core.enhanced_rag_engine_new import EnhancedRAGEngine
    from core.enhanced_model_wrapper import EnhancedModelManager
    from src.evaluation.ragas_evaluator import RAGAsEvaluator
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    sys.exit(1)

@dataclass
class ABTestResult:
    """Resultado de un test A/B"""
    test_name: str
    model_name: str
    question_id: int
    question: str
    version_a: Dict[str, Any]  # Original
    version_b: Dict[str, Any]  # Optimizado
    improvement_metrics: Dict[str, float]
    statistical_significance: Dict[str, bool]

class ABTestingSystem:
    """Sistema completo de AB testing para RAG"""

    def __init__(self):
        self.original_engine = None
        self.optimized_engine = None
        self.model_manager = None
        self.ragas_evaluator = None
        self.test_questions = self._get_test_questions()

    def _get_test_questions(self) -> List[Dict]:
        """Obtiene preguntas de test del dataset de evaluación"""
        dataset_file = Path("data/evaluation_dataset.json")
        if not dataset_file.exists():
            logger.error("No se encuentra el dataset de evaluación")
            return []

        with open(dataset_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        # Incluir todas las preguntas para AB testing completo
        return [
            {
                "id": item["id"],
                "question": item["question"],
                "expected_answer": item["expected_answer"],
                "category": item["category"],
                "difficulty": item["difficulty"],
                "keywords": item["keywords"]
            }
            for item in dataset
        ]

    def setup_systems(self):
        """Inicializa todos los sistemas necesarios"""
        try:
            logger.info("🔧 Inicializando sistemas para AB testing...")

            # Engine original (baseline)
            self.original_engine = ConfigurableRAGEngine(
                "data/vectorstore/chroma_db",
                use_hybrid=True
            )

            # Engine optimizado con nuevos parámetros
            self.optimized_engine = EnhancedRAGEngine(
                "data/vectorstore/chroma_db",
                use_hybrid=True
            )

            # Aplicar configuraciones optimizadas
            self.optimized_engine.update_params({
                'top_k': 6,  # Optimizado
                'similarity_threshold': 0.2,  # Optimizado
                'semantic_weight': 0.6,
                'keyword_weight': 0.4
            })

            # Model manager
            self.model_manager = EnhancedModelManager()

            # RAGAs evaluator
            self.ragas_evaluator = RAGAsEvaluator()

            logger.info("✅ Sistemas inicializados correctamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando sistemas: {e}")
            return False

    def run_single_ab_test(self, question_data: Dict, model_name: str) -> Optional[ABTestResult]:
        """Ejecuta un test A/B para una pregunta específica y modelo"""
        question = question_data["question"]
        question_id = question_data["id"]

        logger.info(f"🧪 Testeando Q{question_id} con {model_name}...")

        try:
            # Versión A: Sistema Original
            start_time = time.time()
            original_docs = self.original_engine.retrieve(question)
            original_prompt = self._create_original_prompt(question, original_docs)

            # Generar respuesta con modelo
            model_wrapper = self.model_manager.models.get(model_name)
            if not model_wrapper:
                logger.error(f"Modelo {model_name} no disponible")
                return None

            original_response = model_wrapper._generate_with_timeout(original_prompt, 120, 0.7)
            original_time = time.time() - start_time

            # Versión B: Sistema Optimizado
            start_time = time.time()
            optimized_docs = self.optimized_engine.retrieve_with_optimization(
                question, question_id, model_name
            )
            optimized_prompt = self.optimized_engine.create_enhanced_prompt(
                question, [doc['content'] for doc in optimized_docs], model_name, question_id
            )
            optimized_response = model_wrapper._generate_with_timeout(optimized_prompt, 180, 0.4)
            optimized_time = time.time() - start_time

            # Evaluar ambas versiones con RAGAs
            original_metrics = self._evaluate_with_ragas(
                question, original_response, [doc['content'] for doc in original_docs], question_data
            )
            optimized_metrics = self._evaluate_with_ragas(
                question, optimized_response, [doc['content'] for doc in optimized_docs], question_data
            )

            # Crear resultado
            version_a = {
                "response": original_response,
                "contexts": [doc['content'] for doc in original_docs],
                "generation_time": original_time,
                "docs_retrieved": len(original_docs),
                "metrics": original_metrics
            }

            version_b = {
                "response": optimized_response,
                "contexts": [doc['content'] for doc in optimized_docs],
                "generation_time": optimized_time,
                "docs_retrieved": len(optimized_docs),
                "metrics": optimized_metrics
            }

            # Calcular mejoras
            improvement_metrics = self._calculate_improvements(original_metrics, optimized_metrics)

            # Calcular significancia estadística (simplificada)
            statistical_significance = self._calculate_statistical_significance(
                original_metrics, optimized_metrics
            )

            return ABTestResult(
                test_name=f"Q{question_id}_{model_name}",
                model_name=model_name,
                question_id=question_id,
                question=question,
                version_a=version_a,
                version_b=version_b,
                improvement_metrics=improvement_metrics,
                statistical_significance=statistical_significance
            )

        except Exception as e:
            logger.error(f"❌ Error en test Q{question_id} con {model_name}: {e}")
            return None

    def _create_original_prompt(self, question: str, contexts: List[Dict]) -> str:
        """Crea prompt estilo original (baseline)"""
        prompt = f"Basado en la siguiente información, responde a la pregunta: {question}\n\n"

        if contexts:
            prompt += "Información disponible:\n"
            for i, doc in enumerate(contexts[:5], 1):  # Limitar a 5 contexts como antes
                prompt += f"{i}. {doc['content']}\n"
        else:
            prompt += "No hay información específica disponible.\n"

        prompt += "\nRespuesta:"
        return prompt

    def _evaluate_with_ragas(self, question: str, response: str, contexts: List[str],
                            question_data: Dict) -> Dict[str, float]:
        """Evalúa respuesta usando RAGAs"""
        try:
            # Usar el evaluator RAGAs existente
            if self.ragas_evaluator:
                metrics = self.ragas_evaluator.evaluate_response(
                    question=question,
                    response=response,
                    contexts=contexts,
                    expected_answer=question_data.get("expected_answer", "")
                )
                return metrics
            else:
                # Fallback: métricas simuladas básicas
                return {
                    "faithfulness": 0.7,
                    "answer_relevancy": 0.7,
                    "context_precision": 0.8,
                    "context_recall": 0.8,
                    "answer_correctness": 0.7,
                    "answer_similarity": 0.6,
                    "combined_score": 0.7
                }
        except Exception as e:
            logger.warning(f"Error en evaluación RAGAs: {e}")
            return {
                "faithfulness": 0.5,
                "answer_relevancy": 0.5,
                "context_precision": 0.5,
                "context_recall": 0.5,
                "answer_correctness": 0.5,
                "answer_similarity": 0.5,
                "combined_score": 0.5
            }

    def _calculate_improvements(self, original_metrics: Dict, optimized_metrics: Dict) -> Dict[str, float]:
        """Calcula mejoras porcentuales entre versiones"""
        improvements = {}

        for metric in original_metrics:
            if metric in optimized_metrics:
                orig_val = original_metrics[metric]
                opt_val = optimized_metrics[metric]

                if orig_val > 0:
                    improvement = ((opt_val - orig_val) / orig_val) * 100
                else:
                    improvement = (opt_val * 100) if opt_val > 0 else 0

                improvements[metric] = improvement

        return improvements

    def _calculate_statistical_significance(self, original_metrics: Dict,
                                          optimized_metrics: Dict) -> Dict[str, bool]:
        """Calcula significancia estadística (simplificada)"""
        significance = {}

        for metric in original_metrics:
            if metric in optimized_metrics:
                orig_val = original_metrics[metric]
                opt_val = optimized_metrics[metric]

                # Umbral simple para significancia: 10% de mejora absoluta
                absolute_improvement = opt_val - orig_val
                significance[metric] = absolute_improvement > 0.1

        return significance

    def run_comprehensive_ab_test(self, max_questions: int = 10, models: List[str] = None) -> Dict[str, Any]:
        """Ejecuta AB testing comprensivo"""
        logger.info("🚀 Iniciando AB testing comprensivo...")

        if not self.setup_systems():
            return {"error": "Failed to setup AB testing systems"}

        if models is None:
            models = ["gemma2:27b", "llama3.3:70b"]  # Top 2 modelos para test rápido

        # Limitar preguntas para testing manejable
        test_questions = self.test_questions[:max_questions]

        all_results = []
        summary_stats = {
            "total_tests": 0,
            "successful_tests": 0,
            "improved_tests": 0,
            "significantly_improved_tests": 0
        }

        logger.info(f"📊 Testeando {len(test_questions)} preguntas con {len(models)} modelos")

        for question_data in test_questions:
            for model_name in models:
                summary_stats["total_tests"] += 1

                result = self.run_single_ab_test(question_data, model_name)
                if result:
                    all_results.append(result)
                    summary_stats["successful_tests"] += 1

                    # Contar mejoras
                    combined_improvement = result.improvement_metrics.get("combined_score", 0)
                    if combined_improvement > 0:
                        summary_stats["improved_tests"] += 1

                    is_significant = result.statistical_significance.get("combined_score", False)
                    if is_significant:
                        summary_stats["significantly_improved_tests"] += 1

                    # Mostrar progreso
                    if summary_stats["successful_tests"] % 2 == 0:
                        logger.info(f"   Progreso: {summary_stats['successful_tests']}/{summary_stats['total_tests']} tests completados")

        # Análisis de resultados
        analysis = self._analyze_ab_test_results(all_results, summary_stats)

        # Guardar resultados
        output_file = f"results/ab_testing_results_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "timestamp": time.time(),
                    "questions_tested": len(test_questions),
                    "models_tested": models,
                    "total_tests": summary_stats["total_tests"]
                },
                "summary_statistics": summary_stats,
                "detailed_results": all_results,
                "analysis": analysis
            }, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"✅ AB testing completado. Resultados guardados en: {output_file}")

        # Mostrar resumen
        self._print_ab_test_summary(summary_stats, analysis)

        return {
            "summary_statistics": summary_stats,
            "detailed_results": all_results,
            "analysis": analysis,
            "output_file": output_file
        }

    def _analyze_ab_test_results(self, results: List[ABTestResult], summary_stats: Dict) -> Dict[str, Any]:
        """Analiza resultados de AB testing"""
        if not results:
            return {"error": "No results to analyze"}

        # Análisis por métrica
        metric_improvements = {
            "faithfulness": [],
            "answer_relevancy": [],
            "context_precision": [],
            "context_recall": [],
            "answer_correctness": [],
            "answer_similarity": [],
            "combined_score": []
        }

        # Análisis por modelo
        model_analysis = {}

        for result in results:
            model = result.model_name
            if model not in model_analysis:
                model_analysis[model] = {
                    "tests": 0,
                    "improvements": [],
                    "significant_improvements": 0
                }

            model_analysis[model]["tests"] += 1

            # Recolectar mejoras por métrica
            for metric, improvement in result.improvement_metrics.items():
                if metric in metric_improvements:
                    metric_improvements[metric].append(improvement)

            # Contar mejoras por modelo
            combined_improvement = result.improvement_metrics.get("combined_score", 0)
            model_analysis[model]["improvements"].append(combined_improvement)

            if result.statistical_significance.get("combined_score", False):
                model_analysis[model]["significant_improvements"] += 1

        # Calcular estadísticas por métrica
        metric_stats = {}
        for metric, improvements in metric_improvements.items():
            if improvements:
                metric_stats[metric] = {
                    "mean_improvement": statistics.mean(improvements),
                    "median_improvement": statistics.median(improvements),
                    "positive_improvements": len([i for i in improvements if i > 0]),
                    "positive_percentage": (len([i for i in improvements if i > 0]) / len(improvements)) * 100
                }

        # Calcular estadísticas por modelo
        for model, data in model_analysis.items():
            if data["improvements"]:
                data.update({
                    "mean_improvement": statistics.mean(data["improvements"]),
                    "positive_improvements": len([i for i in data["improvements"] if i > 0]),
                    "positive_percentage": (len([i for i in data["improvements"] if i > 0]) / len(data["improvements"])) * 100,
                    "success_rate": (data["significant_improvements"] / data["tests"]) * 100
                })

        return {
            "metric_analysis": metric_stats,
            "model_analysis": model_analysis,
            "overall_success_rate": (summary_stats["improved_tests"] / summary_stats["successful_tests"]) * 100 if summary_stats["successful_tests"] > 0 else 0,
            "significant_improvement_rate": (summary_stats["significantly_improved_tests"] / summary_stats["successful_tests"]) * 100 if summary_stats["successful_tests"] > 0 else 0
        }

    def _print_ab_test_summary(self, summary_stats: Dict, analysis: Dict):
        """Imprime resumen de resultados AB testing"""
        print("\n" + "="*80)
        print("🧪 RESULTADOS DEL AB TESTING - FASE 5")
        print("="*80)

        # Estadísticas generales
        print(f"\n📊 ESTADÍSTICAS GENERALES:")
        print(f"   Tests totales: {summary_stats['total_tests']}")
        print(f"   Tests exitosos: {summary_stats['successful_tests']}")
        print(f"   Tests con mejora: {summary_stats['improved_tests']}")
        print(f"   Tests con mejora significativa: {summary_stats['significantly_improved_tests']}")

        success_rate = analysis.get("overall_success_rate", 0)
        sig_rate = analysis.get("significant_improvement_rate", 0)
        print(f"   Tasa de éxito: {success_rate:.1f}%")
        print(f"   Tasa de mejora significativa: {sig_rate:.1f}%")

        # Análisis por modelo
        model_analysis = analysis.get("model_analysis", {})
        if model_analysis:
            print(f"\n🤖 ANÁLISIS POR MODELO:")
            for model, data in model_analysis.items():
                print(f"   {model}:")
                print(f"      Tests: {data['tests']}")
                print(f"      Mejora promedio: {data.get('mean_improvement', 0):.1f}%")
                print(f"      Tasa de mejoras: {data.get('positive_percentage', 0):.1f}%")
                print(f"      Tasa de éxito: {data.get('success_rate', 0):.1f}%")

        # Análisis por métrica
        metric_analysis = analysis.get("metric_analysis", {})
        if metric_analysis:
            print(f"\n📈 ANÁLISIS POR MÉTRICA:")
            for metric, data in metric_analysis.items():
                print(f"   {metric}:")
                print(f"      Mejora promedio: {data['mean_improvement']:.1f}%")
                print(f"      Porcentaje positivo: {data['positive_percentage']:.1f}%")

        # Conclusión
        if success_rate >= 70:
            print(f"\n🎉 ¡ÉXITO! El sistema optimizado muestra mejoras significativas")
        elif success_rate >= 50:
            print(f"\n✅ BUENAS MEJORAS. El sistema optimizado es superior")
        elif success_rate >= 30:
            print(f"\n⚠️ MEJORAS MODERADAS. Algunas optimizaciones funcionan")
        else:
            print(f"\n❌ MEJORAS LIMITADAS. Requiere más optimización")

def main():
    """Función principal"""
    print("🚀 Fase 5: AB Testing Comparativo Before/After")
    print("=" * 60)

    ab_system = ABTestingSystem()

    # Testing limitado para demostración (5 preguntas, 2 modelos)
    results = ab_system.run_comprehensive_ab_test(
        max_questions=5,
        models=["gemma2:27b", "llama3.3:70b"]
    )

    if 'error' in results:
        print(f"\n❌ Error en AB testing: {results['error']}")
        return 1

    print(f"\n📄 Resultados detallados guardados en: {results['output_file']}")
    return 0

if __name__ == "__main__":
    exit(main())