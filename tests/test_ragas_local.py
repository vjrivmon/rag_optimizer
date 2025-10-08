#!/usr/bin/env python3
"""Test de RAGAs usando Ollama local"""

import sys
sys.path.insert(0, '.')

from src.evaluation.ragas_evaluator import HybridEvaluator

def test_ragas_local():
    print("🧪 Testing RAGAs con Ollama LOCAL\n")
    print("="*80)

    # Crear evaluador con Ollama local
    print("📊 Inicializando HybridEvaluator con Ollama local...")
    evaluator = HybridEvaluator(
        use_ragas=True,
        use_openai=False,
        use_ollama=True,
        ollama_model="qwen2.5:7b",
        ollama_base_url="http://localhost:11434",
        filter_thinking_tags=True
    )

    print("✅ Evaluador creado\n")

    # Test simple
    question = "¿Qué es un desayuno?"
    answer = "Un desayuno es la primera comida del día, generalmente consumida por la mañana."
    contexts = [
        "El desayuno es la comida que se realiza al inicio del día.",
        "Los desayunos típicos incluyen cereales, pan, frutas y café."
    ]
    ground_truth = "La primera comida del día"

    print(f"❓ Pregunta: {question}")
    print(f"💬 Respuesta: {answer}")
    print(f"📚 Contextos: {len(contexts)} documentos")
    print(f"\n🔄 Evaluando con RAGAs...\n")

    try:
        metrics = evaluator.evaluate(
            question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=ground_truth,
            keywords=["desayuno", "comida"]
        )

        print("✅ EVALUACIÓN EXITOSA!\n")
        print("📊 Métricas obtenidas:")
        print("="*80)
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key:25s}: {value:.3f}")
            else:
                print(f"  {key:25s}: {value}")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')

    success = test_ragas_local()
    sys.exit(0 if success else 1)
