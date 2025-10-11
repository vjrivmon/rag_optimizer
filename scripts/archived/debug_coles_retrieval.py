#!/usr/bin/env python3
"""
🔍 Debug específico del retrieval de preguntas COLES
Investiga por qué el Enhanced RAG Engine no recupera la información correcta
"""

import json
import re
from src.core.enhanced_rag_engine import EnhancedRAGEngine

def debug_coles_questions():
    """Debug específico de preguntas sobre COLES"""
    print("🔍 Debug de Retrieval - Preguntas COLES")
    print("=" * 60)

    # Inicializar Enhanced RAG Engine
    rag_engine = EnhancedRAGEngine(
        vector_store_path="data/vectorstore/chroma_db",
        use_hybrid=True
    )

    # Preguntas problemáticas sobre COLES
    problematic_questions = [
        {
            'id': 10,
            'question': '¿Qué se hace en la actividad de coles?',
            'expected_keywords': ['refuerzo escolar', 'colegio', 'niños', 'deberes', 'cuentos']
        },
        {
            'id': 12,
            'question': '¿Qué días vais a coles?',
            'expected_keywords': ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', '15:30', '16:30']
        },
        {
            'id': 13,
            'question': '¿Cuánto dura la actividad de coles?',
            'expected_keywords': ['15:30', '16:30', 'una hora']
        }
    ]

    # Cargar documentos COLES para comparar
    try:
        with open('data/documents/06_coles_refuerzo.txt', 'r', encoding='utf-8') as f:
            coles_document = f.read()
        print(f"📄 Documento COLES cargado: {len(coles_document)} caracteres")
    except FileNotFoundError:
        print("❌ No se encuentra el documento COLES")
        return

    for q_info in problematic_questions:
        print(f"\n" + "="*60)
        print(f"📝 Pregunta {q_info['id']}: {q_info['question']}")
        print(f"🎯 Keywords esperadas: {q_info['expected_keywords']}")
        print("-"*60)

        # Test 1: Retrieval con Enhanced RAG Engine
        print(f"\n🔍 Test 1: Enhanced RAG Engine")
        results = rag_engine.retrieve_with_fallback(q_info['question'])

        print(f"Resultados recuperados: {len(results)}")

        # Verificar si la información está en los chunks recuperados
        found_keywords = set()
        relevant_chunks = []

        for i, result in enumerate(results[:5]):  # Top 5
            content = result['content']
            print(f"\n  Chunk {i+1} (Score: {result['score']:.3f}):")
            content_preview = content[:200] + "..." if len(content) > 200 else content
            print(f"    Content: {content_preview}")

            # Buscar keywords esperados
            chunk_keywords = [kw for kw in q_info['expected_keywords'] if kw.lower() in content.lower()]
            if chunk_keywords:
                found_keywords.update(chunk_keywords)
                relevant_chunks.append((i, content, chunk_keywords))
                print(f"    ✅ Keywords encontrados: {chunk_keywords}")
            else:
                print(f"    ❌ No se encontraron keywords esperados")

        print(f"\n📊 Resumen Enhanced RAG Engine:")
        print(f"  - Keywords encontrados: {found_keywords}")
        print(f"  - Chunks relevantes: {len(relevant_chunks)}")
        print(f"  - Tasa de recuperación: {len(found_keywords)/len(q_info['expected_keywords'])*100:.1f}%")

        # Test 2: Búsqueda directa en el documento COLES
        print(f"\n🔍 Test 2: Búsqueda directa en documento COLES")
        for keyword in q_info['expected_keywords']:
            if keyword.lower() in coles_document.lower():
                print(f"  ✅ '{keyword}' encontrado en documento COLES")
                # Encontrar el contexto alrededor
                start_pos = coles_document.lower().find(keyword.lower())
                if start_pos != -1:
                    context_start = max(0, start_pos - 50)
                    context_end = min(len(coles_document), start_pos + 150)
                    context = coles_document[context_start:context_end]
                    print(f"    Contexto: ...{context}...")
            else:
                print(f"  ❌ '{keyword}' NO encontrado en documento COLES")

        # Test 3: Búsqueda con el Enhanced RAG Engine pero con queries alternativas
        print(f"\n🔍 Test 3: Queries alternativas")
        alternative_queries = [
            f"refuerzo escolar {q_info['question']}",
            f"colegio {q_info['question']}",
            f"niños {q_info['question']}",
            q_info['question'].replace('¿', '').replace('?', '')
        ]

        for alt_query in alternative_queries:
            alt_results = rag_engine.retrieve_with_fallback(alt_query)
            alt_found = [kw for kw in q_info['expected_keywords']
                         if any(kw.lower() in r['content'].lower() for r in alt_results)]

            if alt_found:
                print(f"  ✅ Query '{alt_query[:50]}...' encontró: {alt_found}")
            else:
                print(f"  ❌ Query '{alt_query[:50]}...' no encontró keywords")

        # Test 4: Análisis de embeddings
        print(f"\n🔍 Test 4: Análisis de similitud de embeddings")
        query_embedding = rag_engine.embeddings.embed_query(q_info['question'])

        # Buscar chunks más similares por similitud directa
        all_data = rag_engine.vector_store.get()
        similarities = []

        for i, (content, metadata) in enumerate(zip(all_data['documents'], all_data['metadatas'])):
            if 'coles' in content.lower() or 'refuerzo' in content.lower():
                chunk_embedding = rag_engine.embeddings.embed_query(content)
                # Calcular similitud coseno manualmente
                import numpy as np
                query_norm = np.linalg.norm(query_embedding)
                chunk_norm = np.linalg.norm(chunk_embedding)
                if query_norm > 0 and chunk_norm > 0:
                    similarity = np.dot(query_embedding, chunk_embedding) / (query_norm * chunk_norm)
                else:
                    similarity = 0.0
                similarities.append((similarity, i, content[:100], metadata.get('source', '')))

        # Top 5 chunks COLES más similares
        similarities.sort(reverse=True)
        print(f"  Top 5 chunks COLES más similares a la query:")
        for similarity, idx, preview, source in similarities[:5]:
            has_keywords = any(kw.lower() in preview.lower() for kw in q_info['expected_keywords'])
            status = "✅" if has_keywords else "❌"
            print(f"    {status} Sim={similarity:.3f}: {preview}... ({source})")

