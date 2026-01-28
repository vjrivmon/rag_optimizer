#!/usr/bin/env python3
"""
🔍 Script de Diagnóstico para P22 - ¿Qué se hace en la actividad de resis?
Analiza por qué el sistema RAG no recupera la información correcta
"""

import json
import numpy as np
from typing import List, Dict, Any

# Imports del proyecto
from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper

def load_rag_system():
    """Carga el sistema RAG actual"""
    print("🔧 Cargando sistema RAG...")

    # Inicializar RAG engine con configuración actual
    rag_engine = ConfigurableRAGEngine(
        vector_store_path="data/vectorstore/chroma_db",
        use_hybrid=True
    )

    print(f"✅ RAG engine cargado")
    print(f"   - Vector store: {rag_engine.vector_store}")
    print(f"   - Hybrid retrieval: {rag_engine.use_hybrid}")
    print(f"   - Top k: {rag_engine.params['top_k']}")
    print(f"   - Similarity threshold: {rag_engine.params['similarity_threshold']}")
    print(f"   - Semantic weight: {rag_engine.params['semantic_weight']}")
    print(f"   - Keyword weight: {rag_engine.params['keyword_weight']}")

    return rag_engine

def test_query_retrieval(rag_engine: ConfigurableRAGEngine, query: str, question_id: int):
    """Testea qué chunks recupera una query específica"""
    print(f"\n🔍 Test de Retrieval - Pregunta {question_id}")
    print(f"Query: '{query}'")
    print("=" * 60)

    # Test 1: Retrieval con configuración actual
    print("\n📊 1. Retrieval con configuración ACTUAL:")
    results = rag_engine.retrieve(query)

    print(f"Chunks recuperados: {len(results)}")
    for i, result in enumerate(results[:5]):  # Top 5
        content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
        print(f"\nChunk {i+1} (Score: {result['score']:.3f}):")
        print(f"  Content: {content_preview}")
        print(f"  Metadata: {result.get('metadata', {})}")

    # Test 2: Buscar el chunk correcto manualmente
    print(f"\n🎯 2. Búsqueda manual del chunk CORRECTO:")
    all_data = rag_engine.vector_store.get()

    for i, content in enumerate(all_data['documents']):
        if "resis" in content.lower() and "actividad" in content.lower():
            print(f"\nChunk RESIS encontrado (índice {i}):")
            print(f"  Content: {content}")
            print(f"  Metadata: {all_data['metadatas'][i]}")

            # Calcular similitud con la query
            query_embedding = rag_engine.embeddings.embed_query(query)
            chunk_embedding = rag_engine.embeddings.embed_query(content)
            # Calcular similitud coseno manualmente
            query_norm = np.linalg.norm(query_embedding)
            chunk_norm = np.linalg.norm(chunk_embedding)
            if query_norm > 0 and chunk_norm > 0:
                similarity = np.dot(query_embedding, chunk_embedding) / (query_norm * chunk_norm)
            else:
                similarity = 0.0
            print(f"  Similitud con query: {similarity:.3f}")

    # Test 3: Probar diferentes variaciones de la query
    print(f"\n🔄 3. Testing variaciones de la query:")
    query_variations = [
        "¿Qué se hace en la actividad de resis?",  # Original
        "Qué actividades se realizan en resis",    # Sin signos de interrogación
        "actividades resis voluntarios",           # Keywords
        "resis actividades voluntariado",          # Permutación
        "voluntariado resis qué hacer",            # Reordenado
        "DNI resis actividades",                   # Con contexto DNI
    ]

    for variation in query_variations:
        var_results = rag_engine.retrieve(variation)
        # Buscar si aparece el chunk de resis en los resultados
        has_resis = any("resis" in r['content'].lower() for r in var_results[:3])
        print(f"  '{variation}' -> {'✅ RECUPERA' if has_resis else '❌ NO RECUPERA'} (Top-3)")

    return results

