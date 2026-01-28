#!/usr/bin/env python3
"""
Test de debug para entender el flujo de chunks en el chatbot
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.core.conversational_rag import ConversationalRAGEngine

def main():
    print("="*80)
    print("TEST DE DEBUG: Flujo de Chunks en Chatbot")
    print("="*80)
    print()

    # Inicializar componentes como en el chatbot
    VECTOR_STORE_PATH = project_root / "data" / "vectorstore" / "chroma_db"
    
    print("📦 Inicializando componentes...")
    model = LLMWrapper(
        model_name="gemma2:27b",
        api_endpoint="https://ollama.gti-ia.upv.es:443/api/generate"
    )
    print("   ✓ Modelo cargado")
    
    rag_engine = EnhancedRAGEngineNew(
        vector_store_path=str(VECTOR_STORE_PATH),
        model=model
    )
    print("   ✓ RAG Engine cargado")
    
    conversational_rag = ConversationalRAGEngine(
        base_rag_engine=rag_engine,
        model_wrapper=model
    )
    print("   ✓ Conversational RAG cargado")
    print()

    # Simular pregunta del usuario
    question = "¿Cómo me puedo apuntar a la actividad de desayunos?"
    session_id = "test_session_debug"
    question_id = 1
    
    print(f"❓ Pregunta de test: {question}")
    print()
    
    # Procesar query EXACTAMENTE como lo hace el chatbot
    print("🔍 Procesando con Conversational RAG...")
    result = conversational_rag.process_query(
        query=question,
        session_id=session_id,
        question_id=question_id
    )
    print()
    
    # Extraer datos como lo hace app.py
    print("📊 Extrayendo datos del resultado...")
    chunks = result.get('contexts', [])
    raw_chunks = result.get('raw_chunks', chunks)
    answer = result.get('answer', '')
    
    print(f"   Contexts (strings): {len(chunks)} elementos")
    print(f"   Raw chunks: {len(raw_chunks)} elementos")
    print(f"   Answer length: {len(answer)} chars")
    print()
    
    # DEBUG: Analizar estructura de raw_chunks
    print("="*80)
    print("ANÁLISIS DE RAW_CHUNKS")
    print("="*80)
    print()
    
    if raw_chunks:
        print(f"Total raw_chunks: {len(raw_chunks)}")
        print(f"Type of raw_chunks: {type(raw_chunks)}")
        print()
        
        for i, chunk in enumerate(raw_chunks[:3], 1):
            print(f"--- Chunk {i} ---")
            print(f"Type: {type(chunk)}")
            
            if isinstance(chunk, dict):
                print(f"Keys: {list(chunk.keys())}")
                if 'source' in chunk:
                    print(f"'source' in top level: {chunk['source']}")
                if 'metadata' in chunk:
                    print(f"'metadata' present: Yes")
                    if isinstance(chunk['metadata'], dict):
                        print(f"  Metadata keys: {list(chunk['metadata'].keys())}")
                        if 'source' in chunk['metadata']:
                            print(f"  Metadata['source']: {chunk['metadata']['source']}")
                    else:
                        print(f"  Metadata type: {type(chunk['metadata'])}")
                        print(f"  Metadata value: {chunk['metadata']}")
            elif hasattr(chunk, 'page_content'):
                print(f"Has page_content: True")
                print(f"Has metadata: {hasattr(chunk, 'metadata')}")
                if hasattr(chunk, 'metadata'):
                    print(f"Metadata type: {type(chunk.metadata)}")
                    print(f"Metadata: {chunk.metadata}")
            else:
                print(f"String or other: {str(chunk)[:100]}")
            print()
    
    # Intentar extract_top_chunks_info
    print("="*80)
    print("LLAMANDO A extract_top_chunks_info")
    print("="*80)
    print()
    
    top_chunks_info = rag_engine.extract_top_chunks_info(raw_chunks, top_n=3)
    
    print()
    print("="*80)
    print("RESULTADO DE extract_top_chunks_info")
    print("="*80)
    print()
    
    for chunk_info in top_chunks_info:
        print(f"Chunk {chunk_info['rank']}:")
        print(f"  Source: {chunk_info['source']}")
        print(f"  Score: {chunk_info['score']}")
        print(f"  Location: {chunk_info['location']}")
        print(f"  Content: {chunk_info['content'][:100]}...")
        print()


if __name__ == "__main__":
    main()
