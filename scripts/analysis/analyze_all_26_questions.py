#!/usr/bin/env python3
"""
Análisis exhaustivo de las 26 preguntas para detectar problemas de retrieval
"""

import json
import sys
from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("🔍 ANÁLISIS EXHAUSTIVO DE LAS 26 PREGUNTAS")
print("=" * 80)

# Cargar dataset
with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Configurar embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Conectar a vector store (como lo hace benchmark.py)
from src.core.rag_engine import ConfigurableRAGEngine

print("\n📚 Inicializando RAG Engine...")
rag = ConfigurableRAGEngine(use_hybrid=True)

# Análisis de cada pregunta
results = []
problematic_questions = []
critical_issues = []

print("\n🔍 Analizando cada pregunta...")
print("-" * 80)

for idx, q_data in enumerate(dataset, 1):
    question = q_data['question']
    expected = q_data['expected_answer']
    keywords = q_data['keywords']

    # Recuperar documentos
    docs = rag.retrieve(question)

    # Analizar los primeros 10 chunks
    keywords_found = set()
    answer_fragments_found = False
    critical_info_position = None

    # Buscar keywords y fragmentos de respuesta en top 10
    for i, doc in enumerate(docs[:10]):
        doc_content = doc['content'].lower()

        # Buscar keywords
        for kw in keywords:
            if kw.lower() in doc_content:
                keywords_found.add(kw)

        # Buscar fragmentos de respuesta (primeras 5 palabras importantes)
        answer_words = [w for w in expected.lower().split()[:10]
                        if len(w) > 3 and w not in ['para', 'desde', 'hacia', 'entre']]

        if sum(1 for w in answer_words[:5] if w in doc_content) >= 3:
            answer_fragments_found = True
            if critical_info_position is None:
                critical_info_position = i + 1

    # Buscar en chunks 11-20 si no se encontró en top 10
    if not answer_fragments_found and len(docs) > 10:
        for i, doc in enumerate(docs[10:20], 11):
            doc_content = doc['content'].lower()
            answer_words = [w for w in expected.lower().split()[:10]
                           if len(w) > 3 and w not in ['para', 'desde', 'hacia', 'entre']]
            if sum(1 for w in answer_words[:5] if w in doc_content) >= 3:
                critical_info_position = i
                break

    # Calcular coverage
    coverage = len(keywords_found) / len(keywords) if keywords else 0

    # Determinar estado
    if answer_fragments_found and coverage >= 0.5:
        status = "✅ OK"
    elif answer_fragments_found or coverage >= 0.3:
        status = "⚠️ PARCIAL"
    else:
        status = "❌ PROBLEMA"
        problematic_questions.append(idx)

    # Detectar problemas críticos
    if len(docs) < 10:
        status = "🚨 CRÍTICO"
        critical_issues.append({
            'q_num': idx,
            'question': question[:50] + "...",
            'docs_retrieved': len(docs),
            'reason': f"Solo {len(docs)} docs recuperados (necesita 10)"
        })
    elif critical_info_position and critical_info_position > 10:
        if status != "✅ OK":
            status = "⚠️ INFO>10"
        critical_issues.append({
            'q_num': idx,
            'question': question[:50] + "...",
            'info_position': critical_info_position,
            'reason': f"Info crítica en posición {critical_info_position} (>10)"
        })

    result = {
        'Q': f"Q{idx}",
        'Pregunta': question[:40] + "..." if len(question) > 40 else question,
        'Docs': len(docs),
        'Top10_Cov': f"{coverage:.0%}",
        'Resp_En': "Top10" if answer_fragments_found else ("11-20" if critical_info_position else "NO"),
        'Estado': status
    }
    results.append(result)

    # Mostrar progreso
    if idx % 5 == 0:
        print(f"   Procesadas {idx}/26 preguntas...")

print("\n" + "=" * 80)
print("📊 TABLA DE RESULTADOS")
print("=" * 80)