def test_different_configurations(rag_engine: ConfigurableRAGEngine, query: str):
    """Testea diferentes configuraciones del RAG"""
    print(f"\n⚙️ 4. Testing diferentes configuraciones:")

    # Configuraciones a probar
    configs = [
        {"name": "Actual", "params": rag_engine.params.copy()},
        {"name": "Más permisivo", "params": {**rag_engine.params, "similarity_threshold": 0.25}},
        {"name": "Más semantic", "params": {**rag_engine.params, "semantic_weight": 0.8, "keyword_weight": 0.2}},
        {"name": "Más keywords", "params": {**rag_engine.params, "semantic_weight": 0.4, "keyword_weight": 0.6}},
        {"name": "Más chunks", "params": {**rag_engine.params, "top_k": 15}},
        {"name": "Combinado", "params": {**rag_engine.params, "similarity_threshold": 0.2, "top_k": 15, "semantic_weight": 0.7, "keyword_weight": 0.3}},
    ]

    best_config = None
    best_score = 0

    for config in configs:
        # Actualizar configuración
        rag_engine.update_params(config["params"])

        # Test retrieval
        results = rag_engine.retrieve(query)

        # Evaluar si resis está en los resultados
        has_resis_in_top3 = any("resis" in r['content'].lower() for r in results[:3])
        has_resis_in_top5 = any("resis" in r['content'].lower() for r in results[:5])

        # Score simple: posición del primer chunk con resis
        resis_position = None
        for i, r in enumerate(results):
            if "resis" in r['content'].lower():
                resis_position = i + 1
                break

        config_score = 10 - resis_position if resis_position and resis_position <= 5 else 0

        print(f"\n  {config['name']}:")
        print(f"    Resis en Top-3: {'✅' if has_resis_in_top3 else '❌'}")
        print(f"    Resis en Top-5: {'✅' if has_resis_in_top5 else '❌'}")
        print(f"    Posición resis: {resis_position if resis_position else 'No encontrado'}")
        print(f"    Score: {config_score}/5")

        if config_score > best_score:
            best_score = config_score
            best_config = config['name']

    print(f"\n🏆 Mejor configuración: {best_config} (Score: {best_score}/5)")

    # Restaurar configuración original
    rag_engine.update_params(configs[0]["params"])

    return best_config

def analyze_embedding_distances(rag_engine: ConfigurableRAGEngine):
    """Analiza distancias entre embeddings"""
    print(f"\n📏 5. Análisis de distancias de embeddings:")

    # Query P22
    query_p22 = "¿Qué se hace en la actividad de resis?"

    # Query similar que funciona bien (ej: P2)
    query_working = "¿Dónde es el punto de encuentro de desayunos?"

    # Chunk correcto para P22 (del documento)
    correct_chunk_p22 = "¿Qué se hace en la actividad?\nEn este voluntariado vamos a pasar tiempo con los residentes de la Acollida. A través de distintas actividades buscamos llevarles la alegría de los jóvenes"

    # Embeddings
    emb_p22 = rag_engine.embeddings.embed_query(query_p22)
    emb_working = rag_engine.embeddings.embed_query(query_working)
    emb_correct = rag_engine.embeddings.embed_query(correct_chunk_p22)

    # Calcular similitudes manualmente
    def cosine_sim_manual(a, b):
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a > 0 and norm_b > 0:
            return np.dot(a, b) / (norm_a * norm_b)
        return 0.0

    sim_p22_correct = cosine_sim_manual(emb_p22, emb_correct)
    sim_working_correct = cosine_sim_manual(emb_working, emb_correct)

    print(f"Similitud P22 ↔ Chunk correcto: {sim_p22_correct:.3f}")
    print(f"Similitud Query funcionando ↔ Chunk P22: {sim_working_correct:.3f}")

    # Buscar chunks con alta similitud para P22
    all_data = rag_engine.vector_store.get()
    similarities = []

    for i, content in enumerate(all_data['documents']):
        emb_chunk = rag_engine.embeddings.embed_query(content)
        sim = cosine_sim_manual(emb_p22, emb_chunk)
        similarities.append((i, sim, content[:50] + "..." if len(content) > 50 else content))

    # Top 10 similitudes
    similarities.sort(key=lambda x: x[1], reverse=True)
    print(f"\nTop 10 chunks más similares a P22:")
    for i, (idx, sim, preview) in enumerate(similarities[:10]):
        has_resis = "resis" in all_data['documents'][idx].lower()
        print(f"  {i+1}. Sim={sim:.3f} | {'✅RESIS' if has_resis else '   '} | {preview}")

    return sim_p22_correct

