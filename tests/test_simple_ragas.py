#!/usr/bin/env python3
"""
Test simplificado del wrapper robusto - solo probar que funciona
"""

import sys
sys.path.insert(0, '/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')

from src.evaluation.ragas_evaluator import OllamaRAGASEvaluator

print("🧪 TEST SIMPLE DE RAGAs CON WRAPPER ROBUSTO")
print("=" * 60)

# Inicializar evaluador (usará el wrapper robusto si está disponible)
evaluator = OllamaRAGASEvaluator(
    model_name="gemma2:27b",
    base_url="https://ollama.gti-ia.upv.es:443"
)

# Datos simples de prueba
question = "What is 2+2?"
answer = "The answer is 4."
contexts = ["Basic math: 2+2=4", "Addition facts"]
ground_truth = "4"

print("\n📊 Evaluando pregunta simple...")
print(f"Q: {question}")
print(f"A: {answer}")

try:
    metrics = evaluator.evaluate_single(
        question=question,
        answer=answer,
        contexts=contexts,
        ground_truth=ground_truth
    )

    if metrics:
        print("\n✅ ÉXITO - RAGAs funciona correctamente!")
        for metric, value in metrics.items():
            print(f"  • {metric}: {value:.3f}")
    else:
        print("\n⚠️ No se obtuvieron métricas pero no hubo crash")

except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)
print("🏁 Test completado")