def test_vector_store_integrity():
    """Verifica la integridad del vector store"""
    print(f"\n🔍 Test de Integridad del Vector Store")
    print("=" * 60)

    rag_engine = EnhancedRAGEngine(
        vector_store_path="data/vectorstore/chroma_db",
        use_hybrid=True
    )

    all_data = rag_engine.vector_store.get()
    total_docs = len(all_data['documents'])

    print(f"📊 Total documentos en vector store: {total_docs}")

    # Buscar documentos COLES
    coles_docs = []
    refuerzo_docs = []

    for i, (content, metadata) in enumerate(zip(all_data['documents'], all_data['metadatas'])):
        if 'coles' in content.lower():
            coles_docs.append((i, content[:100], metadata.get('source', '')))
        if 'refuerzo' in content.lower():
            refuerzo_docs.append((i, content[:100], metadata.get('source', '')))

    print(f"📄 Documentos que mencionan 'coles': {len(coles_docs)}")
    print(f"📄 Documentos que mencionan 'refuerzo': {len(refuerzo_docs)}")

    # Mostrar ejemplos
    if coles_docs:
        print(f"\n📝 Ejemplos de documentos COLES:")
        for i, (idx, preview, source) in coles_docs[:3]:
            print(f"  {idx}: {preview}... ({source})")

    # Verificar si hay chunks específicos para las preguntas problemáticas
    print(f"\n🎯 Verificación de información específica:")

    specific_info = {
        "15:30": "días de coles",
        "16:30": "días de coles",
        "lunes": "días de coles",
        "martes": "días de coles",
        "miércoles": "días de coles",
        "jueves": "días de coles",
        "viernes": "días de coles",
        "una hora": "duración coles",
        "1 hora": "duración coles"
    }

    all_text = ' '.join(all_data['documents']).lower()

    for keyword, description in specific_info.items():
        if keyword in all_text:
            print(f"  ✅ '{keyword}' encontrado ({description})")
        else:
            print(f"  ❌ '{keyword}' NO encontrado ({description})")

def main():
    """Función principal"""
    print("🚀 Debug Específico de Retrieval COLES")
    print("=" * 70)

    debug_coles_questions()
    test_vector_store_integrity()

    print(f"\n💡 CONCLUSIONES INMEDIATAS:")
    print("1. Identificar exactamente por qué el retrieval falla para COLES")
    print("2. Verificar si el problema está en los embeddings o en la configuración")
    print("3. Determinar si se necesita mejorar el query expansion para COLES")

if __name__ == "__main__":
    main()