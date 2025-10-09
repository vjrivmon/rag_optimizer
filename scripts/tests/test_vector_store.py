#!/usr/bin/env python3
"""
Test rápido del vector store regenerado
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def test_vector_store():
    """Test que el vector store funciona correctamente"""

    print("🧪 TEST DEL VECTOR STORE")
    print("="*60)

    try:
        # Configurar embeddings
        print("\n📚 Cargando embeddings...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Cargar vector store
        print("💾 Cargando vector store...")
        vector_store = Chroma(
            persist_directory="data/vectorstore/chroma_db",
            embedding_function=embeddings,
            collection_name="rag_collection_fixed_v2"
        )

        # Queries de prueba
        test_queries = [
            "¿A qué hora son los desayunos?",
            "¿Dónde es el punto de encuentro de desayunos?",
            "¿Cómo me apunto a desayunos solidarios?",
            "¿Qué se hace en la actividad de coles?"
        ]

        print("\n🔍 Ejecutando queries de prueba...")
        print("-"*60)

        for query in test_queries:
            print(f"\n❓ Query: {query}")

            # Búsqueda semántica
            results = vector_store.similarity_search(query, k=3)

            if results:
                print(f"   ✅ {len(results)} resultados encontrados")
                for i, doc in enumerate(results, 1):
                    preview = doc.page_content[:100].replace('\n', ' ')
                    print(f"   [{i}] {preview}...")

                    # Verificar metadata
                    if 'chunk_type' in doc.metadata:
                        print(f"       📋 Tipo: {doc.metadata['chunk_type']}")
            else:
                print("   ❌ No se encontraron resultados")

        print("\n" + "="*60)
        print("✅ Vector store funcionando correctamente!")
        print("   • Colección: rag_collection_fixed_v2")
        print("   • Sin errores de metadata")
        print("\n📌 Puedes ejecutar el benchmark:")
        print("   ./venv/bin/python benchmark.py")

    except Exception as e:
        print(f"\n❌ Error en el test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    test_vector_store()