# Mostrar tabla de resultados
headers = ['Q', 'Pregunta', 'Docs', 'Top10_Cov', 'Resp_En', 'Estado']
print("\n" + tabulate(results, headers=headers, tablefmt='grid'))

# Resumen de problemas
print("\n" + "=" * 80)
print("🚨 PROBLEMAS CRÍTICOS DETECTADOS")
print("=" * 80)

if critical_issues:
    print(f"\n⚠️ Se encontraron {len(critical_issues)} problemas críticos:\n")
    for issue in critical_issues:
        print(f"   Q{issue['q_num']}: {issue['question']}")
        print(f"      → {issue['reason']}")
        print()
else:
    print("\n✅ No se encontraron problemas críticos")

# Estadísticas generales
ok_count = sum(1 for r in results if "✅" in r['Estado'])
partial_count = sum(1 for r in results if "⚠️" in r['Estado'])
problem_count = sum(1 for r in results if "❌" in r['Estado'])
critical_count = sum(1 for r in results if "🚨" in r['Estado'])

print("\n" + "=" * 80)
print("📈 ESTADÍSTICAS GENERALES")
print("=" * 80)

print(f"""
Distribución de estados:
   ✅ OK:       {ok_count:2d}/26 ({ok_count/26*100:.1f}%)
   ⚠️ PARCIAL:  {partial_count:2d}/26 ({partial_count/26*100:.1f}%)
   ❌ PROBLEMA: {problem_count:2d}/26 ({problem_count/26*100:.1f}%)
   🚨 CRÍTICO:  {critical_count:2d}/26 ({critical_count/26*100:.1f}%)

Documentos recuperados:
   • Preguntas con <10 docs: {sum(1 for r in results if r['Docs'] < 10)}
   • Preguntas con 10+ docs: {sum(1 for r in results if r['Docs'] >= 10)}
   • Promedio de docs: {sum(r['Docs'] for r in results)/26:.1f}
""")

# Análisis del impacto del límite de 7 chunks
print("=" * 80)
print("⚠️ IMPACTO DEL LÍMITE DE 7 CHUNKS (ANTES DEL HOTFIX)")
print("=" * 80)

affected_questions = []
for r in results:
    q_num = int(r['Q'][1:])
    if r['Docs'] < 7:
        affected_questions.append({
            'q': q_num,
            'docs': r['Docs'],
            'impact': 'SEVERO - Solo usaba ' + str(r['Docs']) + ' chunks'
        })
    elif r['Resp_En'] in ['11-20', 'NO']:
        affected_questions.append({
            'q': q_num,
            'docs': r['Docs'],
            'impact': 'MODERADO - Info crítica fuera de top 7'
        })

if affected_questions:
    print(f"\n🔴 Preguntas afectadas por el límite de 7 chunks:\n")
    for aq in sorted(affected_questions, key=lambda x: x['q']):
        print(f"   Q{aq['q']}: {aq['impact']}")
else:
    print("\n✅ Ninguna pregunta adicional afectada")

# Recomendaciones finales
print("\n" + "=" * 80)
print("💡 RECOMENDACIONES")
print("=" * 80)

print("""
Con el HOTFIX aplicado (usando 10 chunks):
   ✅ Resuelve el problema de preguntas con <10 docs
   ✅ Mejora cobertura para respuestas en posiciones 8-10
   ✅ Mantiene buen balance sin dilución excesiva

Mejoras adicionales sugeridas:
""")

if sum(1 for r in results if r['Docs'] < 5) > 0:
    print("   1. ⚠️ Hay preguntas con <5 docs - considerar ajustar similarity_threshold")

if sum(1 for ci in critical_issues if ci.get('info_position', 0) > 15) > 0:
    print("   2. ⚠️ Algunas respuestas están en posición >15 - considerar reranking")

if partial_count > 10:
    print("   3. ⚠️ Muchas preguntas parciales - revisar calidad de embeddings")

print("\n✅ El hotfix debería mejorar significativamente los resultados")