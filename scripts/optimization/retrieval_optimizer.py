#!/usr/bin/env python3
"""
Fase 4: Optimización avanzada de retrieval
Optimiza top_k, similarity_threshold, query expansion y re-ranking
"""

import json
import time
import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
import statistics

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir paths para imports
import sys
sys.path.append('src')

try:
    from core.enhanced_rag_engine_new import EnhancedRAGEngine
    from core.rag_engine import ConfigurableRAGEngine
except ImportError as e:
    logger.error(f"Error importando módulos: {e}")
    sys.exit(1)

@dataclass
class RetrievalTestResult:
    """Resultado de un test de retrieval"""
    test_name: str
    params: Dict[str, Any]
    question_id: int
    query: str
    retrieved_docs: List[Dict]
    relevance_score: float
    keyword_matches: int
    processing_time: float
    success: bool

class RetrievalOptimizer:
    """Optimizador avanzado de retrieval"""

    def __init__(self):
        self.base_engine = None
        self.enhanced_engine = None
        self.test_queries = self._get_test_queries()

    def _get_test_queries(self) -> Dict[int, Dict]:
        """Queries de test específicas para optimización"""
        return {
            22: {  # CASO CRÍTICO - resis
                "question": "¿Qué se hace en la actividad de resis?",
                "keywords": ["resis", "acollida", "residentes", "pasar tiempo", "actividades"],
                "expected_topics": ["acollida", "actividades con residentes", "miércoles", "alegría"]
            },
            6: {  # CASO TIMEOUT - apuntarse desayunos
                "question": "¿Cómo me apunto a desayunos solidarios?",
                "keywords": ["miércoles", "sábado", "whatsapp", "formulario", "inscribirse"],
                "expected_topics": ["whatsapp", "formulario", "miércoles", "sábado"]
            },
            14: {  # CASO INFO NO USADA - edad niños
                "question": "¿Qué edad tienen los niños en coles?",
                "keywords": ["tres años", "sexto de primaria", "infantil", "primaria", "edades"],
                "expected_topics": ["edades", "infantil", "primaria", "tres años", "sexto"]
            },
            19: {  # CASO TIMEOUT - actividades niños
                "question": "¿Qué otras actividades se hacen relacionadas con niños?",
                "keywords": ["reyes", "navidad", "día del niño", "terra mítica", "verano"],
                "expected_topics": ["terra mítica", "reyes", "día del niño", "actividades"]
            }
        }

    def setup_engines(self):
        """Inicializa los engines de retrieval"""
        try:
            logger.info("🔧 Inicializando engines de retrieval...")
            self.base_engine = ConfigurableRAGEngine("data/vectorstore/chroma_db", use_hybrid=True)
            self.enhanced_engine = EnhancedRAGEngine("data/vectorstore/chroma_db", use_hybrid=True)
            logger.info("✅ Engines inicializados correctamente")
            return True
        except Exception as e:
            logger.error(f"❌ Error inicializando engines: {e}")
            return False

    def test_current_retrieval(self) -> Dict[str, Any]:
        """Testea el retrieval actual para establecer baseline"""
        logger.info("📊 Testeando retrieval actual (baseline)...")

        baseline_results = {}

        for q_id, query_data in self.test_queries.items():
            query = query_data["question"]
            keywords = query_data["keywords"]

            try:
                # Test con engine base
                start_time = time.time()
                base_docs = self.base_engine.retrieve(query)
                base_time = time.time() - start_time

                # Test con enhanced engine
                start_time = time.time()
                enhanced_docs = self.enhanced_engine.retrieve_with_optimization(
                    query, q_id, "gemma2:27b"
                )
                enhanced_time = time.time() - start_time

                # Análisis de relevancia
                base_relevance = self._calculate_relevance_score(base_docs, keywords)
                enhanced_relevance = self._calculate_relevance_score(enhanced_docs, keywords)

                baseline_results[f"Q{q_id}"] = {
                    "question": query,
                    "keywords": keywords,
                    "baseline": {
                        "docs_count": len(base_docs),
                        "relevance_score": base_relevance,
                        "processing_time": base_time
                    },
                    "enhanced": {
                        "docs_count": len(enhanced_docs),
                        "relevance_score": enhanced_relevance,
                        "processing_time": enhanced_time
                    },
                    "improvement": enhanced_relevance - base_relevance
                }

                logger.info(f"   Q{q_id}: Baseline {base_relevance:.3f} → Enhanced {enhanced_relevance:.3f} "
                           f"(+{enhanced_relevance - base_relevance:.3f})")

            except Exception as e:
                logger.error(f"   ❌ Error en Q{q_id}: {e}")
                baseline_results[f"Q{q_id}"] = {"error": str(e)}

        return baseline_results

    def optimize_top_k_and_threshold(self) -> Dict[str, Any]:
        """Optimiza parámetros top_k y similarity_threshold"""
        logger.info("🎯 Optimizando top_k y similarity_threshold...")

        # Rangos de prueba
        top_k_values = [5, 8, 10, 12, 15]
        threshold_values = [0.2, 0.3, 0.35, 0.4, 0.5]

        optimization_results = {}

        for q_id, query_data in self.test_queries.items():
            query = query_data["question"]
            keywords = query_data["keywords"]

            best_config = None
            best_score = 0

            optimization_results[f"Q{q_id}"] = {
                "question": query,
                "tested_configs": [],
                "best_config": None,
                "best_score": 0
            }

            for top_k in top_k_values:
                for threshold in threshold_values:
                    try:
                        # Configurar parámetros
                        self.base_engine.update_params({
                            'top_k': top_k,
                            'similarity_threshold': threshold
                        })

                        # Realizar retrieval
                        docs = self.base_engine.retrieve(query)
                        relevance_score = self._calculate_relevance_score(docs, keywords)

                        config_result = {
                            'top_k': top_k,
                            'similarity_threshold': threshold,
                            'relevance_score': relevance_score,
                            'docs_count': len(docs)
                        }

                        optimization_results[f"Q{q_id}"]["tested_configs"].append(config_result)

                        # Guardar mejor configuración
                        if relevance_score > best_score:
                            best_score = relevance_score
                            best_config = config_result.copy()

                    except Exception as e:
                        logger.warning(f"Error con top_k={top_k}, threshold={threshold}: {e}")

            optimization_results[f"Q{q_id}"]["best_config"] = best_config
            optimization_results[f"Q{q_id}"]["best_score"] = best_score

            logger.info(f"   Q{q_id}: Mejor config: top_k={best_config['top_k'] if best_config else 'N/A'}, "
                       f"threshold={best_config['similarity_threshold'] if best_config else 'N/A'} → "
                       f"Score {best_score:.3f}")

        return optimization_results

    def test_query_expansion(self) -> Dict[str, Any]:
        """Test de expansión de queries para mejorar retrieval"""
        logger.info("🔍 Testeando expansión de queries...")

        expansion_results = {}

        for q_id, query_data in self.test_queries.items():
            original_query = query_data["question"]
            keywords = query_data["keywords"]

            # Generar queries expandidas
            expanded_queries = self._generate_expanded_queries(original_query, keywords)

            expansion_results[f"Q{q_id}"] = {
                "original_query": original_query,
                "keywords": keywords,
                "expanded_queries": expanded_queries,
                "comparisons": []
            }

            # Test original query
            try:
                original_docs = self.base_engine.retrieve(original_query)
                original_relevance = self._calculate_relevance_score(original_docs, keywords)

                expansion_results[f"Q{q_id}"]["comparisons"].append({
                    "query_type": "original",
                    "query": original_query,
                    "relevance_score": original_relevance,
                    "docs_count": len(original_docs)
                })

            except Exception as e:
                logger.error(f"Error con query original Q{q_id}: {e}")

            # Test queries expandidas
            for expanded_query in expanded_queries:
                try:
                    expanded_docs = self.base_engine.retrieve(expanded_query)
                    expanded_relevance = self._calculate_relevance_score(expanded_docs, keywords)

                    expansion_results[f"Q{q_id}"]["comparisons"].append({
                        "query_type": "expanded",
                        "query": expanded_query,
                        "relevance_score": expanded_relevance,
                        "docs_count": len(expanded_docs),
                        "improvement": expanded_relevance - original_relevance
                    })

                    logger.info(f"   Q{q_id} - '{expanded_query[:50]}...': "
                               f"Score {expanded_relevance:.3f} "
                               f"({expanded_relevance - original_relevance:+.3f})")

                except Exception as e:
                    logger.warning(f"Error con query expandida '{expanded_query}': {e}")

        return expansion_results

    def _generate_expanded_queries(self, original_query: str, keywords: List[str]) -> List[str]:
        """Genera queries expandidas usando keywords"""
        expanded_queries = []

        # Añadir keywords importantes a la query
        for keyword in keywords[:3]:  # Top 3 keywords
            if keyword.lower() not in original_query.lower():
                expanded_queries.append(f"{original_query} {keyword}")

        # Queries alternativas
        if "resis" in original_query.lower():
            expanded_queries.extend([
                "actividades con residentes acollida",
                "voluntariado personas mayores",
                "residencia acollida actividades"
            ])

        if "desayunos" in original_query.lower():
            expanded_queries.extend([
                "inscripción voluntariado comida",
                "formulario whatsapp comidas solidarias",
                "apuntarse voluntario desayuno"
            ])

        if "niños" in original_query.lower():
            expanded_queries.extend([
                "actividades infantiles voluntariado",
                "colegio refuerzo escolar",
                "niños centros acogida actividades"
            ])

        return list(set(expanded_queries))  # Eliminar duplicados

    def test_reranking(self) -> Dict[str, Any]:
        """Test de estrategias de re-ranking"""
        logger.info("🏆 Testeando estrategias de re-ranking...")

        reranking_results = {}

        for q_id, query_data in self.test_queries.items():
            query = query_data["question"]
            keywords = query_data["keywords"]

            try:
                # Obtener documentos base
                base_docs = self.base_engine.retrieve(query)

                # Aplicar diferentes estrategias de re-ranking
                reranked_variants = {
                    "keyword_priority": self._rerank_by_keywords(base_docs, keywords),
                    "length_optimized": self._rerank_by_length(base_docs),
                    "hybrid": self._rerank_hybrid(base_docs, keywords)
                }

                reranking_results[f"Q{q_id}"] = {
                    "question": query,
                    "keywords": keywords,
                    "base_docs": len(base_docs),
                    "base_relevance": self._calculate_relevance_score(base_docs, keywords),
                    "reranking_results": {}
                }

                for strategy, reranked_docs in reranked_variants.items():
                    relevance_score = self._calculate_relevance_score(reranked_docs, keywords)

                    reranking_results[f"Q{q_id}"]["reranking_results"][strategy] = {
                        "relevance_score": relevance_score,
                        "docs_count": len(reranked_docs),
                        "improvement": relevance_score - reranking_results[f"Q{q_id}"]["base_relevance"]
                    }

                    logger.info(f"   Q{q_id} - {strategy}: Score {relevance_score:.3f} "
                               f"({relevance_score - reranking_results[f'Q{q_id}']['base_relevance']:+.3f})")

            except Exception as e:
                logger.error(f"Error en re-ranking Q{q_id}: {e}")
                reranking_results[f"Q{q_id}"] = {"error": str(e)}

        return reranking_results

    def _rerank_by_keywords(self, docs: List[Dict], keywords: List[str]) -> List[Dict]:
        """Re-rankea documentos por presencia de keywords"""
        scored_docs = []

        for doc in docs:
            content_lower = doc['content'].lower()
            keyword_score = sum(1 for keyword in keywords if keyword in content_lower)
            scored_docs.append((doc, keyword_score))

        # Ordenar por score de keywords (descendente)
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs]

    def _rerank_by_length(self, docs: List[Dict]) -> List[Dict]:
        """Re-rankea documentos por longitud óptima"""
        scored_docs = []

        for doc in docs:
            length = len(doc['content'])
            # Preferir documentos de longitud media (ni muy cortos ni muy largos)
            if 50 <= length <= 500:
                length_score = 1.0
            elif 30 <= length <= 800:
                length_score = 0.8
            else:
                length_score = 0.5

            scored_docs.append((doc, length_score))

        # Ordenar por score de longitud (descendente)
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs]

    def _rerank_hybrid(self, docs: List[Dict], keywords: List[str]) -> List[Dict]:
        """Re-rankeo híbrido combinando múltiples factores"""
        scored_docs = []

        for doc in docs:
            content_lower = doc['content'].lower()
            length = len(doc['content'])

            # Score de keywords
            keyword_score = sum(1 for keyword in keywords if keyword in content_lower)

            # Score de longitud
            if 50 <= length <= 500:
                length_score = 1.0
            elif 30 <= length <= 800:
                length_score = 0.8
            else:
                length_score = 0.5

            # Score original del documento
            original_score = doc.get('score', 0.5)

            # Score combinado
            combined_score = (keyword_score * 0.5) + (length_score * 0.3) + (original_score * 0.2)
            scored_docs.append((doc, combined_score))

        # Ordenar por score combinado (descendente)
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs]

    def _calculate_relevance_score(self, docs: List[Dict], keywords: List[str]) -> float:
        """Calcula score de relevancia para documentos recuperados"""
        if not docs or not keywords:
            return 0.0

        total_score = 0
        for doc in docs:
            content_lower = doc['content'].lower()
            keyword_matches = sum(1 for keyword in keywords if keyword in content_lower)
            total_score += keyword_matches

        # Normalizar por número de documentos y keywords
        max_possible_score = len(docs) * len(keywords)
        if max_possible_score > 0:
            return total_score / max_possible_score
        return 0.0

    def generate_optimization_report(self, baseline_results: Dict,
                                   optimization_results: Dict,
                                   expansion_results: Dict,
                                   reranking_results: Dict) -> Dict[str, Any]:
        """Genera reporte comprensivo de optimización"""
        logger.info("📋 Generando reporte de optimización...")

        # Análisis de mejoras
        improvements = {}
        for q_id in self.test_queries.keys():
            improvements[f"Q{q_id}"] = {
                "baseline_score": baseline_results.get(f"Q{q_id}", {}).get("baseline", {}).get("relevance_score", 0),
                "optimization_score": optimization_results.get(f"Q{q_id}", {}).get("best_score", 0),
                "improvement": 0,
                "best_config": optimization_results.get(f"Q{q_id}", {}).get("best_config")
            }

            baseline_score = improvements[f"Q{q_id}"]["baseline_score"]
            opt_score = improvements[f"Q{q_id}"]["optimization_score"]
            improvements[f"Q{q_id}"]["improvement"] = opt_score - baseline_score

        # Configuraciones recomendadas
        recommended_configs = self._get_recommended_configs(optimization_results)

        # Próximos pasos
        next_steps = self._generate_next_steps(improvements, recommended_configs)

        return {
            "optimization_metadata": {
                "timestamp": time.time(),
                "tested_questions": list(self.test_queries.keys()),
                "total_tests": len(self.test_queries)
            },
            "baseline_results": baseline_results,
            "parameter_optimization": optimization_results,
            "query_expansion": expansion_results,
            "reranking_results": reranking_results,
            "improvements_summary": improvements,
            "recommended_configs": recommended_configs,
            "next_steps": next_steps,
            "overall_success_rate": self._calculate_success_rate(improvements)
        }

    def _get_recommended_configs(self, optimization_results: Dict) -> Dict[str, Any]:
        """Obtiene configuraciones recomendadas basadas en resultados"""
        configs_by_question = {}

        for q_id, results in optimization_results.items():
            best_config = results.get("best_config")
            if best_config:
                configs_by_question[q_id] = best_config

        # Configuración global recomendada
        if configs_by_question:
            avg_top_k = statistics.mean([c["top_k"] for c in configs_by_question.values()])
            avg_threshold = statistics.mean([c["similarity_threshold"] for c in configs_by_question.values()])

            global_config = {
                "top_k": round(avg_top_k),
                "similarity_threshold": round(avg_threshold, 2)
            }
        else:
            global_config = {
                "top_k": 10,
                "similarity_threshold": 0.35
            }

        return {
            "global_config": global_config,
            "by_question": configs_by_question
        }

    def _generate_next_steps(self, improvements: Dict, configs: Dict) -> List[str]:
        """Genera próximos pasos basados en resultados de optimización"""
        next_steps = []

        # Analizar tasa de éxito
        successful_improvements = [
            q_id for q_id, data in improvements.items()
            if data["improvement"] > 0.1
        ]

        if len(successful_improvements) >= 3:
            next_steps.extend([
                "🚀 Implementar configuraciones optimizadas en producción",
                "📊 Continuar con Fase 5: AB testing comparativo",
                "🔧 Integrar expansión de queries para casos específicos"
            ])
        elif len(successful_improvements) >= 2:
            next_steps.extend([
                "🔧 Refinar optimizaciones en preguntas con mejora baja",
                "📈 Implementar re-ranking híbrido selectivo",
                "⚡ Probar configuraciones intermedias"
            ])
        else:
            next_steps.extend([
                "🔍 Investigar problemas fundamentales de retrieval",
                "📝 Reconsiderar estrategia de chunks y embeddings",
                "🔄 Probar enfoques alternativos de retrieval"
            ])

        # Configuraciones específicas
        if configs.get("global_config"):
            config = configs["global_config"]
            next_steps.append(
                f"🎯 Configuración recomendada: top_k={config['top_k']}, "
                f"threshold={config['similarity_threshold']}"
            )

        return next_steps

    def _calculate_success_rate(self, improvements: Dict) -> float:
        """Calcula tasa de éxito general de optimizaciones"""
        if not improvements:
            return 0.0

        successful_count = sum(
            1 for data in improvements.values()
            if data["improvement"] > 0
        )

        return successful_count / len(improvements)

    def run_complete_optimization(self) -> Dict[str, Any]:
        """Ejecuta optimización completa de retrieval"""
        logger.info("🚀 Iniciando optimización completa de retrieval...")

        if not self.setup_engines():
            return {"error": "Failed to setup retrieval engines"}

        try:
            # 1. Establecer baseline
            logger.info("📊 Paso 1: Estableciendo baseline...")
            baseline_results = self.test_current_retrieval()

            # 2. Optimizar parámetros
            logger.info("🎯 Paso 2: Optimizando parámetros...")
            optimization_results = self.optimize_top_k_and_threshold()

            # 3. Test query expansion
            logger.info("🔍 Paso 3: Testeando expansión de queries...")
            expansion_results = self.test_query_expansion()

            # 4. Test re-ranking
            logger.info("🏆 Paso 4: Testeando re-ranking...")
            reranking_results = self.test_reranking()

            # 5. Generar reporte
            logger.info("📋 Paso 5: Generando reporte...")
            report = self.generate_optimization_report(
                baseline_results, optimization_results,
                expansion_results, reranking_results
            )

            # Guardar reporte
            output_file = f"results/retrieval_optimization_{int(time.time())}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Optimización completada. Reporte guardado en: {output_file}")

            # Mostrar resumen
            self.print_optimization_summary(report)

            return report

        except Exception as e:
            logger.error(f"❌ Error en optimización: {e}")
            return {"error": str(e)}

    def print_optimization_summary(self, report: Dict[str, Any]):
        """Imprime resumen de optimización"""
        print("\n" + "="*80)
        print("🎯 RESUMEN DE OPTIMIZACIÓN DE RETRIEVAL - FASE 4")
        print("="*80)

        improvements = report['improvements_summary']
        success_rate = report['overall_success_rate']
        configs = report['recommended_configs']

        print(f"\n📊 MÉTRICAS GLOBALES:")
        print(f"   Tasa de éxito: {success_rate:.1%}")
        print(f"   Preguntas testeadas: {len(improvements)}")

        print(f"\n🏆 MEJORAS POR PREGUNTA:")
        for q_id, data in improvements.items():
            baseline = data['baseline_score']
            optimized = data['optimization_score']
            improvement = data['improvement']

            print(f"   {q_id}: {baseline:.3f} → {optimized:.3f} ({improvement:+.3f})")

        print(f"\n🎯 CONFIGURACIÓN RECOMENDADA:")
        global_config = configs['global_config']
        print(f"   top_k: {global_config['top_k']}")
        print(f"   similarity_threshold: {global_config['similarity_threshold']}")

        print(f"\n🔮 PRÓXIMOS PASOS:")
        for i, step in enumerate(report['next_steps'][:5], 1):
            print(f"   {i}. {step}")

def main():
    """Función principal"""
    print("🚀 Fase 4: Optimización Avanzada de Retrieval")
    print("=" * 60)

    optimizer = RetrievalOptimizer()
    report = optimizer.run_complete_optimization()

    if 'error' in report:
        print(f"\n❌ Error en optimización: {report['error']}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())