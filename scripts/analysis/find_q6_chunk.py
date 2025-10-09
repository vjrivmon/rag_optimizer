#!/usr/bin/env python3
"""
Buscar específicamente el chunk de Q6 en el vector store v2
"""

import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

print("=" * 80)
print("BÚSQUEDA DEL CHUNK Q6 EN VECTOR STORE v2")
print("=" * 80)

# Conectar a ChromaDB
client = chromadb.PersistentClient(path="data/vectorstore/chroma_db")
collection = client.get_collection(name="rag_collection_fixed_v2")

# Obtener todos los documentos
all_data = collection.get()

print(f"\nTotal de chunks en la colección: {len(all_data['documents'])}")

# Buscar el chunk específico de Q6
q6_chunks = []
for i, (doc, metadata) in enumerate(zip(all_data['documents'], all_data['metadatas'])):
    # Buscar variaciones de la pregunta
    if any(phrase in doc.lower() for phrase in [
        "cómo me apunto",
        "como me apunto",
        "miércoles se publica",
        "formulario para inscrib"
    ]):
        q6_chunks.append({
            'id': all_data['ids'][i],
            'doc': doc,
            'metadata': metadata
        })

print(f"\n✅ Encontrados {len(q6_chunks)} chunks relacionados con Q6:")
print("=" * 80)

for i, chunk in enumerate(q6_chunks):
    print(f"\n{i+1}. ID: {chunk['id']}")
    print(f"   Metadata: {chunk['metadata']}")
    print(f"   Contenido: {chunk['doc'][:200]}...")

if q6_chunks:
    print("\n🔍 ANÁLISIS DEL PROBLEMA:")
    print("=" * 80)

    # Configurar embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Calcular similaridad con la pregunta
    question = "¿Cómo me apunto a desayunos solidarios?"
    query_embedding = embeddings.embed_query(question)

    print(f"\nPregunta de test: {question}")

    for chunk in q6_chunks:
        # Recuperar embedding del chunk
        chunk_result = collection.get(ids=[chunk['id']], include=['embeddings'])
        if chunk_result['embeddings'] and len(chunk_result['embeddings']) > 0:
            chunk_embedding = chunk_result['embeddings'][0]

            # Calcular similaridad coseno
            from numpy import dot
            from numpy.linalg import norm
            similarity = dot(query_embedding, chunk_embedding)/(norm(query_embedding)*norm(chunk_embedding))

            print(f"\n   Chunk: {chunk['doc'][:80]}...")
            print(f"   Similaridad con pregunta: {similarity:.3f}")

            # Buscar posición en ranking
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=20
            )

            position = None
            for j, doc in enumerate(results['documents'][0]):
                if chunk['doc'] in doc or doc in chunk['doc']:
                    position = j + 1
                    break

            if position:
                print(f"   📍 Posición en ranking: #{position}")
                if position > 10:
                    print(f"   ⚠️ PROBLEMA: Está en posición {position}, fuera del TOP 10")
            else:
                print(f"   ❌ NO APARECE en TOP 20!")

print("\n" + "=" * 80)
print("💡 DIAGNÓSTICO:")
if q6_chunks:
    print("   - El chunk SÍ existe en el vector store")
    print("   - Pero tiene baja similaridad con la pregunta")
    print("   - Posible solución: Ajustar el chunk o usar reranking")
else:
    print("   ❌ El chunk NO existe en el vector store")
    print("   - Necesita reconstruir el vector store")