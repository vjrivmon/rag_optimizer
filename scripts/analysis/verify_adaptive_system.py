#!/usr/bin/env python3
"""
Verificación rápida del sistema adaptativo
Comprueba que el clasificador y selector funcionan correctamente
"""

import warnings
from colorama import init, Fore, Style
from src.core.adaptive_rag import QuestionClassifier, create_adaptive_rag

# Inicializar
init(autoreset=True)
warnings.filterwarnings('ignore')

print(f"\n{Fore.CYAN}=== VERIFICACIÓN DEL SISTEMA ADAPTATIVO ==={Style.RESET_ALL}\n")

# Test 1: Verificar clasificador
print(f"{Fore.YELLOW}1. Test del Clasificador de Preguntas:{Style.RESET_ALL}")
classifier = QuestionClassifier()

test_questions = {
    "¿Dónde es la actividad de coles?": "simple",
    "¿Cuándo es la actividad?": "simple",
    "¿Quién paga la gasolina?": "simple",
    "¿Qué se hace en la actividad de desayunos?": "complex",
    "¿Cómo me apunto a desayunos solidarios?": "complex",
    "¿Qué significa Para-Mira-Ayuda?": "conceptual",
    "¿Por qué existe DNI?": "conceptual"
}

for question, expected_type in test_questions.items():
    classified_type = classifier.classify(question)
    if classified_type == expected_type:
        print(f"   ✅ {question[:30]:30s} -> {classified_type:10s}")
    else:
        print(f"   ❌ {question[:30]:30s} -> {classified_type:10s} (esperado: {expected_type})")

# Test 2: Verificar retrieval adaptativo
print(f"\n{Fore.YELLOW}2. Test del Retrieval Adaptativo:{Style.RESET_ALL}")
rag = create_adaptive_rag("data/vectorstore/chroma_db")

# Probar con una pregunta de cada tipo
test_cases = [
    ("¿Dónde es la actividad de coles?", "simple", 3, 5),
    ("¿Qué se hace en desayunos?", "complex", 5, 7),
    ("¿Qué significa DNI?", "conceptual", 6, 8)
]

for query, expected_type, min_chunks, max_chunks in test_cases:
    docs, metadata = rag.retrieve_adaptive(query)

    chunks_used = metadata['chunks_selected']
    actual_type = metadata['question_type']
    avg_relevance = metadata['avg_relevance']

    print(f"\n   Pregunta: {query}")
    print(f"   Tipo detectado: {actual_type} {'✅' if actual_type == expected_type else '❌'}")
    print(f"   Chunks: {chunks_used} (esperado: {min_chunks}-{max_chunks})")
    print(f"   Relevancia promedio: {avg_relevance:.2f}")

    if min_chunks <= chunks_used <= max_chunks:
        print(f"   {Fore.GREEN}✅ Chunks en rango correcto{Style.RESET_ALL}")
    else:
        print(f"   {Fore.RED}❌ Chunks fuera de rango{Style.RESET_ALL}")

# Test 3: Verificar que se están haciendo llamadas reales
print(f"\n{Fore.YELLOW}3. Test de Llamadas al Servidor:{Style.RESET_ALL}")

from src.core.model_wrapper import LLMWrapper
import time

model = LLMWrapper(
    model_name="gemma2:27b",
    api_endpoint="https://ollama.gti-ia.upv.es:443/api/generate"
)

test_prompt = "Responde con una palabra: ¿Cuál es la capital de España?"
print(f"   Enviando prompt de prueba al servidor...")
start = time.time()

try:
    response = model.generate(test_prompt, max_tokens=10)
    latency = time.time() - start

    if response['success']:
        print(f"   ✅ Respuesta recibida: '{response.get('answer', response['response'])[:50]}'")
        print(f"   Latencia: {latency:.2f}s")
        if latency > 0.5:
            print(f"   {Fore.GREEN}✅ Latencia realista para llamada real al servidor{Style.RESET_ALL}")
        else:
            print(f"   {Fore.YELLOW}⚠️ Latencia muy baja, podría ser caché{Style.RESET_ALL}")
    else:
        print(f"   {Fore.RED}❌ Error en respuesta: {response.get('error', 'Unknown')}{Style.RESET_ALL}")

except Exception as e:
    print(f"   {Fore.RED}❌ Error de conexión: {str(e)}{Style.RESET_ALL}")

print(f"\n{Fore.CYAN}=== FIN DE VERIFICACIÓN ==={Style.RESET_ALL}\n")