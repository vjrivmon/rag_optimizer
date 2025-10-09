#!/usr/bin/env python3
"""
Test del wrapper robusto para RAGAs
"""

import sys
sys.path.insert(0, '/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')

from src.evaluation.ollama_llm_wrapper import create_robust_ollama_for_ragas
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import faithfulness, context_recall, answer_relevancy
from ragas import evaluate
from datasets import Dataset
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except:
    from langchain_community.embeddings import HuggingFaceEmbeddings

print("🚀 TEST DEL WRAPPER ROBUSTO PARA RAGAs")
print("=" * 60)

# Crear LLM con wrapper robusto
print("\n📦 Creando wrapper robusto...")
robust_llm_base = create_robust_ollama_for_ragas(
    model_name="gemma2:27b",
    base_url="https://ollama.gti-ia.upv.es:443",
    temperature=0.0,
    debug=True  # Activar debug para ver el proceso
)

# Wrap para RAGAs
robust_llm = LangchainLLMWrapper(robust_llm_base)

# Embeddings locales
embeddings = HuggingFaceEmbeddings(
    model_name="paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'}
)

# Test 1: Inglés (debería funcionar bien)
print("\n" + "=" * 60)
print("TEST 1: INGLÉS")
print("-" * 60)

data_en = {
    'question': ["What is the capital of France?"],
    'answer': ["The capital of France is Paris."],
    'contexts': [["France is a country in Europe.", "Paris is the capital city of France."]],
    'ground_truth': ["Paris is the capital of France."]
}

dataset_en = Dataset.from_dict(data_en)

try:
    result = evaluate(
        dataset_en,
        metrics=[faithfulness, answer_relevancy],
        llm=robust_llm,
        embeddings=embeddings
    )
    print("✅ Test inglés exitoso!")
    print(f"   Faithfulness: {result['faithfulness']}")
    print(f"   Answer relevancy: {result['answer_relevancy']}")
except Exception as e:
    print(f"❌ Error en test inglés: {e}")

# Test 2: Español (más desafiante)
print("\n" + "=" * 60)
print("TEST 2: ESPAÑOL")
print("-" * 60)

data_es = {
    'question': ["¿Qué se hace en la actividad de desayunos?"],
    'answer': ["En la actividad se reparte comida y se comparte tiempo con personas sin hogar."],
    'contexts': [
        ["Se reparte comida a personas vulnerables",
         "Los voluntarios dedican tiempo para conversar",
         "La actividad busca dar compañía además de alimento"]
    ],
    'ground_truth': ["Se reparte desayunos y se comparte tiempo con personas sin hogar."]
}

dataset_es = Dataset.from_dict(data_es)

try:
    result = evaluate(
        dataset_es,
        metrics=[faithfulness, context_recall],
        llm=robust_llm,
        embeddings=embeddings
    )
    print("✅ Test español exitoso!")
    print(f"   Faithfulness: {result['faithfulness']}")
    print(f"   Context recall: {result['context_recall']}")
except Exception as e:
    print(f"❌ Error en test español: {e}")

# Test 3: Respuesta con thinking tags (caso problemático)
print("\n" + "=" * 60)
print("TEST 3: RESPUESTA CON THINKING TAGS")
print("-" * 60)

data_think = {
    'question': ["What is 2+2?"],
    'answer': ["<think>Let me calculate 2+2. It equals 4.</think>The answer is 4."],
    'contexts': [["Basic arithmetic: 2+2=4"]],
    'ground_truth': ["4"]
}

dataset_think = Dataset.from_dict(data_think)

try:
    result = evaluate(
        dataset_think,
        metrics=[faithfulness],
        llm=robust_llm,
        embeddings=embeddings
    )
    print("✅ Test thinking tags exitoso!")
    print(f"   Faithfulness: {result['faithfulness']}")
except Exception as e:
    print(f"❌ Error en test thinking tags: {e}")

print("\n" + "=" * 60)
print("🏁 TESTS COMPLETADOS")