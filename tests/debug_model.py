#!/usr/bin/env python3
"""Script de debug para probar modelos individuales"""

import sys
import traceback
from src.core.model_wrapper import LLMWrapper
from src.core.rag_engine import ConfigurableRAGEngine

def test_model(model_name):
    """Prueba un modelo específico"""

    print(f"\n{'='*80}")
    print(f"🧪 PRUEBA DE MODELO: {model_name}")
    print(f"{'='*80}\n")

    # Crear RAG Engine
    print("📚 Cargando RAG Engine...")
    rag = ConfigurableRAGEngine("data/vectorstore/chroma_db")

    # Crear modelo
    print(f"🤖 Inicializando {model_name}...")
    model = LLMWrapper(
        model_name=model_name,
        api_endpoint="https://ollama.gti-ia.upv.es:443/api/generate",
        context_window=2048
    )

    # Pregunta de prueba
    question = "¿Qué se hace en la actividad de desayunos?"
    print(f"❓ Pregunta: {question}\n")

    # Recuperar contexto
    print("📚 Recuperando contexto...")
    docs = rag.retrieve(question)
    context_text = rag.build_context(docs[:5])
    print(f"   ✓ {len(docs)} documentos recuperados\n")

    # Generar prompt
    print("📝 Generando prompt...")
    prompt = model.build_rag_prompt(question, context_text, 'high')
    print(f"   ✓ Prompt de {len(prompt)} caracteres\n")

    # Generar respuesta
    print("🚀 Generando respuesta...")
    try:
        generation = model.generate(
            prompt,
            temperature=0.3,
            top_p=0.9,
            max_tokens=512
        )

        if generation['success']:
            print(f"   ✅ SUCCESS!")
            print(f"   ⏱️  Latencia: {generation['latency']:.2f}s")
            print(f"   📏 Respuesta: {len(generation['response'])} caracteres")
            print(f"\n{'─'*80}")
            print(f"📄 RESPUESTA COMPLETA:")
            print(f"{'─'*80}")
            print(generation['response'][:500])
            if len(generation['response']) > 500:
                print(f"\n... (truncado, {len(generation['response']) - 500} chars más)")
        else:
            print(f"   ❌ ERROR!")
            print(f"   ⏱️  Latencia: {generation['latency']:.2f}s")
            print(f"\n{'─'*80}")
            print(f"❌ DETALLE DEL ERROR:")
            print(f"{'─'*80}")
            print(generation.get('error', 'No error message'))

    except Exception as e:
        print(f"   ❌ EXCEPCIÓN CAPTURADA!")
        print(f"\n{'─'*80}")
        print(f"❌ TRACEBACK COMPLETO:")
        print(f"{'─'*80}")
        traceback.print_exc()

if __name__ == "__main__":
    models = [
        "qwen3:32b",
        "deepseek-r1:latest",
        "gemma2:27b",
        "llama3.3:70b"
    ]

    if len(sys.argv) > 1:
        # Probar solo el modelo especificado
        test_model(sys.argv[1])
    else:
        # Probar todos los modelos
        for model in models:
            try:
                test_model(model)
                print("\n")
            except KeyboardInterrupt:
                print("\n\n⚠️  Prueba interrumpida por el usuario")
                break
