import json

# Cargar ambos benchmarks
with open('results/benchmark_20251008_093326.json') as f:
    openai_bench = json.load(f)

with open('results/benchmark_20251008_205337.json') as f:
    dual_bench = json.load(f)

print("="*80)
print("COMPARATIVA: OpenAI-only vs Dual Backend")
print("="*80)

print(f"\n📊 CONFIGURACIÓN:")
print(f"   OpenAI-only (benchmark anterior):")
print(f"      Backend: {openai_bench['metadata'].get('ragas_backend', 'openai (por defecto)')}")
print(f"      Tiempo total: {openai_bench['metadata']['total_time']/3600:.2f} horas")
print(f"\n   Dual (benchmark actual):")
print(f"      Backend: {dual_bench['metadata']['ragas_backend']}")
print(f"      Tiempo total: {dual_bench['metadata']['total_time']/3600:.2f} horas")

# Analizar primera pregunta como ejemplo
q1_openai = openai_bench['results'][0]
q1_dual = dual_bench['results'][0]

print(f"\n{'='*80}")
print(f"ANÁLISIS DETALLADO - Pregunta 1: {q1_openai['question']}")
print(f"{'='*80}")

models = ['qwen3:32b', 'deepseek-r1:latest', 'gemma2:27b', 'llama3.3:70b']

for model in models:
    print(f"\n📌 {model}:")
    openai_metrics = q1_openai['models'][model]['metrics']
    dual_metrics = q1_dual['models'][model]['metrics']
    
    print(f"   Score combinado:")
    print(f"      OpenAI-only: {openai_metrics['combined_score']:.4f}")
    print(f"      Dual:        {dual_metrics['combined_score']:.4f}")
    diff = ((dual_metrics['combined_score'] - openai_metrics['combined_score']) / openai_metrics['combined_score']) * 100
    print(f"      Diferencia:  {diff:+.2f}%")
    
    print(f"\n   Métricas RAGAs individuales:")
    ragas_metrics = ['faithfulness', 'answer_relevancy', 'context_precision', 
                     'context_recall', 'answer_correctness', 'answer_similarity']
    
    for metric in ragas_metrics:
        openai_val = openai_metrics.get(metric, 0)
        dual_val = dual_metrics.get(metric, 0)
        if openai_val > 0:
            diff_pct = ((dual_val - openai_val) / openai_val) * 100
            symbol = "📈" if diff_pct > 0 else "📉" if diff_pct < 0 else "➡️"
            print(f"      {metric:20s}: {openai_val:.4f} → {dual_val:.4f} ({diff_pct:+.1f}%) {symbol}")
        else:
            print(f"      {metric:20s}: N/A")

# Estadísticas generales
print(f"\n{'='*80}")
print(f"ESTADÍSTICAS GLOBALES (26 preguntas)")
print(f"{'='*80}")

for model in models:
    print(f"\n📊 {model}:")
    
    openai_scores = []
    dual_scores = []
    
    for result in openai_bench['results']:
        if model in result['models']:
            openai_scores.append(result['models'][model]['score'])
    
    for result in dual_bench['results']:
        if model in result['models']:
            dual_scores.append(result['models'][model]['score'])
    
    openai_avg = sum(openai_scores) / len(openai_scores) if openai_scores else 0
    dual_avg = sum(dual_scores) / len(dual_scores) if dual_scores else 0
    
    diff = ((dual_avg - openai_avg) / openai_avg) * 100 if openai_avg > 0 else 0
    
    print(f"   Score promedio:")
    print(f"      OpenAI-only: {openai_avg:.4f}")
    print(f"      Dual:        {dual_avg:.4f}")
    print(f"      Diferencia:  {diff:+.2f}%")
    
    if abs(diff) < 5:
        print(f"      ✅ Diferencia aceptable (<5%)")
    else:
        print(f"      ⚠️  Diferencia significativa (>5%)")

print(f"\n{'='*80}")
print(f"🎯 CONCLUSIÓN")
print(f"{'='*80}")

# Verificar si hay 6 métricas en dual
sample_dual_metrics = dual_bench['results'][0]['models']['gemma2:27b']['metrics']
ragas_count = len([k for k in sample_dual_metrics if k in ragas_metrics])

print(f"\n✅ Dual backend tiene {ragas_count}/6 métricas RAGAs")

if ragas_count == 6:
    print(f"✅ Todas las métricas RAGAs se calcularon correctamente")
else:
    print(f"⚠️  Faltan {6-ragas_count} métricas RAGAs")

# Verificar consistencia
consistency_ok = True
for model in models:
    openai_avg = sum([r['models'][model]['score'] for r in openai_bench['results']]) / 26
    dual_avg = sum([r['models'][model]['score'] for r in dual_bench['results']]) / 26
    diff = abs(((dual_avg - openai_avg) / openai_avg) * 100)
    
    if diff > 10:
        consistency_ok = False
        print(f"⚠️  {model}: diferencia {diff:.1f}% (>10%) - inconsistencia alta")

if consistency_ok:
    print(f"\n✅ Scores consistentes entre backends (<10% diferencia)")
    print(f"\n💡 RECOMENDACIÓN: Cambiar a Ollama-only (gratis) es seguro")
else:
    print(f"\n⚠️  Inconsistencia detectada entre evaluadores")
    print(f"\n💡 RECOMENDACIÓN: Mantener OpenAI-only o investigar diferencias")

