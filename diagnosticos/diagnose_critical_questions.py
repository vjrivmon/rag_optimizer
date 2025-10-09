#!/usr/bin/env python3
"""
Diagnóstico urgente de Q2, Q4 y Q6 que están fallando en el benchmark
"""

import json
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

print("=" * 80)
print("🚨 DIAGNÓSTICO URGENTE: Q2, Q4, Q6")
print("=" * 80)

# Cargar dataset
with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Preguntas problemáticas
problematic = {
    2: {  # Q2 - Score: 0.100
        'question': dataset[1]['question'],
        'expected': dataset[1]['expected_answer'],
        'keywords': dataset[1]['keywords']
    },
    4: {  # Q4 - Score: 0.087-0.450
        'question': dataset[3]['question'],
        'expected': dataset[3]['expected_answer'],
        'keywords': dataset[3]['keywords']
    },
    6: {  # Q6 - Score: 0.264-0.591
        'question': dataset[5]['question'],
        'expected': dataset[5]['expected_answer'],
        'keywords': dataset[5]['keywords']
    }
}

# Configurar embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Conectar a vector store (simulando lo que hace el benchmark)
vector_store = Chroma(
    persist_directory="data/vectorstore/chroma_db",
    embedding_function=embeddings,
    collection_name="rag_collection_fixed_v2"
)

print("\n📋 Verificando configuración del vector store...")

# Obtener información del vector store
client = chromadb.PersistentClient(path="data/vectorstore/chroma_db")
collection = client.get_collection(name="rag_collection_fixed_v2")
all_data = collection.get()
print(f"   • Total chunks: {len(all_data['documents'])}")
print(f"   • Collection: rag_collection_fixed_v2")

critical_info = {
    "Porta de la Mar": False,
    "una vez a la semana": False,
    "sábados": False,
    "miércoles": False,
    "formulario": False
}

# Verificar si la información crítica existe
for doc in all_data['documents']:
    doc_lower = doc.lower()
    for key in critical_info.keys():
        if key.lower() in doc_lower:
            critical_info[key] = True

print("\n📊 Información crítica en el vector store:")
for info, exists in critical_info.items():
    print(f"   • '{info}': {'✅ Existe' if exists else '❌ NO EXISTE'}")

print("\n" + "=" * 80)
print("ANÁLISIS POR PREGUNTA")
print("=" * 80)

for q_num, data in problematic.items():
    print(f"\n{'='*60}")
    print(f"Q{q_num}: {data['question']}")
    print(f"{'='*60}")
    print(f"Respuesta esperada: {data['expected'][:100]}...")
    print(f"Keywords esperados: {data['keywords']}")

    # Usar el retriever del vector store (como hace benchmark.py)
    retriever = vector_store.as_retriever(search_kwargs={'k': 10})
    docs = retriever.get_relevant_documents(data['question'])

    print(f"\n📚 Top 5 chunks recuperados:")
    keywords_found = set()
    answer_found = False

    for i, doc in enumerate(docs[:5], 1):
        content = doc.page_content[:80].replace('\n', ' ')
        print(f"\n   {i}. {content}...")

        # Buscar keywords
        doc_lower = doc.page_content.lower()
        for kw in data['keywords']:
            if kw.lower() in doc_lower:
                keywords_found.add(kw)

        # Verificar si contiene la respuesta
        answer_words = data['expected'].lower().split()[:5]
        if sum(1 for w in answer_words if w in doc_lower) >= 3:
            answer_found = True
            print(f"      ✅ Contiene fragmentos de la respuesta")

    coverage = len(keywords_found) / len(data['keywords']) if data['keywords'] else 0
    print(f"\n📈 Análisis:")
    print(f"   • Keywords coverage: {coverage:.0%} ({len(keywords_found)}/{len(data['keywords'])})")
    print(f"   • Keywords encontrados: {keywords_found if keywords_found else 'NINGUNO'}")
    print(f"   • Respuesta en chunks: {'SÍ' if answer_found else 'NO'}")

    if not answer_found or coverage < 0.3:
        print(f"\n❌ PROBLEMA CRÍTICO:")
        if q_num == 2:
            print("   La información 'Porta de la Mar' NO se está recuperando")
            print("   Aunque existe en el corpus, no está en los chunks devueltos")
        elif q_num == 4:
            print("   La información 'una vez a la semana' NO se está recuperando")
            print("   Los chunks recuperados no contienen la frecuencia")
        elif q_num == 6:
            print("   El chunk con 'miércoles' y 'formulario' NO se recupera")
            print("   Está en posición > 10 en el ranking")

print("\n" + "=" * 80)
print("🔍 CAUSA RAÍZ DEL PROBLEMA")
print("=" * 80)

print("""
El problema es que el benchmark.py está usando un número VARIABLE de chunks
basado en el número de documentos recuperados:

- Q2: "7 documentos recuperados, usando top 7 truncados"
- Q4: "8 documentos recuperados, usando top 7 truncados"
- Q6: "3 documentos recuperados, usando top 7 truncados" ⚠️

Para Q6 solo usa 3 chunks cuando el chunk correcto está en posición > 10!

SOLUCIÓN URGENTE:
1. Forzar un mínimo de 7-10 chunks siempre
2. No truncar basado en documentos recuperados
3. Usar el top_k configurado (10) consistentemente
""")

print("\n💡 HOTFIX RECOMENDADO:")
print("-" * 60)
print("""
En benchmark.py, cambiar la línea que dice:
   contexts = [doc['content'][:400] for doc in docs[:min(len(docs), 7)]]

Por:
   contexts = [doc['content'][:400] for doc in docs[:10]]  # Usar siempre top 10

Esto asegurará que siempre se usen los 10 mejores chunks,
no solo los primeros N documentos recuperados.
""")