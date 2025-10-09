#!/usr/bin/env python3
"""
Test rápido para verificar que el fix de RAGAs funciona
"""

import sys
sys.path.insert(0, '/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')

from src.evaluation.ragas_evaluator import OllamaRAGASEvaluator

def test_ragas_fix():
    """Prueba la evaluación con Ollama para verificar el fix"""

    print("🧪 Testing RAGAs fix...")
    print("-" * 50)

    # Inicializar evaluador con Ollama
    evaluator = OllamaRAGASEvaluator(
        model_name="gemma2:27b",
        base_url="https://ollama.gti-ia.upv.es:443",
        filter_thinking_tags=True
    )

    # Datos de prueba
    question = "¿Qué se hace en la actividad de desayunos?"
    answer = """En la actividad de desayunos solidarios, se distribuyen alimentos y productos
    de primera necesidad a personas en situación vulnerable. Los voluntarios se dividen en
    grupos y recorren rutas establecidas, entregando desayunos que incluyen productos como
    napolitanas valencianas, leche semidesnatada, café y azúcar."""

    contexts = [
        "La actividad de desayunos consiste en repartir comida a personas sin hogar.",
        "Los voluntarios se reúnen los sábados por la mañana para preparar los desayunos.",
        "Es importante el tiempo que se comparte con las personas, no solo la comida."
    ]

    ground_truth = """La actividad consiste en que un grupo de voluntarios se reúne en un punto
    de encuentro, se dividen en equipos, y cada uno recorre una zona de Valencia repartiendo
    desayunos o cenas a personas sin hogar. Lo más importante no es la comida, sino el tiempo
    que se comparte con ellas (conversación, compañía)."""

    # Evaluar
    print("📊 Evaluando con RAGAs + Ollama...")
    print(f"   Modelo: gemma2:27b")
    print(f"   URL: https://ollama.gti-ia.upv.es:443")

    metrics = evaluator.evaluate_single(
        question=question,
        answer=answer,
        contexts=contexts,
        ground_truth=ground_truth
    )

    if metrics:
        print("✅ Evaluación completada exitosamente!")
        print("\n📈 Métricas obtenidas:")
        for metric, value in metrics.items():
            print(f"   • {metric}: {value:.3f}")
    else:
        print("⚠️  No se obtuvieron métricas (pero no hubo crash)")

    print("-" * 50)
    print("✅ Test completado sin errores fatales")
    return True


if __name__ == "__main__":
    success = test_ragas_fix()
    sys.exit(0 if success else 1)