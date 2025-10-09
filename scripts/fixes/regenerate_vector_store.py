#!/usr/bin/env python3
"""
Regenerar el vector store para solucionar el error "Missing metadata segment"
"""

import os
import shutil
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import warnings

# Suprimir warnings
warnings.filterwarnings('ignore')

def regenerate_vector_store():
    """Regenera el vector store completamente"""

    print("🔧 REGENERANDO VECTOR STORE")
    print("="*80)

    # Limpiar directorio existente
    db_path = "data/vectorstore/chroma_db"
    if os.path.exists(db_path):
        print(f"   ⚠️  Eliminando vector store corrupto en {db_path}")
        shutil.rmtree(db_path)

    # Crear directorio
    os.makedirs(db_path, exist_ok=True)

    # Cargar documentos
    print("\n📚 Cargando documentos...")
    loader = DirectoryLoader(
        'data/documents',
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    documents = loader.load()

    print(f"   ✓ Total documentos cargados: {len(documents)}")

    # Configurar text splitter optimizado
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,      # Chunks más pequeños para mejor precisión
        chunk_overlap=100,   # Mayor overlap para no perder contexto
        separators=["\n\n¿", "\n¿", "\n\n", "\n", ". ", ", ", " "],
        keep_separator=True,
        length_function=len
    )

    # Dividir documentos
    print("\n✂️  Dividiendo documentos en chunks...")
    chunks = text_splitter.split_documents(documents)

    # Procesar chunks para FAQ
    print("\n🔍 Detectando y preservando FAQs...")
    processed_chunks = []

    for i, chunk in enumerate(chunks):
        content = chunk.page_content

        # Detectar si es una pregunta-respuesta
        if content.strip().startswith("¿") and "?" in content:
            # Es una FAQ, intentar preservar Q&A juntos
            lines = content.split('\n')
            question_line = lines[0] if lines else ""

            # Buscar la respuesta completa
            if i + 1 < len(chunks) and not chunks[i + 1].page_content.strip().startswith("¿"):
                # El siguiente chunk es probablemente la respuesta
                answer = chunks[i + 1].page_content
                combined = f"{question_line}\n{answer}"

                # Actualizar metadata
                chunk.page_content = combined
                chunk.metadata['chunk_type'] = 'faq'
                chunk.metadata['question'] = question_line

                # Clasificar por categoría
                if any(word in question_line.lower() for word in ['desayuno', 'cena']):
                    chunk.metadata['category'] = 'desayunos'
                elif any(word in question_line.lower() for word in ['cole', 'escuela']):
                    chunk.metadata['category'] = 'coles'
                elif any(word in question_line.lower() for word in ['residencia', 'mayor']):
                    chunk.metadata['category'] = 'residencias'
                else:
                    chunk.metadata['category'] = 'general'

                chunk.metadata['importance'] = 'high'
        else:
            chunk.metadata['chunk_type'] = 'regular'
            chunk.metadata['importance'] = 'normal'

        # Añadir metadata adicional
        chunk.metadata['chunk_index'] = i
        chunk.metadata['content_length'] = len(chunk.page_content)

        processed_chunks.append(chunk)

    # Eliminar duplicados manteniendo FAQs
    unique_chunks = []
    seen_content = set()

    for chunk in processed_chunks:
        content_key = chunk.page_content[:100]  # Usar primeros 100 chars como clave
        if content_key not in seen_content or chunk.metadata.get('chunk_type') == 'faq':
            unique_chunks.append(chunk)
            seen_content.add(content_key)

    print(f"   ✓ Chunks procesados: {len(unique_chunks)}")
    print(f"   ✓ FAQs detectadas: {sum(1 for c in unique_chunks if c.metadata.get('chunk_type') == 'faq')}")

    # Configurar embeddings (IMPORTANTE: mismo modelo que en rag_engine.py)
    print("\n🤖 Configurando embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Crear vector store
    print("\n💾 Creando vector store...")
    vector_store = Chroma.from_documents(
        documents=unique_chunks,
        embedding=embeddings,
        collection_name="rag_collection_fixed_v2",  # Mantener el nombre de colección
        persist_directory=db_path,
        collection_metadata={"hnsw:space": "cosine"}
    )

    # Persistir
    vector_store.persist()

    # Verificar
    print("\n✅ Vector store regenerado exitosamente")
    print(f"   • Ubicación: {db_path}")
    print(f"   • Colección: rag_collection_fixed_v2")
    print(f"   • Total chunks: {len(unique_chunks)}")
    print(f"   • Modelo embeddings: paraphrase-multilingual-mpnet-base-v2 (768 dims)")

    # Test rápido
    print("\n🧪 Test rápido del vector store...")
    test_query = "¿A qué hora son los desayunos?"
    results = vector_store.similarity_search(test_query, k=3)

    if results:
        print(f"   ✓ Query test: '{test_query}'")
        print(f"   ✓ Resultados encontrados: {len(results)}")
        print(f"   ✓ Primer resultado: {results[0].page_content[:100]}...")
    else:
        print("   ⚠️  No se encontraron resultados en el test")

    return vector_store

if __name__ == "__main__":
    try:
        regenerate_vector_store()
        print("\n🎉 Vector store regenerado correctamente")
        print("   Ahora puedes ejecutar: python benchmark.py")
    except Exception as e:
        print(f"\n❌ Error regenerando vector store: {e}")
        import traceback
        traceback.print_exc()