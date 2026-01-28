"""
🚀 Enhanced RAG Engine v2.1 - Configuración optimizada para eliminar desplomes
Implementa mejoras específicas detectadas en el diagnóstico P22
"""

from typing import List, Dict, Any, Optional
import re
import numpy as np
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document

class EnhancedRAGEngine:
    """
    Enhanced RAG Engine con configuración optimizada y detección de fallos
    """

    def __init__(self, vector_store_path: str, use_hybrid: bool = True):
        print("🚀 Inicializando Enhanced RAG Engine v2.1...")

        # Embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Cargar vector store
        self.vector_store = Chroma(
            persist_directory=vector_store_path,
            embedding_function=self.embeddings,
            collection_name="langchain"
        )

        # Parámetros optimizados basados en diagnóstico P22
        self.params = {
            'top_k': 15,  # Aumentado para evitar desplomes como P22
            'similarity_threshold': 0.25,  # Más permisivo
            'semantic_weight': 0.7,  # Más peso a semantic para conceptos abstractos
            'keyword_weight': 0.3   # Menos peso a keyword matching
        }

        # Query expansion para términos específicos DNI
        self.domain_expansions = {
            'resis': ['resis', 'acollida', 'residencia', 'voluntariado'],
            'desayunos': ['desayuno', 'desayunos', 'comida', 'repartir', 'solidario'],
            'coles': ['colegio', 'colegios', 'refuerzo', 'escolar', 'ayuda'],
            'actividades': ['actividad', 'actividades', 'qué hacer', 'qué se hace'],
            'voluntariado': ['voluntario', 'voluntarios', 'voluntariado', 'participar']
        }

        # Configurar hybrid retrieval
        self.use_hybrid = use_hybrid
        if use_hybrid:
            self._setup_hybrid_retrieval()

        print(f"✅ Enhanced RAG Engine configurado:")
        print(f"   - Top K: {self.params['top_k']}")
        print(f"   - Similarity Threshold: {self.params['similarity_threshold']}")
        print(f"   - Semantic/Keyword Weights: {self.params['semantic_weight']}/{self.params['keyword_weight']}")

    def _setup_hybrid_retrieval(self):
        """Configura hybrid retrieval con parámetros optimizados"""
        # Obtener todos los documentos
        all_data = self.vector_store.get()
        documents = [
            Document(page_content=content, metadata=metadata)
            for content, metadata in zip(all_data['documents'], all_data['metadatas'])
        ]

        # Crear BM25 retriever
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = int(self.params['top_k'])

        # Chroma retriever
        self.chroma_retriever = self.vector_store.as_retriever(
            search_kwargs={'k': int(self.params['top_k'])}
        )

        # Ensemble retriever con pesos optimizados
        self.hybrid_retriever = EnsembleRetriever(
            retrievers=[self.chroma_retriever, self.bm25_retriever],
            weights=[self.params['semantic_weight'], self.params['keyword_weight']]
        )

    def expand_query(self, query: str) -> str:
        """
        Expande la query con términos específicos del dominio DNI
        """
        expanded_terms = []

        # Identificar términos clave y añadir expansiones
        for term, expansions in self.domain_expansions.items():
            if term in query.lower():
                expanded_terms.extend(expansions)

        # Construir query expandida
        if expanded_terms:
            expanded_query = f"{query} {' '.join(set(expanded_terms))}"
            return expanded_query

        return query

    def retrieve_with_fallback(self, query: str, max_attempts: int = 3) -> List[Dict[str, Any]]:
        """
        Recupera documentos con múltiples estrategias de fallback
        """
        original_query = query
        attempts = 0

        while attempts < max_attempts:
            attempts += 1

            try:
                if attempts == 1:
                    # Estrategia 1: Query expandida
                    expanded_query = self.expand_query(original_query)
                    results = self._retrieve_single(expanded_query)
                    print(f"🔍 Intento {attempts}: Query expandida '{expanded_query[:50]}...'")

                elif attempts == 2:
                    # Estrategia 2: Keywords específicas
                    keyword_query = self._extract_keywords(original_query)
                    results = self._retrieve_single(keyword_query)
                    print(f"🔍 Intento {attempts}: Keywords '{keyword_query}'")

                else:
                    # Estrategia 3: Query original
                    results = self._retrieve_single(original_query)
                    print(f"🔍 Intento {attempts}: Query original")

                # Verificar si los resultados son relevantes
                if self._validate_results(results, original_query):
                    print(f"✅ Recuperación exitosa en intento {attempts}")
                    return results

            except Exception as e:
                print(f"⚠️ Error en intento {attempts}: {e}")
                continue

        print(f"❌ Todos los intentos fallaron para query: '{original_query}'")
        return []

    def _retrieve_single(self, query: str) -> List[Dict[str, Any]]:
        """Realiza una única recuperación"""
        if self.use_hybrid:
            docs = self.hybrid_retriever.invoke(query)
        else:
            k = int(self.params['top_k'])
            docs = self.vector_store.similarity_search(query, k=k)

        top_k = int(self.params['top_k'])
        results = []
        for i, doc in enumerate(docs[:top_k]):
            results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': 1.0 - (i * 0.1),  # Score decreciente simple
                'rank': i + 1
            })

        return results

    def _extract_keywords(self, query: str) -> str:
        """Extrae keywords clave de la query"""
        # Eliminar stop words y quedarnos con términos importantes
        stop_words = ['qué', 'cómo', 'dónde', 'cuándo', 'cuánto', 'para', 'por', 'con', 'sin', 'sobre', 'del', 'de', 'la', 'el', 'los', 'las', 'en', 'un', 'una', 'unos', 'unas', 'es', 'son', 'se', 'me']

        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return ' '.join(keywords)

    def _validate_results(self, results: List[Dict[str, Any]], original_query: str) -> bool:
        """
        Valida si los resultados son relevantes para la query original
        """
        if not results:
            return False

        # Verificar si hay suficientes resultados
        if len(results) < 3:
            print(f"⚠️ Solo {len(results)} resultados recuperados")
            return False

        # Verificar si los resultados contienen términos relevantes
        query_terms = set(self._extract_keywords(original_query).split())
        relevant_results = 0

        for result in results[:5]:  # Top 5
            content_lower = result['content'].lower()
            if any(term in content_lower for term in query_terms):
                relevant_results += 1

        # Si al menos 2 de los top 5 son relevantes, considerar éxito
        is_valid = relevant_results >= 2
        if not is_valid:
            print(f"⚠️ Solo {relevant_results}/5 resultados relevantes")

        return is_valid

    def get_confidence_score(self, results: List[Dict[str, Any]], query: str) -> float:
        """
        Calcula un score de confianza para los resultados de retrieval
        """
        if not results:
            return 0.0

        # Factores de confianza
        factors = {
            'num_results': min(len(results) / 10, 1.0),  # Preferir más resultados
            'avg_score': np.mean([r['score'] for r in results[:5]]),  # Score promedio
            'content_relevance': self._calculate_content_relevance(results, query)
        }

        # Ponderación de factores
        confidence = (
            factors['num_results'] * 0.2 +
            factors['avg_score'] * 0.3 +
            factors['content_relevance'] * 0.5
        )

        return confidence

    def _calculate_content_relevance(self, results: List[Dict[str, Any]], query: str) -> float:
        """Calcula relevancia del contenido respecto a la query"""
        query_terms = set(self._extract_keywords(query).split())
        if not query_terms:
            return 0.5  # Default para queries sin términos claros

        relevance_scores = []
        for result in results[:5]:
            content_lower = result['content'].lower()
            matches = sum(1 for term in query_terms if term in content_lower)
            relevance = matches / len(query_terms)
            relevance_scores.append(relevance)

        return np.mean(relevance_scores)

    def update_params(self, new_params: Dict[str, Any]):
        """Actualiza parámetros del sistema"""
        old_params = self.params.copy()
        self.params.update(new_params)

        # Actualizar retrievers si es necesario
        if self.use_hybrid:
            if 'top_k' in new_params:
                k_value = int(new_params['top_k'])
                self.bm25_retriever.k = k_value
                self.chroma_retriever.search_kwargs['k'] = k_value

            if 'semantic_weight' in new_params or 'keyword_weight' in new_params:
                self.hybrid_retriever = EnsembleRetriever(
                    retrievers=[self.chroma_retriever, self.bm25_retriever],
                    weights=[self.params['semantic_weight'], self.params['keyword_weight']]
                )

        print(f"🔧 Parámetros actualizados: {old_params} → {self.params}")

    def get_diagnostics(self) -> Dict[str, Any]:
        """Retorna información de diagnóstico del motor RAG"""
        return {
            'engine_type': 'Enhanced RAG Engine v2.1',
            'config': self.params,
            'hybrid_retrieval': self.use_hybrid,
            'domain_expansions': list(self.domain_expansions.keys()),
            'vector_store_docs': len(self.vector_store.get()['documents']),
            'supported_strategies': ['expanded_query', 'keyword_extraction', 'original_query']
        }