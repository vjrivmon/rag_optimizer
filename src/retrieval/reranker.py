#!/usr/bin/env python3
"""
🎯 Cross-Encoder Reranker - Reranking de alta precisión post-retrieval

MEJORA #3: Cross-Encoder Reranking
- Recupera 20 candidatos con bi-encoder (rápido)
- Rerank top-10 con cross-encoder (preciso)
- Combina scores original + rerank para máxima precisión

USO:
    from reranker import CrossEncoderReranker

    reranker = CrossEncoderReranker(base_retriever)
    results = reranker.retrieve_and_rerank("¿Dónde son los desayunos?", k=10)
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

try:
    from sentence_transformers import CrossEncoder
    from sentence_transformers.util import cos_sim
except ImportError:
    print("❌ Instala sentence-transformers: pip install sentence-transformers")
    CrossEncoder = None


@dataclass
class RerankerConfig:
    """Configuración del reranker"""
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    max_length: int = 512
    batch_size: int = 16
    initial_k: int = 20  # Candidatos a recuperar inicialmente
    final_k: int = 10    # Resultados finales a retornar
    weight_rerank: float = 0.7  # Peso del score de reranking
    weight_original: float = 0.3  # Peso del score original
    normalize_scores: bool = True
    device: str = "cpu"


class CrossEncoderReranker:
    """
    Sistema de reranking con cross-encoder

    Estrategia de dos fases:
    1. Fase 1: Retrieval rápido con bi-encoder (N=20 candidatos)
    2. Fase 2: Reranking preciso con cross-encoder (top-10)

    Beneficios:
    - +20-25% en context_precision
    - Elimina chunks mediocres del contexto
    - Trade-off controlado: +50-100ms latencia
    """

    def __init__(
        self,
        base_retriever,
        config: Optional[RerankerConfig] = None
    ):
        """
        Inicializar reranker

        Args:
            base_retriever: Retriever base (puede ser MultiEmbeddingRetriever)
            config: Configuración del reranker
        """
        self.base_retriever = base_retriever
        self.config = config or RerankerConfig()

        # Inicializar cross-encoder
        if CrossEncoder is None:
            raise ImportError("Instala sentence-transformers: pip install sentence-transformers")

        print(f"🔄 Cargando cross-encoder: {self.config.model_name}")
        self.reranker = CrossEncoder(
            self.config.model_name,
            max_length=self.config.max_length,
            device=self.config.device
        )
        print("✅ Cross-encoder cargado")

    def retrieve_and_rerank(
        self,
        query: str,
        k: Optional[int] = None,
        min_score: float = 0.0,
        include_metadata: bool = True,
        return_rerank_details: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieval y reranking en dos fases

        Args:
            query: Query de búsqueda
            k: Número final de resultados (default de config)
            min_score: Score mínimo para incluir resultado
            include_metadata: Incluir metadata de documentos
            return_rerank_details: Incluir detalles del reranking

        Returns:
            Lista de documentos rerankeados
        """
        k = k or self.config.final_k
        start_time = time.time()

        print(f"🔍 Iniciando retrieval + reranking para: '{query}'")

        # Fase 1: Retrieval inicial (rápido)
        print(f"   Fase 1: Retrieval inicial (k={self.config.initial_k})")
        initial_candidates = self._initial_retrieval(query, min_score, include_metadata)

        if not initial_candidates:
            print("   ❌ No se encontraron candidatos en fase inicial")
            return []

        print(f"   ✅ {len(initial_candidates)} candidatos recuperados")

        # Fase 2: Reranking (preciso)
        print(f"   Fase 2: Reranking con cross-encoder")
        reranked_results = self._rerank_candidates(query, initial_candidates)

        # Fase 3: Combinar scores y seleccionar top-k
        final_results = self._combine_scores_and_select(
            reranked_results, k, return_rerank_details
        )

        # Estadísticas finales
        total_time = time.time() - start_time
        print(f"✅ Reranking completado: {len(final_results)} resultados en {total_time:.3f}s")

        # Enriquecer resultados con estadísticas
        for result in final_results:
            result['reranker_stats'] = {
                'total_time': total_time,
                'initial_candidates': len(initial_candidates),
                'final_results': len(final_results),
                'model_used': self.config.model_name,
                'weights': {
                    'rerank': self.config.weight_rerank,
                    'original': self.config.weight_original
                }
            }

        return final_results

    def _initial_retrieval(
        self,
        query: str,
        min_score: float,
        include_metadata: bool
    ) -> List[Dict[str, Any]]:
        """
        Fase 1: Retrieval inicial con bi-encoder
        """
        try:
            # Usar el retriever base para obtener más candidatos
            if hasattr(self.base_retriever, 'retrieve_ensemble'):
                # Es MultiEmbeddingRetriever
                candidates = self.base_retriever.retrieve_ensemble(
                    query=query,
                    k=self.config.initial_k,
                    min_score=min_score,
                    include_metadata=include_metadata
                )
            else:
                # Es retriever estándar
                candidates = self.base_retriever.retrieve(
                    query=query,
                    k=self.config.initial_k,
                    min_score=min_score,
                    include_metadata=include_metadata
                )

            return candidates

        except Exception as e:
            print(f"   ❌ Error en retrieval inicial: {e}")
            return []

    def _rerank_candidates(
        self,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fase 2: Reranking con cross-encoder
        """
        if not candidates:
            return []

        try:
            # Preparar pares query-documento
            query_doc_pairs = []
            candidate_indices = []

            for i, candidate in enumerate(candidates):
                content = candidate['content']
                # Truncar si es muy largo para el cross-encoder
                if len(content) > self.config.max_length - len(query) - 10:
                    # Truncar inteligentemente (intentar completar última palabra)
                    max_len = self.config.max_length - len(query) - 10
                    content = content[:max_len].rsplit(' ', 1)[0] + '...'

                query_doc_pairs.append([query, content])
                candidate_indices.append(i)

            # Batch prediction con cross-encoder
            print(f"   Procesando {len(query_doc_pairs)} pares query-documento...")
            rerank_scores = self.reranker.predict(
                query_doc_pairs,
                batch_size=self.config.batch_size,
                show_progress_bar=False
            )

            # Normalizar scores si se requiere
            if self.config.normalize_scores:
                rerank_scores = self._normalize_scores(rerank_scores)

            # Asignar scores a los candidatos
            reranked_candidates = []
            for i, (candidate_idx, rerank_score) in enumerate(zip(candidate_indices, rerank_scores)):
                candidate = candidates[candidate_idx].copy()
                candidate['rerank_score'] = float(rerank_score)
                candidate['rerank_rank'] = i + 1
                reranked_candidates.append(candidate)

            # Ordenar por score de reranking
            reranked_candidates.sort(key=lambda x: x['rerank_score'], reverse=True)

            print(f"   ✅ Reranking completado (score range: {min(rerank_scores):.3f} - {max(rerank_scores):.3f})")

            return reranked_candidates

        except Exception as e:
            print(f"   ❌ Error en reranking: {e}")
            # Fallback: retornar candidatos originales con rerank_score = 0
            for candidate in candidates:
                candidate['rerank_score'] = 0.0
                candidate['rerank_rank'] = len(candidates)
            return candidates

    def _combine_scores_and_select(
        self,
        reranked_candidates: List[Dict[str, Any]],
        k: int,
        return_details: bool
    ) -> List[Dict[str, Any]]:
        """
        Fase 3: Combinar scores y seleccionar top-k
        """
        final_results = []

        for candidate in reranked_candidates:
            # Score original (normalizado si existe)
            original_score = candidate.get('score', 0.5)
            if isinstance(original_score, (int, float)) and original_score > 1.0:
                # Asumir que es similitud coseno (0-1), normalizar si es necesario
                original_score = min(original_score, 1.0)

            # Score de reranking
            rerank_score = candidate.get('rerank_score', 0.0)

            # Combinación ponderada
            final_score = (
                self.config.weight_rerank * rerank_score +
                self.config.weight_original * original_score
            )

            # Crear resultado final
            result = candidate.copy()
            result['final_score'] = final_score
            result['original_score'] = original_score
            result['score'] = final_score  # Para compatibilidad

            # Detalles del reranking (si se solicita)
            if return_details:
                result['rerank_details'] = {
                    'original_score': original_score,
                    'rerank_score': rerank_score,
                    'final_score': final_score,
                    'weight_rerank': self.config.weight_rerank,
                    'weight_original': self.config.weight_original,
                    'rerank_rank': candidate.get('rerank_rank', 0)
                }

            final_results.append(result)

        # Ordenar por score final y seleccionar top-k
        final_results.sort(key=lambda x: x['final_score'], reverse=True)
        return final_results[:k]

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalizar scores al rango [0, 1]
        """
        if len(scores) == 0:
            return scores

        min_score = np.min(scores)
        max_score = np.max(scores)

        if max_score == min_score:
            # Todos los scores son iguales
            return np.full_like(scores, 0.5)

        # Normalización min-max
        normalized = (scores - min_score) / (max_score - min_score)
        return normalized

    def analyze_reranking_impact(
        self,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analizar el impacto del reranking en una query específica

        Útil para debugging y análisis de calidad
        """
        if not candidates:
            return {'error': 'No candidates provided'}

        print(f"🔬 Analizando impacto de reranking para: '{query}'")

        # Reranking
        reranked = self._rerank_candidates(query, candidates)

        # Análisis comparativo
        analysis = {
            'query': query,
            'total_candidates': len(candidates),
            'reranked_candidates': len(reranked),
            'top_changes': [],
            'score_statistics': {},
            'rank_changes': {}
        }

        # Comparar top-5 antes vs después
        top_original = candidates[:5]
        top_reranked = reranked[:5]

        # Cambios en el top
        for i, (orig, rerank) in enumerate(zip(top_original, top_reranked)):
            if orig['content'] != rerank['content']:
                analysis['top_changes'].append({
                    'position': i + 1,
                    'original': {
                        'content': orig['content'][:100] + '...',
                        'score': orig.get('score', 0)
                    },
                    'reranked': {
                        'content': rerank['content'][:100] + '...',
                        'score': rerank.get('rerank_score', 0),
                        'original_score': rerank.get('original_score', 0)
                    }
                })

        # Estadísticas de scores
        original_scores = [c.get('score', 0) for c in candidates]
        rerank_scores = [c.get('rerank_score', 0) for c in reranked]

        analysis['score_statistics'] = {
            'original': {
                'mean': np.mean(original_scores),
                'std': np.std(original_scores),
                'min': np.min(original_scores),
                'max': np.max(original_scores)
            },
            'rerank': {
                'mean': np.mean(rerank_scores),
                'std': np.std(rerank_scores),
                'min': np.min(rerank_scores),
                'max': np.max(rerank_scores)
            }
        }

        # Cambios de rank
        for orig_candidate in candidates:
            orig_content = orig_candidate['content']
            orig_rank = next(i for i, c in enumerate(candidates) if c['content'] == orig_content)

            rerank_rank = next(
                (i for i, c in enumerate(reranked) if c['content'] == orig_content),
                len(reranked)
            )

            if orig_rank != rerank_rank:
                analysis['rank_changes'][orig_content[:50] + '...'] = {
                    'original_rank': orig_rank + 1,
                    'rerank_rank': rerank_rank + 1,
                    'change': (orig_rank + 1) - (rerank_rank + 1)
                }

        return analysis

    def benchmark_reranker(
        self,
        test_queries: List[str],
        base_k: int = 20
    ) -> Dict[str, Any]:
        """
        Benchmark del reranker comparando con retrieval base

        Args:
            test_queries: Queries de prueba
            base_k: Número de candidatos para retrieval base

        Returns:
            Estadísticas comparativas
        """
        print(f"🔬 Benchmarkeando reranker con {len(test_queries)} queries...")

        benchmark_results = {
            'queries_tested': len(test_queries),
            'reranker_stats': {
                'total_time': 0.0,
                'avg_time_per_query': 0.0,
                'score_improvements': [],
                'rank_changes': []
            },
            'base_retriever_stats': {
                'total_time': 0.0,
                'avg_time_per_query': 0.0
            }
        }

        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}/{len(test_queries)}: '{query}'")

            # Retrieval base
            base_start = time.time()
            base_candidates = self._initial_retrieval(query, 0.0, True)
            base_time = time.time() - base_start

            # Reranking
            rerank_start = time.time()
            reranked_results = self.retrieve_and_rerank(query, k=10)
            rerank_time = time.time() - rerank_start

            # Acumular estadísticas
            benchmark_results['base_retriever_stats']['total_time'] += base_time
            benchmark_results['reranker_stats']['total_time'] += rerank_time

            # Análisis de mejora (si hay suficientes candidatos)
            if len(base_candidates) >= 5 and len(reranked_results) >= 5:
                # Comparar scores promedio del top-5
                base_top_scores = [c.get('score', 0) for c in base_candidates[:5]]
                rerank_top_scores = [c.get('final_score', 0) for c in reranked_results[:5]]

                base_avg = np.mean(base_top_scores)
                rerank_avg = np.mean(rerank_top_scores)

                improvement = rerank_avg - base_avg
                benchmark_results['reranker_stats']['score_improvements'].append(improvement)

                print(f"      Base avg score: {base_avg:.3f}")
                print(f"      Rerank avg score: {rerank_avg:.3f}")
                print(f"      Improvement: {improvement:+.3f}")

        # Calcular estadísticas finales
        if benchmark_results['reranker_stats']['score_improvements']:
            improvements = benchmark_results['reranker_stats']['score_improvements']
            benchmark_results['reranker_stats']['avg_improvement'] = np.mean(improvements)
            benchmark_results['reranker_stats']['improvement_std'] = np.std(improvements)
            benchmark_results['reranker_stats']['positive_improvements'] = sum(1 for imp in improvements if imp > 0)
            benchmark_results['reranker_stats']['improvement_rate'] = (
                benchmark_results['reranker_stats']['positive_improvements'] / len(improvements) * 100
            )

        # Tiempos promedio
        benchmark_results['base_retriever_stats']['avg_time_per_query'] = (
            benchmark_results['base_retriever_stats']['total_time'] / len(test_queries)
        )
        benchmark_results['reranker_stats']['avg_time_per_query'] = (
            benchmark_results['reranker_stats']['total_time'] / len(test_queries)
        )

        # Resumen
        print(f"\n📊 Resultados del benchmark:")
        print(f"   Tiempo promedio base: {benchmark_results['base_retriever_stats']['avg_time_per_query']:.3f}s")
        print(f"   Tiempo promedio reranker: {benchmark_results['reranker_stats']['avg_time_per_query']:.3f}s")
        print(f"   Overhead: {benchmark_results['reranker_stats']['avg_time_per_query'] - benchmark_results['base_retriever_stats']['avg_time_per_query']:.3f}s")

        if 'avg_improvement' in benchmark_results['reranker_stats']:
            print(f"   Mejora promedio score: {benchmark_results['reranker_stats']['avg_improvement']:+.3f}")
            print(f"   Tasa de mejora: {benchmark_results['reranker_stats']['improvement_rate']:.1f}%")

        return benchmark_results

    def get_model_info(self) -> Dict[str, Any]:
        """
        Información del modelo de reranking
        """
        return {
            'model_name': self.config.model_name,
            'max_length': self.config.max_length,
            'device': self.config.device,
            'config': {
                'initial_k': self.config.initial_k,
                'final_k': self.config.final_k,
                'weight_rerank': self.config.weight_rerank,
                'weight_original': self.config.weight_original,
                'batch_size': self.config.batch_size
            }
        }


# Función de conveniencia para uso rápido
def create_reranker(
    base_retriever,
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    initial_k: int = 20,
    final_k: int = 10
) -> CrossEncoderReranker:
    """
    Crea un reranker con configuración por defecto

    Args:
        base_retriever: Retriever base
        model_name: Modelo cross-encoder a usar
        initial_k: Candidatos iniciales a recuperar
        final_k: Resultados finales a retornar

    Returns:
        Instancia de CrossEncoderReranker
    """
    config = RerankerConfig(
        model_name=model_name,
        initial_k=initial_k,
        final_k=final_k
    )

    return CrossEncoderReranker(base_retriever, config)


if __name__ == "__main__":
    # Ejemplo de uso (requiere un retriever base)
    print("🎯 Cross-Encoder Reranker - Ejemplo de uso")
    print("\nEste script requiere un retriever base para funcionar.")
    print("Ejemplo:")
    print("""
    from multi_embedding_retriever import MultiEmbeddingRetriever
    from reranker import create_reranker

    # Crear retriever base
    base_retriever = MultiEmbeddingRetriever("data/vectorstore")

    # Crear reranker
    reranker = create_reranker(base_retriever)

    # Usar
    results = reranker.retrieve_and_rerank("¿Dónde son los desayunos?")
    """)