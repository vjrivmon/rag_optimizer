#!/usr/bin/env python3
"""
🔍 Multi-Embedding Retriever - Ensemble de embeddings para retrieval robusto

MEJORA #2: Multi-Embedding Ensemble
- 3 modelos de embeddings especializados
- Reciprocal Rank Fusion (RRF) para fusionar resultados
- Recuperación más robusta ante variaciones de query

USO:
    from multi_embedding_retriever import MultiEmbeddingRetriever

    retriever = MultiEmbeddingRetriever(vector_store_path="data/vectorstore")
    results = retriever.retrieve_ensemble("¿Dónde son los desayunos?", k=10)
"""

import os
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

try:
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Por favor instala: pip install langchain chromadb scikit-learn")
    exit(1)


@dataclass
class RetrievalConfig:
    """Configuración del retriever multi-embedding"""
    models_config: Dict[str, Dict[str, Any]]
    rrf_k: int = 60  # Parámetro k para Reciprocal Rank Fusion
    weight_ensemble: Dict[str, float] = None  # Pesos por modelo (opcional)
    cache_enabled: bool = True
    cache_size: int = 1000


class EmbeddingCache:
    """Cache simple para embeddings de queries"""

    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []

    def get(self, query: str, model_name: str) -> Optional[np.ndarray]:
        """Obtener embedding del cache"""
        key = f"{model_name}:{query}"
        if key in self.cache:
            # Mover al final de orden de acceso
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def set(self, query: str, model_name: str, embedding: np.ndarray):
        """Guardar embedding en cache"""
        key = f"{model_name}:{query}"

        # Si excede tamaño, remover más antiguo
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]

        self.cache[key] = embedding
        if key not in self.access_order:
            self.access_order.append(key)

    def clear(self):
        """Limpiar cache"""
        self.cache.clear()
        self.access_order.clear()


