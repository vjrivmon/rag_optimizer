#!/usr/bin/env python3
"""
Test específico para verificar que Q6 funciona con el fix v2
"""

import sys
sys.path.append('.')

from src.core.rag_engine import ConfigurableRAGEngine
from src.models.model_wrapper import ModelWrapper

def test_q6():
    print("=" * 80)
    print("TEST Q6 CON VECTOR STORE v2")
    print("=" * 80)

    # Inicializar RAG
    rag = ConfigurableRAGEngine(use_hybrid=True)

    # Pregunta Q6
    question = "¿Cómo me apunto a desayunos solidarios?"
    print(f"\n📝 Pregunta: {question}")

    # Recuperar documentos
    docs = rag.retrieve(question)
    print(f"\n📚 Documentos recuperados: {len(docs)}")

    # Mostrar top 3 chunks
    print("\n🔍 Top 3 chunks:")
    for i, doc in enumerate(docs[:3]):
        content = doc['content'][:150].replace('\n', ' ')
        metadata = doc['metadata']
        print(f"\n{i+1}. Contenido: {content}...")
        print(f"   Tipo: {metadata.get('chunk_type', 'unknown')}")
        print(f"   Actividad: {metadata.get('activity', 'unknown')}")
        print(f"   Importancia: {metadata.get('importance', 'unknown')}")

        # Verificar si es el chunk correcto
        if "miércoles" in doc['content'].lower() and "formulario" in doc['content'].lower():
            print(f"   ✅ CHUNK CORRECTO!")

    # Generar respuesta con un modelo
    print("\n🤖 Generando respuesta con gemma2:27b...")

    # Configurar modelo
    model = ModelWrapper(
        model_name="gemma2:27b",
        api_url="https://ollama.gti-ia.upv.es:443/api/generate"
    )

    # Construir contexto
    context = rag.build_context(docs[:7])

    # Generar respuesta
    prompt = f"""Usando ÚNICAMENTE la siguiente información, responde la pregunta de forma concisa y directa.

Contexto:
{context}

Pregunta: {question}

Respuesta:"""

    response = model.generate(prompt)
    print(f"\n📝 Respuesta del modelo:")
    print(response['answer'])

    # Verificar calidad de la respuesta
    keywords = ["miércoles", "formulario", "whatsapp", "sábado", "inscrib"]
    found = [k for k in keywords if k.lower() in response['answer'].lower()]

    print(f"\n✅ Palabras clave encontradas: {found}")

    if len(found) >= 3:
        print("\n🎉 ÉXITO: La respuesta contiene información correcta sobre cómo apuntarse")
        return True
    else:
        print("\n❌ PROBLEMA: La respuesta no contiene suficiente información")
        return False

if __name__ == "__main__":
    success = test_q6()
    sys.exit(0 if success else 1)