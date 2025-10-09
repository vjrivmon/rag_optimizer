#!/usr/bin/env python3
"""
Debug detallado del problema con RAGAs y Ollama
"""

import sys
import json
sys.path.insert(0, '/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')

from langchain_ollama import ChatOllama
from langchain.callbacks import StdOutCallbackHandler
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import faithfulness
from ragas import evaluate
from datasets import Dataset
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except:
    from langchain_community.embeddings import HuggingFaceEmbeddings

# Configurar LLM con callback para ver prompts y respuestas
print("🔍 DEBUG RAGAs - Capturando prompts y respuestas")
print("=" * 60)

# Crear LLM con callback para debug
ollama_llm = ChatOllama(
    model="gemma2:27b",
    base_url="https://ollama.gti-ia.upv.es:443",
    temperature=0.1,
    client_kwargs={"verify": False, "timeout": 120},
    callbacks=[StdOutCallbackHandler()]  # Esto imprimirá prompts y respuestas
)

# Wrap para RAGAs
wrapped_llm = LangchainLLMWrapper(ollama_llm)

# Embeddings locales
embeddings = HuggingFaceEmbeddings(
    model_name="paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'}
)

# Datos de prueba simples
data = {
    'question': ["¿Qué se hace en la actividad de desayunos?"],
    'answer': ["En la actividad se reparte comida a personas sin hogar."],
    'contexts': [["Se reparte comida", "Los voluntarios ayudan", "Es una actividad solidaria"]],
    'ground_truth': ["Se reparte desayunos a personas sin hogar con voluntarios."]
}

dataset = Dataset.from_dict(data)

print("\n📋 Dataset de prueba:")
print(f"  Question: {data['question'][0]}")
print(f"  Answer: {data['answer'][0]}")
print(f"  Contexts: {data['contexts'][0]}")
print(f"  Ground truth: {data['ground_truth'][0]}")

print("\n🚀 Iniciando evaluación con RAGAs...")
print("-" * 60)

try:
    # Intentar evaluar solo con faithfulness para simplificar
    result = evaluate(
        dataset,
        metrics=[faithfulness],
        llm=wrapped_llm,
        embeddings=embeddings
    )

    print("\n✅ Evaluación exitosa!")
    df = result.to_pandas()
    print(df)

except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}")
    print(f"   Mensaje: {str(e)}")

    # Si es OutputParserException, intentar capturar más detalles
    if "OutputParserException" in str(e):
        print("\n🔍 Análisis del error:")
        print("   RAGAs esperaba un formato diferente en la respuesta del LLM")
        print("   Posiblemente el modelo no está siguiendo las instrucciones del prompt")

        # Intentar extraer lo que el modelo devolvió
        error_msg = str(e)
        if "Got:" in error_msg:
            got_part = error_msg.split("Got:")[1].strip()
            print(f"\n   Lo que el modelo devolvió: {got_part[:500]}")