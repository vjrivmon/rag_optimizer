#!/usr/bin/env python3
"""
Test simple para verificar que Q6 ahora se recupera correctamente
"""

import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

print("=" * 80)
print("TEST Q6 - VERIFICACIÓN RÁPIDA")
print("=" * 80)

# Configurar embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Conectar a ChromaDB
client = chromadb.PersistentClient(path="data/vectorstore/chroma_db")

# Usar la colección v2
collection = client.get_collection(name="rag_collection_fixed_v2")

# Pregunta Q6
question = "¿Cómo me apunto a desayunos solidarios?"
print(f"\n📝 Pregunta: {question}")

# Generar embedding
query_embedding = embeddings.embed_query(question)

# Buscar top 5
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)

print("\n🔍 TOP 5 CHUNKS RECUPERADOS:")
print("=" * 80)

q6_found = False
for i, (doc, score, metadata) in enumerate(zip(
    results['documents'][0],
    results['distances'][0],
    results['metadatas'][0]
)):
    print(f"\n{i+1}. Score: {1-score:.3f}")
    print(f"   Metadata: {metadata}")
    print(f"   Contenido: {doc[:150].replace(chr(10), ' ')}...")

    # Verificar si es el chunk correcto
    if "miércoles" in doc.lower() and "formulario" in doc.lower():
        print(f"   ✅ CHUNK CORRECTO ENCONTRADO EN POSICIÓN {i+1}!")
        q6_found = True

print("\n" + "=" * 80)
if q6_found:
    print("✅ ÉXITO: El chunk de Q6 ahora se recupera correctamente en el TOP 5")
    print("🎉 El vector store v2 está funcionando correctamente")
else:
    print("❌ PROBLEMA: El chunk de Q6 todavía no se recupera en el TOP 5")
    print("   Necesita más ajustes...")

print("\n💡 Recomendación para benchmark.py:")
print("   - El vector store está actualizado con la colección 'rag_collection_fixed_v2'")
print("   - rag_engine.py ya apunta a la nueva colección")
print("   - Q6 debería mejorar significativamente en el benchmark completo")