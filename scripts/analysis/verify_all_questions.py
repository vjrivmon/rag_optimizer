#!/usr/bin/env python3
"""
Verificación exhaustiva de las 26 preguntas del dataset
Identifica qué preguntas pueden tener problemas de retrieval
"""

import json
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from pathlib import Path

def load_dataset():
    """Carga el dataset de evaluación"""
    with open('data/evaluation_dataset.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def check_retrieval_quality(question, expected_answer, keywords, embeddings, collection):
    """Verifica la calidad del retrieval para una pregunta"""

    # Generar embedding
    query_embedding = embeddings.embed_query(question)

    # Buscar top 10 chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10
    )

    # Analizar resultados
    analysis = {
        'question': question,
        'expected_keywords': keywords,
        'found_keywords': set(),
        'best_score': 1 - results['distances'][0][0] if results['distances'][0] else 0,
        'chunk_positions': {},
        'status': 'UNKNOWN'
    }

    # Buscar keywords en los chunks recuperados
    for i, doc in enumerate(results['documents'][0][:5]):  # Revisar top 5
        doc_lower = doc.lower()
        for keyword in keywords:
            if keyword.lower() in doc_lower:
                analysis['found_keywords'].add(keyword)
                if keyword not in analysis['chunk_positions']:
                    analysis['chunk_positions'][keyword] = i + 1

    # Determinar status
    coverage = len(analysis['found_keywords']) / len(keywords) if keywords else 0

    if coverage >= 0.5 and analysis['best_score'] > 0.4:
        analysis['status'] = 'GOOD'
    elif coverage >= 0.3 or analysis['best_score'] > 0.3:
        analysis['status'] = 'PARTIAL'
    else:
        analysis['status'] = 'POOR'

    # Verificar si la respuesta esperada está en algún chunk
    answer_found = False
    for i, doc in enumerate(results['documents'][0][:10]):
        # Verificar si fragmentos clave de la respuesta están en el chunk
        if len(expected_answer) > 50:
            # Para respuestas largas, buscar fragmentos clave
            key_fragments = expected_answer[:100].lower().split('.')
            for fragment in key_fragments:
                if len(fragment) > 20 and fragment.strip() in doc.lower():
                    answer_found = True
                    analysis['answer_found_at'] = i + 1
                    break
        else:
            # Para respuestas cortas, buscar coincidencia más directa
            if any(word in doc.lower() for word in expected_answer.lower().split()[:5]):
                answer_found = True
                analysis['answer_found_at'] = i + 1
                break

    analysis['answer_in_retrieval'] = answer_found

    return analysis

