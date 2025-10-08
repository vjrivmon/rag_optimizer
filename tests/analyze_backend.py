import json

# Benchmark anterior (supuestamente ollama backend)
with open('results/benchmark_20251008_093326.json') as f:
    prev = json.load(f)

# Verificar qué métricas RAGAs tiene el primer resultado
first_result = prev['results'][0]
gemma_metrics = first_result['models']['gemma2:27b']['metrics']

print("=== BENCHMARK 20251008_093326 ===")
print(f"Backend configurado: {prev['metadata'].get('ragas_backend', 'NO REGISTRADO')}")
print(f"\nMétricas RAGAs de gemma2:27b pregunta 1:")

ragas_metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 
                 'context_recall', 'answer_correctness', 'answer_similarity']

for metric in ragas_metrics:
    if metric in gemma_metrics:
        print(f"  ✅ {metric}: {gemma_metrics[metric]:.4f}")
    else:
        print(f"  ❌ {metric}: FALTA")

print(f"\nCombined score: {gemma_metrics['combined_score']:.4f}")

# Si tiene las 6 métricas, debió usar OpenAI
if all(m in gemma_metrics for m in ragas_metrics):
    print("\n🔍 Conclusión: Este benchmark usó OpenAI (6 métricas completas)")
else:
    print("\n🔍 Conclusión: Este benchmark usó Ollama (solo 3 métricas)")
