#!/usr/bin/env python3
"""
Análisis detallado de las preguntas con retrieval parcial
"""

import json
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

# Preguntas identificadas como PARTIAL
partial_questions = {
    1: "¿Qué se hace en la actividad de desayunos?",
    2: "¿Dónde es el punto de encuentro de desayunos?",
    4: "¿Cada cuánto se hace la actividad de desayunos?",
    6: "¿Cómo me apunto a desayunos solidarios?",
    7: "¿Si me apunto un día tengo que ir al resto de desayunos?",
    11: "¿Dónde es la actividad de coles?",
    20: "¿Dónde es la actividad de resis?",
    22: "¿Qué se hace en la actividad de resis?",
    25: "¿Qué significa Para-Mira-Ayuda?"
}

print("=" * 80)
print("ANÁLISIS DETALLADO DE PREGUNTAS CON RETRIEVAL PARCIAL")
print("=" * 80)

# Cargar dataset para obtener respuestas esperadas
with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Configurar embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Conectar a ChromaDB
client = chromadb.PersistentClient(path="data/vectorstore/chroma_db")
collection = client.get_collection(name="rag_collection_fixed_v2")

print(f"\n📝 Analizando {len(partial_questions)} preguntas con retrieval parcial...")
print("-" * 80)

critical_questions = []
moderate_questions = []
minor_questions = []

for q_num, question in partial_questions.items():
    print(f"\nQ{q_num}: {question}")

    # Obtener respuesta esperada del dataset
    expected = dataset[q_num-1]['expected_answer']
    keywords = dataset[q_num-1]['keywords']

    # Buscar chunks
    query_embedding = embeddings.embed_query(question)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    # Analizar top 3 chunks
    print(f"   Respuesta esperada: {expected[:80]}...")
    print(f"   Keywords esperados: {keywords}")
    print(f"\n   Top 3 chunks recuperados:")

    answer_fragments_found = False
    keywords_found = set()

    for i, (doc, score) in enumerate(zip(results['documents'][0][:3], results['distances'][0][:3]), 1):
        doc_lower = doc.lower()
        score_val = 1 - score

        # Buscar keywords
        for kw in keywords:
            if kw.lower() in doc_lower:
                keywords_found.add(kw)

        # Buscar fragmentos de la respuesta
        answer_words = expected.lower().split()[:10]  # Primeras 10 palabras
        matching_words = sum(1 for word in answer_words if word in doc_lower)

        print(f"      {i}. Score: {score_val:.2f} - {doc[:60]}...")

        if matching_words >= 3:
            answer_fragments_found = True
            print(f"         ✓ Contiene fragmentos de la respuesta")

    # Clasificar el problema
    coverage = len(keywords_found) / len(keywords) if keywords else 0
    print(f"\n   📊 Coverage: {coverage:.0%} ({len(keywords_found)}/{len(keywords)} keywords)")

    if not answer_fragments_found and coverage < 0.3:
        print(f"   ❌ CRÍTICO: Respuesta no encontrada y baja cobertura de keywords")
        critical_questions.append(q_num)
    elif coverage < 0.5:
        print(f"   ⚠️ MODERADO: Cobertura parcial de keywords")
        moderate_questions.append(q_num)
    else:
        print(f"   ✓ MENOR: Retrieval aceptable pero mejorable")
        minor_questions.append(q_num)

print("\n" + "=" * 80)
print("RESUMEN Y RECOMENDACIONES")
print("=" * 80)

print(f"\n📊 Clasificación de problemas:")
print(f"   🔴 CRÍTICOS: {len(critical_questions)} preguntas - {critical_questions}")
print(f"   🟡 MODERADOS: {len(moderate_questions)} preguntas - {moderate_questions}")
print(f"   🟢 MENORES: {len(minor_questions)} preguntas - {minor_questions}")

# Análisis específico de preguntas críticas
if critical_questions:
    print(f"\n🚨 PREGUNTAS CRÍTICAS QUE NECESITAN ATENCIÓN:")
    for q_num in critical_questions:
        print(f"\n   Q{q_num}: {partial_questions[q_num]}")
        expected = dataset[q_num-1]['expected_answer']
        print(f"   Respuesta esperada: {expected[:100]}...")

        # Verificar si la información existe en algún chunk
        all_data = collection.get()
        found_in_store = False
        for doc in all_data['documents']:
            if any(word in doc.lower() for word in expected.lower().split()[:5]):
                found_in_store = True
                break

        if found_in_store:
            print(f"   ✓ La información SÍ existe en el vector store")
            print(f"   → Solución: El sistema híbrido BM25 debería capturarlo")
        else:
            print(f"   ❌ La información NO está en el vector store")
            print(f"   → Solución: Necesita reconstruir el vector store")

print("\n" + "=" * 80)
print("IMPACTO ESPERADO EN EL BENCHMARK")
print("=" * 80)

print(f"\n📈 Predicción de rendimiento:")
print(f"   - 17/26 (65%) preguntas con BUEN retrieval → Score alto esperado")
print(f"   - 9/26 (35%) preguntas con retrieval PARCIAL:")

if len(critical_questions) <= 2:
    print(f"     • Solo {len(critical_questions)} críticas → Impacto mínimo")
    print(f"     • Sistema híbrido BM25 compensará la mayoría")
    print(f"\n   ✅ PREDICCIÓN: Benchmark debería dar buenos resultados (>0.75 avg)")
else:
    print(f"     • {len(critical_questions)} críticas → Impacto moderado")
    print(f"     • Sistema híbrido BM25 ayudará pero no resolverá todo")
    print(f"\n   ⚠️ PREDICCIÓN: Benchmark con resultados moderados (0.65-0.75 avg)")

print("\n💡 NOTA IMPORTANTE:")
print("   Las preguntas 11, 20 ya fueron probadas y FUNCIONAN correctamente")
print("   con el vector store v2, así que el impacto real será menor.")