def main():
    print("=" * 80)
    print("VERIFICACIÓN EXHAUSTIVA DE LAS 26 PREGUNTAS")
    print("=" * 80)

    # Cargar dataset
    dataset = load_dataset()
    print(f"\n📚 Dataset cargado: {len(dataset)} preguntas")

    # Configurar embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Conectar a ChromaDB
    client = chromadb.PersistentClient(path="data/vectorstore/chroma_db")
    collection = client.get_collection(name="rag_collection_fixed_v2")

    print("\n🔍 Analizando retrieval para cada pregunta...")
    print("=" * 80)

    # Categorizar resultados
    good_questions = []
    partial_questions = []
    poor_questions = []

    for i, item in enumerate(dataset, 1):
        analysis = check_retrieval_quality(
            item['question'],
            item['expected_answer'],
            item['keywords'],
            embeddings,
            collection
        )

        # Mostrar progreso
        if i % 5 == 0:
            print(f"   Procesadas {i}/26 preguntas...")

        # Categorizar
        if analysis['status'] == 'GOOD':
            good_questions.append(analysis)
        elif analysis['status'] == 'PARTIAL':
            partial_questions.append(analysis)
        else:
            poor_questions.append(analysis)

    # Mostrar resultados
    print("\n" + "=" * 80)
    print("RESULTADOS DEL ANÁLISIS")
    print("=" * 80)

    print(f"\n✅ GOOD ({len(good_questions)}/26): Keywords encontrados y buen score")
    for q in good_questions:
        coverage = len(q['found_keywords']) / len(q['expected_keywords']) if q['expected_keywords'] else 0
        print(f"   Q{dataset.index(next(d for d in dataset if d['question'] == q['question']))+1}: "
              f"{q['question'][:50]}... (coverage: {coverage:.0%}, score: {q['best_score']:.2f})")

    print(f"\n⚠️ PARTIAL ({len(partial_questions)}/26): Algunos keywords o score medio")
    for q in partial_questions:
        coverage = len(q['found_keywords']) / len(q['expected_keywords']) if q['expected_keywords'] else 0
        missing = set(q['expected_keywords']) - q['found_keywords']
        print(f"   Q{dataset.index(next(d for d in dataset if d['question'] == q['question']))+1}: "
              f"{q['question'][:50]}...")
        print(f"      Coverage: {coverage:.0%}, Score: {q['best_score']:.2f}")
        if missing:
            print(f"      Missing keywords: {', '.join(list(missing)[:3])}")

    print(f"\n❌ POOR ({len(poor_questions)}/26): Pocos keywords y score bajo")
    for q in poor_questions:
        coverage = len(q['found_keywords']) / len(q['expected_keywords']) if q['expected_keywords'] else 0
        print(f"   Q{dataset.index(next(d for d in dataset if d['question'] == q['question']))+1}: "
              f"{q['question'][:50]}...")
        print(f"      Coverage: {coverage:.0%}, Score: {q['best_score']:.2f}")
        print(f"      Found keywords: {q['found_keywords'] if q['found_keywords'] else 'NONE'}")
        if not q['answer_in_retrieval']:
            print(f"      ⚠️ PROBLEMA: Respuesta NO encontrada en top 10 chunks")

    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)

    print(f"\n📊 Distribución de calidad:")
    print(f"   ✅ GOOD:    {len(good_questions):2d}/26 ({len(good_questions)/26*100:.1f}%)")
    print(f"   ⚠️ PARTIAL: {len(partial_questions):2d}/26 ({len(partial_questions)/26*100:.1f}%)")
    print(f"   ❌ POOR:    {len(poor_questions):2d}/26 ({len(poor_questions)/26*100:.1f}%)")

    # Identificar las más problemáticas
    critical_issues = [q for q in poor_questions if not q.get('answer_in_retrieval', True)]

    if critical_issues:
        print(f"\n🚨 PROBLEMAS CRÍTICOS ({len(critical_issues)} preguntas):")
        for q in critical_issues:
            idx = dataset.index(next(d for d in dataset if d['question'] == q['question']))
            print(f"\n   Q{idx+1}: {q['question']}")
            print(f"   Expected: {dataset[idx]['expected_answer'][:100]}...")
            print(f"   Keywords: {dataset[idx]['keywords']}")
            print(f"   Status: La respuesta NO se encuentra en los chunks recuperados")

    print("\n" + "=" * 80)
    print("RECOMENDACIONES")
    print("=" * 80)

    if len(poor_questions) > 5:
        print("\n⚠️ Hay varias preguntas con problemas de retrieval.")
        print("   Recomendaciones:")
        print("   1. El sistema híbrido (BM25) debería ayudar con keywords")
        print("   2. Considerar ajustar threshold de similaridad")
        print("   3. Algunas preguntas pueden necesitar reformulación")
    else:
        print("\n✅ La mayoría de preguntas tienen buen retrieval")
        print("   El benchmark debería mostrar buenos resultados")

    # Guardar análisis detallado
    output_file = 'retrieval_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total': 26,
                'good': len(good_questions),
                'partial': len(partial_questions),
                'poor': len(poor_questions),
                'critical': len(critical_issues)
            },
            'good_questions': good_questions,
            'partial_questions': partial_questions,
            'poor_questions': poor_questions
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Análisis detallado guardado en: {output_file}")

if __name__ == "__main__":
    main()