class MultiEmbeddingRetriever:
    """
    Retriever con ensemble de múltiples modelos de embeddings

    Estrategia:
    1. Modelo semántico general (actual mpnet-base-v2)
    2. Modelo especializado en Q&A (multi-qa-mpnet-base)
    3. Modelo multi-idioma (distiluse-base-multilingual)
    4. Fusionar resultados con Reciprocal Rank Fusion
    """

    def __init__(
        self,
        vector_store_path: str,
        config: Optional[RetrievalConfig] = None
    ):
        """
        Inicializar retriever multi-embedding

        Args:
            vector_store_path: Path base para vector stores
            config: Configuración opcional
        """
        self.base_path = vector_store_path
        self.config = config or self._get_default_config()

        # Inicializar cache
        self.cache = EmbeddingCache(self.config.cache_size) if self.config.cache_enabled else None

        # Inicializar modelos de embeddings
        self.embedders = {}
        self.stores = {}
        self._initialize_embeddings()

    def _get_default_config(self) -> RetrievalConfig:
        """Configuración por defecto"""
        return RetrievalConfig(
            models_config={
                'semantic': {
                    'model_name': "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
                    'device': 'cpu',
                    'normalize_embeddings': True
                },
                'qa': {
                    'model_name': "sentence-transformers/multi-qa-mpnet-base-dot-v1",
                    'device': 'cpu',
                    'normalize_embeddings': True
                },
                'multilingual': {
                    'model_name': "sentence-transformers/distiluse-base-multilingual-cased-v2",
                    'device': 'cpu',
                    'normalize_embeddings': True
                }
            },
            rrf_k=60,
            weight_ensemble={
                'semantic': 0.4,
                'qa': 0.4,
                'multilingual': 0.2
            }
        )

    def _initialize_embeddings(self):
        """Inicializar modelos de embeddings y vector stores"""
        print("🔄 Inicializando embeddings multi-modelo...")

        for model_name, model_config in self.config.models_config.items():
            try:
                print(f"   Cargando modelo: {model_config['model_name']}")

                # Crear embedder
                embedder = HuggingFaceEmbeddings(
                    model_name=model_config['model_name'],
                    model_kwargs={'device': model_config['device']},
                    encode_kwargs={
                        'normalize_embeddings': model_config.get('normalize_embeddings', False),
                        'batch_size': 32
                    }
                )

                # Crear vector store para este modelo
                store_path = f"{self.base_path}_{model_name}"
                store = Chroma(
                    persist_directory=store_path,
                    embedding_function=embedder
                )

                self.embedders[model_name] = embedder
                self.stores[model_name] = store

                print(f"   ✅ {model_name} cargado")

            except Exception as e:
                print(f"   ❌ Error cargando {model_name}: {e}")
                continue

        if not self.embedders:
            raise RuntimeError("❌ No se pudo cargar ningún modelo de embeddings")

        print(f"✅ Cargados {len(self.embedders)} modelos de embeddings")

    def retrieve_ensemble(
        self,
        query: str,
        k: int = 10,
        min_score: float = 0.0,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieval usando ensemble de embeddings

        Args:
            query: Query de búsqueda
            k: Número de resultados a retornar
            min_score: Score mínimo para incluir resultado
            include_metadata: Incluir metadata de documentos

        Returns:
            Lista de documentos con scores ensemble
        """
        if not self.embedders:
            return []

        start_time = time.time()

        # Recuperar con cada modelo
        all_results = []
        retrieval_stats = {}

        for model_name, store in self.stores.items():
            try:
                model_start = time.time()

                # Retrieval con este modelo
                docs = store.similarity_search_with_score(query, k=k * 2)  # Obtener más para mejor fusión

                # Procesar resultados
                model_results = []
                for doc, score in docs:
                    if score >= min_score:
                        result = {
                            'content': doc.page_content,
                            'metadata': doc.metadata if include_metadata else {},
                            'score': float(score),
                            'source_model': model_name
                        }
                        model_results.append(result)

                all_results.extend(model_results)

                # Estadísticas
                model_time = time.time() - model_start
                retrieval_stats[model_name] = {
                    'retrieved': len(model_results),
                    'time': model_time
                }

                print(f"   {model_name}: {len(model_results)} docs en {model_time:.2f}s")

            except Exception as e:
                print(f"   ❌ Error en retrieval con {model_name}: {e}")
                retrieval_stats[model_name] = {'retrieved': 0, 'time': 0, 'error': str(e)}
                continue

        # Fusionar resultados con RRF
        fused_results = self._reciprocal_rank_fusion(all_results, k)

        # Enriquecer con estadísticas
        total_time = time.time() - start_time

        for result in fused_results:
            result['ensemble_stats'] = {
                'total_retrieval_time': total_time,
                'models_used': list(self.stores.keys()),
                'retrieval_stats': retrieval_stats
            }

        print(f"✅ Ensemble retrieval: {len(fused_results)} resultados en {total_time:.2f}s")

        return fused_results

    def _reciprocal_rank_fusion(
        self,
        results: List[Dict[str, Any]],
        k: int,
        rrf_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF)

        Fórmula: score(doc) = Σ 1/(k + rank_i)
        donde rank_i es la posición del doc en el ranking i

        Args:
            results: Lista de resultados de todos los modelos
            k: Número final de resultados
            rrf_k: Parámetro k para RRF (default de config)

        Returns:
            Lista de resultados fusionados y ordenados
        """
        if not results:
            return []

        rrf_k = rrf_k or self.config.rrf_k

        # Agrupar por contenido (eliminar duplicados)
        doc_groups = {}

        for result in results:
            content = result['content']
            content_hash = hash(content)

            if content_hash not in doc_groups:
                doc_groups[content_hash] = {
                    'content': content,
                    'metadata': result['metadata'],
                    'source_models': [],
                    'original_scores': [],
                    'ranks': []
                }

            # Agregar información de este resultado
            group = doc_groups[content_hash]
            group['source_models'].append(result['source_model'])
            group['original_scores'].append(result['score'])

        # Calcular RRF score para cada grupo
        for model_name, store in self.stores.items():
            # Filtrar resultados de este modelo y ordenar por score
            model_results = [
                r for r in results if r['source_model'] == model_name
            ]
            model_results.sort(key=lambda x: x['score'], reverse=True)

            # Asignar rank y calcular contribución RRF
            for rank, result in enumerate(model_results, 1):
                content_hash = hash(result['content'])
                if content_hash in doc_groups:
                    rrf_score = 1.0 / (rrf_k + rank)
                    doc_groups[content_hash]['ranks'].append((model_name, rank, rrf_score))

        # Calcular score final
        final_results = []
        for content_hash, group in doc_groups.items():
            # Sumar scores RRF
            rrf_total = sum(rank_info[2] for rank_info in group['ranks'])

            # Score final combinado
            final_score = rrf_total

            # Si hay pesos definidos, aplicarlos
            if self.config.weight_ensemble:
                weighted_score = 0.0
                for model_name, weight in self.config.weight_ensemble.items():
                    if model_name in group['source_models']:
                        # Encontrar el rank para este modelo
                        model_rank = next(
                            (r[1] for r in group['ranks'] if r[0] == model_name),
                            len(results)  # Si no aparece, asignar rank bajo
                        )
                        model_rrf = 1.0 / (rrf_k + model_rank)
                        weighted_score += weight * model_rrf

                final_score = weighted_score

            result = {
                'content': group['content'],
                'metadata': group['metadata'],
                'score': final_score,
                'rrf_score': rrf_total,
                'source_models': list(set(group['source_models'])),
                'model_count': len(set(group['source_models'])),
                'original_scores': group['original_scores'],
                'ranks_detail': group['ranks']
            }

            final_results.append(result)

        # Ordenar por score final y retornar top-k
        final_results.sort(key=lambda x: x['score'], reverse=True)
        return final_results[:k]

    def get_embedding_similarity_analysis(
        self,
        query: str,
        doc: str
    ) -> Dict[str, float]:
        """
        Análisis de similitud de query-documento con todos los modelos

        Útil para debugging y análisis de calidad de retrieval
        """
        similarities = {}

        for model_name, embedder in self.embedders.items():
            try:
                # Embed query y documento
                query_embedding = embedder.embed_query(query)
                doc_embedding = embedder.embed_query(doc)

                # Calcular similitud coseno
                query_embedding = np.array(query_embedding).reshape(1, -1)
                doc_embedding = np.array(doc_embedding).reshape(1, -1)

                similarity = cosine_similarity(query_embedding, doc_embedding)[0][0]
                similarities[model_name] = float(similarity)

            except Exception as e:
                similarities[model_name] = 0.0
                print(f"Error calculando similitud con {model_name}: {e}")

        # Calcular similitud promedio
        similarities['ensemble_average'] = np.mean(list(similarities.values()))

        return similarities

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Estadísticas de los vector stores
        """
        stats = {
            'models_loaded': list(self.embedders.keys()),
            'vector_stores': {},
            'cache_stats': {}
        }

        # Estadísticas por modelo
        for model_name, store in self.stores.items():
            try:
                collection = store._collection
                stats['vector_stores'][model_name] = {
                    'count': collection.count(),
                    'metadata_fields': collection.metadata or {}
                }
            except Exception as e:
                stats['vector_stores'][model_name] = {'error': str(e)}

        # Estadísticas del cache
        if self.cache:
            stats['cache_stats'] = {
                'size': len(self.cache.cache),
                'max_size': self.cache.max_size,
                'utilization': len(self.cache.cache) / self.cache.max_size * 100
            }

        return stats

    def clear_cache(self):
        """Limpiar cache de embeddings"""
        if self.cache:
            self.cache.clear()
            print("✅ Cache de embeddings limpiado")

    def benchmark_models(
        self,
        test_queries: List[str],
        k: int = 10
    ) -> Dict[str, Any]:
        """
        Benchmark comparativo de los modelos de embeddings

        Args:
            test_queries: Lista de queries de prueba
            k: Número de resultados a recuperar

        Returns:
            Estadísticas comparativas por modelo
        """
        print(f"🔬 Benchmarkeando {len(self.embedders)} modelos con {len(test_queries)} queries...")

        benchmark_results = {}

        for model_name, store in self.stores.items():
            model_stats = {
                'total_time': 0.0,
                'total_results': 0,
                'avg_score': 0.0,
                'queries_processed': 0,
                'errors': 0
            }

            scores = []

            for query in test_queries:
                try:
                    start_time = time.time()

                    docs = store.similarity_search_with_score(query, k=k)

                    query_time = time.time() - start_time
                    model_stats['total_time'] += query_time
                    model_stats['total_results'] += len(docs)
                    model_stats['queries_processed'] += 1

                    # Acumular scores
                    for _, score in docs:
                        scores.append(score)

                except Exception as e:
                    model_stats['errors'] += 1
                    print(f"   ❌ Error en query '{query}' con {model_name}: {e}")

            # Calcular estadísticas finales
            if scores:
                model_stats['avg_score'] = np.mean(scores)
                model_stats['min_score'] = np.min(scores)
                model_stats['max_score'] = np.max(scores)

            if model_stats['queries_processed'] > 0:
                model_stats['avg_time_per_query'] = model_stats['total_time'] / model_stats['queries_processed']
                model_stats['avg_results_per_query'] = model_stats['total_results'] / model_stats['queries_processed']

            benchmark_results[model_name] = model_stats

        # Comparación con ensemble
        print("\n📊 Resultados del benchmark:")
        for model_name, stats in benchmark_results.items():
            print(f"\n🤖 {model_name}:")
            print(f"   Queries procesadas: {stats['queries_processed']}/{len(test_queries)}")
            print(f"   Tiempo promedio: {stats.get('avg_time_per_query', 0):.3f}s")
            print(f"   Score promedio: {stats['avg_score']:.3f}")
            print(f"   Resultados promedio: {stats.get('avg_results_per_query', 0):.1f}")
            print(f"   Errores: {stats['errors']}")

        return benchmark_results


# Función de conveniencia para uso rápido
def create_multi_embedding_retriever(
    vector_store_path: str,
    models: Optional[List[str]] = None
) -> MultiEmbeddingRetriever:
    """
    Crea un retriever multi-embedding con configuración por defecto

    Args:
        vector_store_path: Path base para vector stores
        models: Lista de modelos a usar ['semantic', 'qa', 'multilingual']

    Returns:
        Instancia de MultiEmbeddingRetriever
    """
    config = RetrievalConfig(
        models_config={
            'semantic': {
                'model_name': "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
                'device': 'cpu'
            },
            'qa': {
                'model_name': "sentence-transformers/multi-qa-mpnet-base-dot-v1",
                'device': 'cpu'
            },
            'multilingual': {
                'model_name': "sentence-transformers/distiluse-base-multilingual-cased-v2",
                'device': 'cpu'
            }
        }
    )

    # Filtrar modelos si se especifica
    if models:
        filtered_config = {}
        for model in models:
            if model in config.models_config:
                filtered_config[model] = config.models_config[model]
        config.models_config = filtered_config

    return MultiEmbeddingRetriever(vector_store_path, config)


if __name__ == "__main__":
    # Ejemplo de uso
    retriever = MultiEmbeddingRetriever("data/vectorstore")

    # Query de prueba
    query = "¿Dónde se realizan los desayunos solidarios?"

    # Retrieval con ensemble
    results = retriever.retrieve_ensemble(query, k=5)

    print(f"\n🔍 Resultados para: '{query}'")
    for i, result in enumerate(results, 1):
        print(f"\n--- Resultado {i} ---")
        print(f"Score: {result['score']:.4f}")
        print(f"Modelos: {result['source_models']}")
        print(f"Contenido: {result['content'][:100]}...")

    # Análisis de similitud
    if results:
        similarity_analysis = retriever.get_embedding_similarity_analysis(
            query, results[0]['content']
        )
        print(f"\n📈 Análisis de similitud: {similarity_analysis}")