def test_answer_generation(rag_engine: ConfigurableRAGEngine, query: str):
    """Testea generación de respuesta con diferentes modelos"""
    print(f"\n💬 6. Test de generación de respuesta:")

    models = ['gemma2:27b', 'llama3.3:70b', 'deepseek-r1:latest', 'qwen3:32b']

    for model in models:
        try:
            print(f"\n  Modelo: {model}")

            # Recuperar contexto
            results = rag_engine.retrieve(query)
            context_text = "\n".join([r['content'] for r in results[:3]])

            # Verificar si contiene información de resis
            has_resis = "resis" in context_text.lower()
            print(f"    Contexto contiene RESIS: {'✅' if has_resis else '❌'}")

            if has_resis:
                print(f"    Contexto (primeros 200 chars): {context_text[:200]}...")

        except Exception as e:
            print(f"    Error: {e}")

def main():
    """Función principal de diagnóstico"""
    print("🚀 Iniciando diagnóstico P22 - ¿Qué se hace en la actividad de resis?")
    print("=" * 70)

    # Cargar sistema RAG
    rag_engine = load_rag_system()

    # Query problemática
    p22_query = "¿Qué se hace en la actividad de resis?"

    # Test 1: Retrieval actual
    results = test_query_retrieval(rag_engine, p22_query, 22)

    # Test 2: Diferentes configuraciones
    best_config = test_different_configurations(rag_engine, p22_query)

    # Test 3: Análisis de embeddings
    similarity_score = analyze_embedding_distances(rag_engine)

    # Test 4: Generación de respuestas
    test_answer_generation(rag_engine, p22_query)

    # Resumen y recomendaciones
    print(f"\n" + "="*70)
    print(f"📋 RESUMEN DEL DIAGNÓSTICO")
    print(f"="*70)
    print(f"✅ Análisis completado")
    print(f"🎯 Mejor configuración encontrada: {best_config}")
    print(f"📏 Similitud query-chunk correcto: {similarity_score:.3f}")

    if similarity_score < 0.5:
        print(f"⚠️  PROBLEMA IDENTIFICADO: Baja similitud semántica (< 0.5)")
        print(f"💡 RECOMENDACIÓN: Usar query expansion o re-estructurar chunks")
    elif similarity_score >= 0.5:
        print(f"✅ Similitud adecuada: El problema está en la configuración del retrieval")
        print(f"💡 RECOMENDACIÓN: Aplicar la mejor configuración encontrada")

    print(f"\n🔧 ACCIONES INMEDIATAS SUGERIDAS:")
    print(f"1. Aplicar configuración '{best_config}' al sistema RAG")
    print(f"2. Implementar query expansion específica para preguntas RESIS")
    print(f"3. Añadir metadata específica para categorías (RESIS, DESAYUNOS, etc.)")

    print(f"\n📄 Guardando resultados en 'debug_p22_results.json'")

    # Guardar resultados
    debug_results = {
        "timestamp": str(np.datetime64('now')),
        "query": p22_query,
        "best_config": best_config,
        "similarity_score": float(similarity_score),
        "current_params": rag_engine.params,
        "recommendations": [
            "Aplicar mejor configuración encontrada",
            "Implementar query expansion para RESIS",
            "Añadir metadata específica por categoría"
        ]
    }

    with open('debug_p22_results.json', 'w', encoding='utf-8') as f:
        json.dump(debug_results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()