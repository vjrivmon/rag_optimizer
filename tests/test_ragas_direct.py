#!/usr/bin/env python3
"""
Test directo de RAGAs con Ollama - Verificar que funciona
"""

import sys
sys.path.insert(0, '/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')

# Suprimir warnings
import warnings
warnings.filterwarnings('ignore')

from langchain_ollama import ChatOllama
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import faithfulness
from ragas import evaluate
from datasets import Dataset
from langchain_community.embeddings import HuggingFaceEmbeddings

print("🔍 TEST DIRECTO RAGAs + Ollama")
print("=" * 60)

# Configurar LLM exactamente como en el commit que funcionaba
print("📦 Configurando LLM...")
ollama_llm = ChatOllama(
    model="gemma2:27b",
    base_url="https://ollama.gti-ia.upv.es:443",
    temperature=0.1,
    client_kwargs={"verify": False, "timeout": 180}
)

# Wrap para RAGAs
wrapped_llm = LangchainLLMWrapper(ollama_llm)

# Embeddings locales
embeddings = HuggingFaceEmbeddings(
    model_name="paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'}
)

# Datos de prueba mínimos
data = {
    'question': ["What is 2+2?"],
    'answer': ["4"],
    'contexts': [["2+2=4"]],
    'ground_truth': ["4"]
}

dataset = Dataset.from_dict(data)

print("🚀 Evaluando con faithfulness...")

try:
    result = evaluate(
        dataset,
        metrics=[faithfulness],
        llm=wrapped_llm,
        embeddings=embeddings
    )

    print("✅ ÉXITO!")
    df = result.to_pandas()
    print(f"Faithfulness: {df['faithfulness'].iloc[0]}")

except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}")
    print(f"Mensaje: {str(e)[:500]}")

print("=" * 60)