from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

class ConfigurableRAGEngine:
    """Motor RAG con parámetros ajustables dinámicamente"""

    def __init__(self, vector_store_path: str):
        # Embeddings - modelo corregido
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Cargar vector store desde ChromaDB
        self.vector_store = Chroma(
            persist_directory=vector_store_path,
            embedding_function=self.embeddings
        )

        # Parámetros por defecto
        self.params = {
            'top_k': 8,
            'similarity_threshold': 0.4
        }

    def update_params(self, new_params: Dict[str, Any]):
        """Actualiza parámetros"""
        self.params.update(new_params)
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """Recupera documentos relevantes usando ChromaDB"""

        # Búsqueda vectorial con ChromaDB
        # Asegurar que k es un int nativo de Python
        k = int(self.params['top_k'])

        # Usar similarity_search simple (sin scores de distancia L2)
        # ChromaDB devuelve distancias L2 negativas que no funcionan bien con threshold
        docs = self.vector_store.similarity_search(query, k=k)

        # Convertir a formato esperado (sin filtrado por threshold)
        # Los documentos ya vienen ordenados por similitud (más similar primero)
        results = []
        for i, doc in enumerate(docs):
            results.append({
                'content': doc.page_content,
                'score': 1.0 - (i * 0.1),  # Score decreciente: 1.0, 0.9, 0.8, etc.
                'source': doc.metadata.get('source', 'unknown')
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