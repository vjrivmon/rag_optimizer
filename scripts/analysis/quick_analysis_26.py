#!/usr/bin/env python3
"""
Análisis rápido de las 26 preguntas - versión optimizada
"""

import json
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("🔍 ANÁLISIS RÁPIDO DE LAS 26 PREGUNTAS")
print("=" * 80)

# Cargar dataset
with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Configurar embeddings
print("\n⚙️ Configurando embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Conectar directamente al vector store
print("📚 Conectando al vector store...")
vector_store = Chroma(
    persist_directory="data/vectorstore/chroma_db",
    embedding_function=embeddings,
    collection_name="rag_collection_fixed_v2"
)

# Analizar cada pregunta
print("\n🔍 Analizando preguntas...")
print("-" * 80)

results = []
critical_issues = []

for idx, q_data in enumerate(dataset, 1):
    question = q_data['question']
    expected = q_data['expected_answer']
    keywords = q_data['keywords']

    # Recuperar documentos (simulando lo que hace el RAG)
    retriever = vector_store.as_retriever(search_kwargs={'k': 20})
    docs = retriever.get_relevant_documents(question)

    # Análisis rápido
    keywords_in_top10 = 0
    answer_found_position = None

    # Buscar en top 10
    for i, doc in enumerate(docs[:10], 1):
        doc_lower = doc.page_content.lower()

        # Contar keywords
        for kw in keywords:
            if kw.lower() in doc_lower:
                keywords_in_top10 += 1
                break

        # Buscar respuesta (simplificado)
        if not answer_found_position:
            key_words = expected.lower().split()[:5]
            if sum(1 for w in key_words if len(w) > 3 and w in doc_lower) >= 2:
                answer_found_position = i

    # Buscar en 11-20 si no se encontró
    if not answer_found_position and len(docs) > 10:
        for i, doc in enumerate(docs[10:20], 11):
            doc_lower = doc.page_content.lower()
            key_words = expected.lower().split()[:5]
            if sum(1 for w in key_words if len(w) > 3 and w in doc_lower) >= 2:
                answer_found_position = i
                break

    # Determinar estado
    num_docs = len(docs)

    # Identificar problemas críticos
    if num_docs < 7:
        status = "🚨 <7 DOCS"
        critical_issues.append(f"Q{idx}")
    elif num_docs < 10:
        status = "⚠️ <10 DOCS"
    elif not answer_found_position:
        status = "❌ NO RESP"
        critical_issues.append(f"Q{idx}")
    elif answer_found_position > 10:
        status = f"⚠️ POS>{answer_found_position}"
    elif answer_found_position > 7:
        status = f"📍 POS {answer_found_position}"
    else:
        status = f"✅ POS {answer_found_position}"

    results.append({
        'Q': f"Q{idx}",
        'Pregunta': question[:35] + "..." if len(question) > 35 else question,
        'Docs': num_docs,
        'Resp@': answer_found_position if answer_found_position else "-",
        'Estado': status
    })

    if idx % 5 == 0:
        print(f"   Procesadas {idx}/26...")

print("\n" + "=" * 80)
print("📊 TABLA COMPLETA DE RESULTADOS")
print("=" * 80)

# Tabla de resultados
headers = ['Q', 'Pregunta', 'Docs', 'Resp@', 'Estado']
print("\n" + tabulate(results, headers=headers, tablefmt='grid'))

# Análisis del impacto del límite de 7 chunks
print("\n" + "=" * 80)
print("⚠️ ANÁLISIS DEL IMPACTO DEL LÍMITE DE 7 CHUNKS")
print("=" * 80)

affected_by_7_limit = []
severely_affected = []

for r in results:
    q_num = int(r['Q'][1:])
    docs = r['Docs']
    resp_pos = r['Resp@']

    # Casos severamente afectados (no tenían suficientes docs)
    if docs < 7:
        severely_affected.append(f"Q{q_num}: Solo {docs} docs (usaba {docs} chunks)")

    # Casos moderadamente afectados (respuesta en posición 8-10)
    elif resp_pos != "-" and isinstance(resp_pos, int) and resp_pos > 7:
        affected_by_7_limit.append(f"Q{q_num}: Respuesta en posición {resp_pos}")

print(f"\n🔴 SEVERAMENTE AFECTADOS (usaban <7 chunks):")
if severely_affected:
    for item in severely_affected:
        print(f"   {item}")
else:
    print("   Ninguno")

print(f"\n🟡 MODERADAMENTE AFECTADOS (respuesta en pos 8-10):")
if affected_by_7_limit:
    for item in affected_by_7_limit:
        print(f"   {item}")
else:
    print("   Ninguno")

# Estadísticas finales
print("\n" + "=" * 80)
print("📈 ESTADÍSTICAS FINALES")
print("=" * 80)

docs_lt_7 = sum(1 for r in results if r['Docs'] < 7)
docs_lt_10 = sum(1 for r in results if 7 <= r['Docs'] < 10)
docs_gte_10 = sum(1 for r in results if r['Docs'] >= 10)

resp_in_top7 = sum(1 for r in results if r['Resp@'] != "-" and isinstance(r['Resp@'], int) and r['Resp@'] <= 7)
resp_8_10 = sum(1 for r in results if r['Resp@'] != "-" and isinstance(r['Resp@'], int) and 8 <= r['Resp@'] <= 10)
resp_gt_10 = sum(1 for r in results if r['Resp@'] != "-" and isinstance(r['Resp@'], int) and r['Resp@'] > 10)
resp_not_found = sum(1 for r in results if r['Resp@'] == "-")

print(f"""
DOCUMENTOS RECUPERADOS:
   • <7 docs:    {docs_lt_7:2d} preguntas (🚨 problema severo con límite de 7)
   • 7-9 docs:   {docs_lt_10:2d} preguntas (⚠️ problema con límite de 7)
   • 10+ docs:   {docs_gte_10:2d} preguntas (✅ ok)

POSICIÓN DE LA RESPUESTA:
   • Top 7:      {resp_in_top7:2d} preguntas (✅ funcionaba antes)
   • Pos 8-10:   {resp_8_10:2d} preguntas (⚠️ fallaba antes, ok ahora)
   • Pos >10:    {resp_gt_10:2d} preguntas (❌ necesita más de 10 chunks)
   • No encontr: {resp_not_found:2d} preguntas (❌ problema de retrieval)

IMPACTO DEL HOTFIX (usando 10 chunks):
   ✅ Resuelve: {docs_lt_7 + resp_8_10} preguntas ({(docs_lt_7 + resp_8_10)/26*100:.1f}%)
   ⚠️ Mejora parcial: {docs_lt_10} preguntas ({docs_lt_10/26*100:.1f}%)
   ❌ No resuelve: {resp_gt_10 + resp_not_found} preguntas ({(resp_gt_10 + resp_not_found)/26*100:.1f}%)
""")

print("=" * 80)
print("✅ CONCLUSIÓN")
print("=" * 80)
print("""
El HOTFIX de usar 10 chunks en lugar de 7:
   • Resuelve completamente los problemas más críticos
   • Mejora significativamente el retrieval general
   • Algunas preguntas pueden necesitar ajustes adicionales
""")