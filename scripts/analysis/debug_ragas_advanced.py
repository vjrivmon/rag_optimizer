#!/usr/bin/env python3
"""
Debug avanzado: Interceptar y registrar las llamadas al LLM
"""
import sys
import json
import re
sys.path.insert(0, '/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')

from langchain_ollama import ChatOllama
from langchain.callbacks.base import BaseCallbackHandler
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import faithfulness
from ragas import evaluate
from datasets import Dataset
from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import Any, Dict, List

class DebugCallbackHandler(BaseCallbackHandler):
    """Handler para capturar todos los prompts y respuestas"""

    def __init__(self):
        self.prompts = []
        self.responses = []
        self.errors = []

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Capturar cuando se inicia una llamada al LLM"""
        print("\n" + "="*60)
        print("🔵 PROMPT ENVIADO AL LLM:")
        print("-"*60)
        for i, prompt in enumerate(prompts):
            self.prompts.append(prompt)
            print(f"Prompt {i+1}:\n{prompt[:1000]}...")  # Solo primeros 1000 chars
            if len(prompt) > 1000:
                print(f"... (truncado, total: {len(prompt)} caracteres)")

    def on_llm_end(self, response: Any, **kwargs) -> None:
        """Capturar cuando termina una llamada al LLM"""
        print("\n" + "-"*60)
        print("🟢 RESPUESTA DEL LLM:")
        print("-"*60)

        try:
            # Intentar extraer el texto de la respuesta
            if hasattr(response, 'generations'):
                for gen_list in response.generations:
                    for gen in gen_list:
                        text = gen.text if hasattr(gen, 'text') else str(gen)
                        self.responses.append(text)
                        print(f"{text[:1000]}...")  # Solo primeros 1000 chars
                        if len(text) > 1000:
                            print(f"... (truncado, total: {len(text)} caracteres)")

                        # Detectar si es JSON
                        if text.strip().startswith('{'):
                            print("\n📊 Parece ser JSON, intentando parsear:")
                            try:
                                parsed = json.loads(text)
                                print(json.dumps(parsed, indent=2, ensure_ascii=False)[:500])
                            except:
                                print("   ⚠️ No se pudo parsear como JSON")
        except Exception as e:
            print(f"Error extrayendo respuesta: {e}")

    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Capturar errores"""
        print("\n" + "="*60)
        print(f"🔴 ERROR EN LLM: {error}")
        self.errors.append(str(error))

# Configurar LLM con callback de debug
debug_handler = DebugCallbackHandler()

ollama_llm = ChatOllama(
    model="gemma2:27b",
    base_url="https://ollama.gti-ia.upv.es:443",
    temperature=0.0,  # Temperatura 0 para máxima consistencia
    client_kwargs={"verify": False, "timeout": 120},
    callbacks=[debug_handler]
)

# Wrap para RAGAs
wrapped_llm = LangchainLLMWrapper(ollama_llm)

# Embeddings locales
embeddings = HuggingFaceEmbeddings(
    model_name="paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'}
)

# Datos de prueba
data = {
    'question': ["What is the capital of France?"],
    'answer': ["The capital of France is Paris."],
    'contexts': [["France is a country in Europe.", "Paris is the capital city of France.", "The Eiffel Tower is in Paris."]],
    'ground_truth': ["Paris is the capital of France."]
}

dataset = Dataset.from_dict(data)

print("🔍 DEBUG AVANZADO RAGAs - Interceptando llamadas al LLM")
print("=" * 60)
print("\n📋 Dataset de prueba (en inglés para mejor compatibilidad):")
print(f"  Question: {data['question'][0]}")
print(f"  Answer: {data['answer'][0]}")
print(f"  Contexts: {data['contexts'][0]}")
print(f"  Ground truth: {data['ground_truth'][0]}")

print("\n🚀 Iniciando evaluación con RAGAs (faithfulness)...")
print("=" * 60)

try:
    # Evaluar
    result = evaluate(
        dataset,
        metrics=[faithfulness],
        llm=wrapped_llm,
        embeddings=embeddings
    )

    print("\n" + "=" * 60)
    print("✅ EVALUACIÓN COMPLETADA")
    print("=" * 60)

    df = result.to_pandas()
    print("\n📊 Resultados:")
    print(df)

    print(f"\n📝 Total de prompts enviados: {len(debug_handler.prompts)}")
    print(f"📝 Total de respuestas recibidas: {len(debug_handler.responses)}")
    print(f"📝 Total de errores: {len(debug_handler.errors)}")

    # Analizar si hay patrones problemáticos en las respuestas
    print("\n🔍 Análisis de respuestas:")
    for i, resp in enumerate(debug_handler.responses):
        print(f"\nRespuesta {i+1}:")
        # Buscar si contiene JSON estructurado
        if "TP" in resp or "FP" in resp or "FN" in resp:
            print("  ✓ Contiene TP/FP/FN (formato esperado para faithfulness)")
        else:
            print("  ⚠️ NO contiene TP/FP/FN - posible problema de formato")

        # Buscar tags de thinking
        if "<think>" in resp.lower():
            print("  ⚠️ Contiene tags <think> - podría interferir con parsing")

except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}")
    print(f"   Mensaje completo:\n{str(e)}")

    # Más análisis si es OutputParserException
    if "OutputParserException" in str(e):
        print("\n🔍 ANÁLISIS DEL ERROR DE PARSING:")
        error_msg = str(e)

        # Extraer lo que esperaba vs lo que obtuvo
        if "Expected" in error_msg and "Got" in error_msg:
            expected = error_msg.split("Expected")[1].split("Got")[0].strip()
            got = error_msg.split("Got:")[1].strip() if "Got:" in error_msg else "Unknown"

            print(f"\n📌 RAGAs esperaba:")
            print(f"   {expected[:500]}")
            print(f"\n📌 El modelo devolvió:")
            print(f"   {got[:500]}")

print("\n" + "=" * 60)
print("🏁 FIN DEL DEBUG")