#!/usr/bin/env python3
"""
Test simplificado del benchmark con RAGAs
"""

import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')

from src.evaluation.ragas_evaluator import OllamaRAGASEvaluator

print("🧪 TEST BENCHMARK SIMPLIFICADO")
print("=" * 60)

# Crear evaluador
evaluator = OllamaRAGASEvaluator(
    model_name="gemma2:27b",
    base_url="https://ollama.gti-ia.upv.es:443",
    filter_thinking_tags=True
)

# Pregunta de prueba
question = "¿Qué se hace en la actividad de desayunos?"
answer = """En la actividad de desayunos solidarios, se reparte comida y se ofrece
compañía a personas sin hogar. Los voluntarios se dividen en grupos y recorren
distintas zonas de Valencia, entregando desayunos que incluyen productos como
napolitanas valencianas, leche, café y azúcar. Lo más importante de esta
actividad no es solo la comida, sino el tiempo y la conversación que se
comparte con las personas vulnerables."""

contexts = [
    "La actividad de desayunos consiste en repartir comida a personas sin hogar.",
    "Los voluntarios se reúnen en un punto de encuentro y se dividen en grupos.",
    "Cada grupo recorre una zona de Valencia repartiendo desayunos.",
    "Se reparten productos como napolitanas valencianas, leche, café y azúcar.",
    "Lo más importante es el tiempo que se comparte, no solo la comida.",
    "Los grupos se reúnen después para compartir experiencias.",
    "La actividad busca ofrecer compañía además de alimento.",
    "Se realiza los sábados por la mañana.",
    "El tiempo estimado es de una hora y media más desayuno opcional.",
    "La asociación compra los alimentos y paga por transferencia bancaria."
]

ground_truth = """La actividad consiste en que un grupo de voluntarios se reúne
en un punto de encuentro, se dividen en equipos, y cada uno recorre una zona
de Valencia repartiendo desayunos o cenas a personas sin hogar. Lo más
importante no es la comida, sino el tiempo que se comparte con ellas
(conversación, compañía)."""

print("\n📊 Evaluando pregunta con RAGAs...")
print(f"   Pregunta: {question[:50]}...")
print(f"   Respuesta: {answer[:50]}...")
print(f"   Contextos: {len(contexts)} documentos")
print(f"   Ground truth: Sí")

try:
    import time
    start = time.time()

    metrics = evaluator.evaluate_single(
        question=question,
        answer=answer,
        contexts=contexts,
        ground_truth=ground_truth
    )

    elapsed = time.time() - start

    if metrics:
        print(f"\n✅ ÉXITO en {elapsed:.1f} segundos!")
        print("\n📈 Métricas RAGAs:")
        for metric, value in metrics.items():
            if value is not None and str(value) != 'nan':
                print(f"   • {metric}: {value:.3f}")
    else:
        print(f"\n⚠️ No se obtuvieron métricas ({elapsed:.1f}s)")

except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}")
    print(f"   {str(e)[:200]}")

print("\n" + "=" * 60)
print("🏁 Test completado")