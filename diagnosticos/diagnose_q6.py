#!/usr/bin/env python3
"""
Diagnóstico específico para Q6: ¿Cómo me apunto a desayunos solidarios?
"""

import sys
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

def diagnose_q6():
    print("=" * 80)
    print("DIAGNÓSTICO Q6: ¿Cómo me apunto a desayunos solidarios?")
    print("=" * 80)

    # Configurar embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Conectar a ChromaDB
    client = chromadb.PersistentClient(path="data/vectorstore/chroma_db")

    # Verificar colecciones disponibles
    collections = client.list_collections()
    print(f"\nColecciones disponibles: {[c.name for c in collections]}")

    # Usar la colección correcta
    collection_name = "rag_collection_fixed"
    if not any(c.name == collection_name for c in collections):
        print(f"ERROR: Colección '{collection_name}' no encontrada")
        return

    collection = client.get_collection(name=collection_name)

    # Pregunta Q6
    question = "¿Cómo me apunto a desayunos solidarios?"
    print(f"\nPregunta: {question}")

    # Generar embedding de la pregunta
    query_embedding = embeddings.embed_query(question)

    # Buscar chunks relevantes
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10
    )

    print("\n" + "=" * 80)
    print("TOP 10 CHUNKS RECUPERADOS:")
    print("=" * 80)

    for i, (doc, score, metadata) in enumerate(zip(
        results['documents'][0],
        results['distances'][0],
        results['metadatas'][0]
    )):
        print(f"\n📌 Chunk {i+1} (Score: {1-score:.3f}):")
        print(f"   Tipo: {metadata.get('chunk_type', 'unknown')}")
        print(f"   Importancia: {metadata.get('importance', 'unknown')}")
        print(f"   Contenido: {doc[:150]}...")

        # Verificar si contiene información relevante
        keywords = ["apunto", "inscrib", "miércoles", "sábado", "formulario", "whatsapp"]
        matches = [k for k in keywords if k.lower() in doc.lower()]
        if matches:
            print(f"   ✅ RELEVANTE: Contiene {matches}")
        else:
            print(f"   ❌ NO relevante para la pregunta")

    # Buscar específicamente el chunk correcto
    print("\n" + "=" * 80)
    print("BÚSQUEDA ESPECÍFICA DEL CHUNK CORRECTO:")
    print("=" * 80)

    # Buscar por contenido exacto
    all_data = collection.get()
    found_correct = False

    for i, doc in enumerate(all_data['documents']):
        if "¿Cómo me apunto?" in doc or "miércoles se publica" in doc:
            print(f"\n✅ CHUNK CORRECTO ENCONTRADO (ID: {all_data['ids'][i]}):")
            print(f"   Contenido: {doc}")
            print(f"   Metadata: {all_data['metadatas'][i]}")
            found_correct = True

            # Calcular similaridad con la pregunta
            doc_embedding = embeddings.embed_documents([doc])[0]
            from numpy import dot
            from numpy.linalg import norm
            similarity = dot(query_embedding, doc_embedding)/(norm(query_embedding)*norm(doc_embedding))
            print(f"   Similaridad con pregunta: {similarity:.3f}")

            # Verificar posición en el ranking
            print(f"\n   ⚠️ PROBLEMA: Este chunk debería estar en TOP 1-3 pero no aparece en TOP 10!")
            print(f"   La similaridad calculada es: {similarity:.3f}")
            print(f"   Pero el peor chunk del TOP 10 tiene score: {1-results['distances'][0][9]:.3f}")

    if not found_correct:
        print("\n❌ ERROR CRÍTICO: El chunk con la respuesta correcta NO está en el vector store!")

    # Análisis final
    print("\n" + "=" * 80)
    print("ANÁLISIS:")
    print("=" * 80)

    if found_correct and results['distances'][0][0] > 0.5:
        print("❌ Problema: El chunk correcto existe pero NO se está recuperando")
        print("   Posibles causas:")
        print("   1. Embedding de baja calidad para esta pregunta específica")
        print("   2. Chunk demasiado largo/corto que diluye la señal")
        print("   3. Threshold de similaridad muy alto")
    elif not found_correct:
        print("❌ Problema: El chunk con la respuesta NO está indexado")
        print("   Solución: Reconstruir vector store asegurando incluir FAQ completo")
    else:
        print("✅ El sistema debería funcionar correctamente")

if __name__ == "__main__":
    diagnose_q6()