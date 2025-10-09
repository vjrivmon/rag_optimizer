#!/usr/bin/env python3
"""
Test para verificar que OllamaRAGASEvaluator funciona con metrics_subset
"""

import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')

from src.evaluation.ragas_evaluator import OllamaRAGASEvaluator

print("🧪 TEST EVALUADOR CON METRICS_SUBSET")
print("=" * 60)

# Test 1: Modo fast (2 métricas)
print("\n📊 Test 1: Modo FAST (2 métricas)")
try:
    evaluator_fast = OllamaRAGASEvaluator(
        model_name="gemma2:27b",
        base_url="https://ollama.gti-ia.upv.es:443",
        filter_thinking_tags=True,
        metrics_subset=['faithfulness', 'answer_similarity']
    )
    print(f"   ✓ Evaluador creado")
    print(f"   ✓ Métricas configuradas: {len(evaluator_fast.metrics)}")
    print(f"   ✓ Atributo 'metrics' existe: {hasattr(evaluator_fast, 'metrics')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Modo normal (4 métricas)
print("\n📊 Test 2: Modo NORMAL (4 métricas)")
try:
    evaluator_normal = OllamaRAGASEvaluator(
        model_name="gemma2:27b",
        base_url="https://ollama.gti-ia.upv.es:443",
        filter_thinking_tags=True,
        metrics_subset=['faithfulness', 'answer_relevancy', 'context_recall', 'answer_similarity']
    )
    print(f"   ✓ Evaluador creado")
    print(f"   ✓ Métricas configuradas: {len(evaluator_normal.metrics)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Modo full (todas las métricas)
print("\n📊 Test 3: Modo FULL (todas las métricas)")
try:
    evaluator_full = OllamaRAGASEvaluator(
        model_name="gemma2:27b",
        base_url="https://ollama.gti-ia.upv.es:443",
        filter_thinking_tags=True,
        metrics_subset=None  # None = todas las métricas
    )
    print(f"   ✓ Evaluador creado")
    print(f"   ✓ Métricas configuradas: {len(evaluator_full.metrics)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Evaluar algo real con modo fast
print("\n📊 Test 4: Evaluación real con modo FAST")
try:
    question = "¿Qué es Python?"
    answer = "Python es un lenguaje de programación."
    contexts = ["Python es un lenguaje interpretado", "Python fue creado por Guido van Rossum"]
    ground_truth = "Python es un lenguaje de programación interpretado."

    print(f"   Evaluando pregunta de prueba...")
    metrics = evaluator_fast.evaluate_single(
        question=question,
        answer=answer,
        contexts=contexts,
        ground_truth=ground_truth
    )

    if metrics:
        print(f"   ✓ Evaluación exitosa!")
        for metric, value in metrics.items():
            if value is not None and str(value) != 'nan':
                print(f"      • {metric}: {value:.3f}")
    else:
        print(f"   ⚠️ No se obtuvieron métricas")

except Exception as e:
    print(f"   ❌ Error en evaluación: {e}")

print("\n" + "=" * 60)
print("🏁 TEST COMPLETADO")