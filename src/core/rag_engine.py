from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document

class ConfigurableRAGEngine:
    """Motor RAG con parámetros ajustables dinámicamente y hybrid retrieval (semantic + BM25)"""

    def __init__(self, vector_store_path: str, use_hybrid: bool = True):
        # Embeddings - modelo corregido
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Cargar vector store desde ChromaDB
        self.vector_store = Chroma(
            persist_directory=vector_store_path,
            embedding_function=self.embeddings,
            collection_name="langchain"  # Usar colección actual con 106 documentos
        )

        # Parámetros por defecto (optimizados basados en benchmark #3)
        self.params = {
            'top_k': 10,  # Aumentado de 8 a 10 para más candidatos
            'similarity_threshold': 0.35,  # Más permisivo para capturar más contexto
            'semantic_weight': 0.6,  # Dar más peso a semantic para conceptos abstractos
            'keyword_weight': 0.4   # Peso menor a BM25 keyword matching
        }

        # Configurar hybrid retrieval
        self.use_hybrid = use_hybrid
        if use_hybrid:
            self._setup_hybrid_retrieval()

    def _setup_hybrid_retrieval(self):
        """Configura hybrid retrieval combinando ChromaDB (semantic) + BM25 (keyword)"""
        # Obtener todos los documentos del vector store para BM25
        all_data = self.vector_store.get()
        documents = [
            Document(page_content=content, metadata=metadata)
            for content, metadata in zip(all_data['documents'], all_data['metadatas'])
        ]

        # Crear retriever BM25
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = int(self.params['top_k'])  # Asegurar int nativo

        # Crear retriever de ChromaDB - IMPORTANTE: k debe ser int nativo de Python
        self.chroma_retriever = self.vector_store.as_retriever(
            search_kwargs={'k': int(self.params['top_k'])}
        )

        # Ensemble retriever: combina ambos con pesos configurables
        # Semantic weight mayor (0.6) para preguntas conceptuales como "¿Qué significa...?"
        # Keyword weight menor (0.4) para búsquedas literales
        self.hybrid_retriever = EnsembleRetriever(
            retrievers=[self.chroma_retriever, self.bm25_retriever],
            weights=[self.params['semantic_weight'], self.params['keyword_weight']]
        )

    def update_params(self, new_params: Dict[str, Any]):
        """Actualiza parámetros"""
        self.params.update(new_params)

        # Si cambia top_k, actualizar retrievers - SIEMPRE convertir a int nativo
        if 'top_k' in new_params and self.use_hybrid:
            k_value = int(new_params['top_k'])  # Convertir numpy.int64 a int
            self.bm25_retriever.k = k_value
            self.chroma_retriever.search_kwargs['k'] = k_value

        # Si cambian los pesos, recrear el hybrid retriever
        if ('semantic_weight' in new_params or 'keyword_weight' in new_params) and self.use_hybrid:
            self.hybrid_retriever = EnsembleRetriever(
                retrievers=[self.chroma_retriever, self.bm25_retriever],
                weights=[self.params['semantic_weight'], self.params['keyword_weight']]
            )
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Recupera documentos relevantes usando hybrid retrieval (semantic + BM25)"""

        if self.use_hybrid:
            # Usar hybrid retrieval
            docs = self.hybrid_retriever.invoke(query)
        else:
            # Fallback a búsqueda vectorial pura
            k = int(self.params['top_k'])
            docs = self.vector_store.similarity_search(query, k=k)

        # Convertir a formato esperado
        # Los documentos ya vienen ordenados por score combinado
        # IMPORTANTE: Convertir top_k a int nativo para evitar errores con numpy types
        top_k = int(self.params['top_k'])
        results = []
        for i, doc in enumerate(docs[:top_k]):
            results.append({
                'content': doc.page_content,
                'score': 1.0 - (i * 0.1),  # Score decreciente: 1.0, 0.9, 0.8, etc.
                'source': doc.metadata.get('source', 'unknown'),
                'metadata': doc.metadata
            })

        return results
    
    def build_context(self, docs: List[Dict]) -> str:
        """Construye contexto para el prompt"""
        if not docs:
            return "No se encontró información relevante."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(
                f"[Documento {i}]\n{doc['content']}\n"
            )
        
        return "\n".join(context_parts)