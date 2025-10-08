import sys
import os
# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.rag_engine import ConfigurableRAGEngine
import json

def test_rag():
    print("🧪 Probando RAG Engine...")
    
    # Cargar RAG
    rag = ConfigurableRAGEngine("data/vectorstore/faiss_index")
    
    # Cargar preguntas de prueba
    with open("data/evaluation_dataset.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    # Probar primera pregunta
    q = questions[0]
    print(f"\n📝 Pregunta: {q['question']}")
    print(f"   Categoría: {q['category']}")
    
    # Recuperar documentos
    docs = rag.retrieve(q['question'])
    print(f"\n✅ Recuperados {len(docs)} documentos:")
    
    for i, doc in enumerate(docs, 1):
        print(f"\n   [{i}] Score: {doc['score']:.3f}")
        print(f"       {doc['content'][:200]}...")
    
    # Construir contexto
    context = rag.build_context(docs)
    print(f"\n📄 Contexto generado ({len(context)} caracteres)")

if __name__ == "__main__":
    test_rag()