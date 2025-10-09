#!/usr/bin/env python3
"""
Verificar en qué posición está el chunk de Q6
"""

import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

print("=" * 80)
print("VERIFICACIÓN POSICIÓN Q6")
print("=" * 80)

# Configurar embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Conectar a ChromaDB
client = chromadb.PersistentClient(path="data/vectorstore/chroma_db")
collection = client.get_collection(name="rag_collection_fixed_v2")

# Pregunta Q6
question = "¿Cómo me apunto a desayunos solidarios?"
print(f"\n📝 Pregunta: {question}")

# Buscar top 20
query_embedding = embeddings.embed_query(question)
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=20
)

print("\n🔍 BÚSQUEDA EN TOP 20:")
print("=" * 80)

q6_position = None
for i, (doc, score, metadata) in enumerate(zip(
    results['documents'][0],
    results['distances'][0],
    results['metadatas'][0]
), 1):
    # Mostrar solo los primeros 10 y el que coincida
    if i <= 10 or "cómo me apunto" in doc.lower():
        print(f"\n{i}. Score: {1-score:.3f}")
        print(f"   Activity: {metadata.get('activity', '?')}, Type: {metadata.get('chunk_type', '?')}, Importance: {metadata.get('importance', '?')}")
        content_preview = doc[:100].replace('\n', ' ')
        print(f"   Contenido: {content_preview}...")

        # Verificar si es el chunk de Q6
        if "cómo me apunto" in doc.lower() and "miércoles" in doc.lower():
            print(f"   ✅ CHUNK Q6 ENCONTRADO!")
            q6_position = i

print("\n" + "=" * 80)
print("RESULTADO:")
print("=" * 80)

if q6_position:
    if q6_position <= 5:
        print(f"✅ ÉXITO: Chunk Q6 en posición #{q6_position} (TOP 5)")
    elif q6_position <= 10:
        print(f"⚠️ ACEPTABLE: Chunk Q6 en posición #{q6_position} (TOP 10)")
    else:
        print(f"❌ PROBLEMA: Chunk Q6 en posición #{q6_position} (fuera de TOP 10)")
else:
    print("❌ ERROR: Chunk Q6 NO encontrado en TOP 20")

print("\n💡 Estado actual:")
print("   - Vector store: rag_collection_fixed_v2")
print("   - Total chunks: 79")
print("   - FAQ chunks con metadata optimizada")
print("   - rag_engine.py configurado para usar v2")

if q6_position and q6_position > 10:
    print("\n⚠️ NOTA: Aunque Q6 está fuera del TOP 10,")
    print("   el sistema híbrido (BM25 + semantic) debería capturarlo")
    print("   por las palabras clave 'apunto' y 'formulario'")