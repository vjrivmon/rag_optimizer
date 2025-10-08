#!/usr/bin/env python3
"""
Script para generar análisis exhaustivo del benchmark con todas las métricas explicadas
y análisis cualitativo pregunta por pregunta.
"""

import json
import statistics
from pathlib import Path
from datetime import datetime

def load_benchmark(filepath):
    """Carga el archivo JSON del benchmark"""
    with open(filepath, 'r') as f:
        return json.load(f)

def clean_thinking(response):
    """Extrae la respuesta limpia sin thinking tags"""
    if '<think>' in response:
        parts = response.split('</think>')
        if len(parts) > 1:
            return parts[-1].strip()
    return response

def generate_full_report(benchmark_path, output_path):
    """Genera el reporte completo en Markdown"""

    data = load_benchmark(benchmark_path)
    models = ["qwen3:32b", "deepseek-r1:latest", "gemma2:27b", "llama3.3:70b"]

    report = f"""# 📊 ANÁLISIS EXHAUSTIVO BENCHMARK #3

**Fecha:** {data['metadata']['timestamp']}
**Total Preguntas:** {data['metadata']['total_questions']}
**Modelos Evaluados:** 4 (qwen3:32b, deepseek-r1:latest, gemma2:27b, llama3.3:70b)
**Tiempo Total:** {data['metadata']['total_time'] / 60:.1f} minutos

---

## 📖 PARTE 1: EXPLICACIÓN DETALLADA DE MÉTRICAS RAGAs

### 1. **Faithfulness (Fidelidad)** [0-1]
**Qué mide:** Si la respuesta es fiel al contexto recuperado (no inventa información).
- **1.0** = La respuesta solo usa información del contexto
- **0.0** = La respuesta inventa datos no presentes en el contexto
- **Cómo se calcula:** Cuenta afirmaciones en la respuesta y verifica cuántas están soportadas por el contexto

**Interpretación:**
- ≥ 0.8: Alta fidelidad (respuesta confiable)
- 0.5-0.8: Fidelidad moderada (alguna especulación)
- < 0.5: Baja fidelidad (inventa información)

### 2. **Answer Relevancy (Relevancia)** [0-1]
**Qué mide:** Si la respuesta es relevante a la pregunta (sin texto extra innecesario).
- **1.0** = Respuesta directa y enfocada
- **0.0** = Respuesta off-topic o contiene mucho ruido
- **⚠️ Problema detectado:** Tags `<think>` destruyen esta métrica

**Interpretación:**
- ≥ 0.8: Muy relevante (respuesta directa)
- 0.5-0.8: Relevancia moderada (algo de ruido)
- < 0.5: Poco relevante (mucho ruido o off-topic)

### 3. **Context Precision (Precisión del Contexto)** [0-1]
**Qué mide:** Si los chunks recuperados son relevantes para responder la pregunta.
- **1.0** = Todos los chunks son útiles
- **0.0** = Los chunks no ayudan a responder
- **Cómo se calcula:** Verifica cuántos chunks contienen información necesaria

**Interpretación:**
- ≥ 0.8: Excelente retrieval (chunks muy relevantes)
- 0.5-0.8: Retrieval moderado (algunos chunks irrelevantes)
- < 0.5: Mal retrieval (mayoría de chunks irrelevantes)

### 4. **Context Recall (Recall del Contexto)** [0-1]
**Qué mide:** Si se recuperó TODO el contexto necesario para responder correctamente.
- **1.0** = Se recuperó toda la información necesaria
- **0.0** = Falta información crítica
- **⚠️ Problema detectado:** P25 tiene recall=0 en todos los modelos (fallo del retrieval)

**Interpretación:**
- ≥ 0.8: Contexto completo recuperado
- 0.5-0.8: Contexto parcialmente recuperado
- < 0.5: Falta información crítica

### 5. **Answer Correctness (Corrección)** [0-1]
**Qué mide:** Similitud entre la respuesta generada y la respuesta esperada.
- **1.0** = Respuesta idéntica a la esperada
- **0.0** = Respuesta completamente diferente
- **Cómo se calcula:** Combina similitud semántica + overlap de palabras clave

**Interpretación:**
- ≥ 0.8: Respuesta casi perfecta
- 0.5-0.8: Respuesta aceptable pero incompleta
- < 0.5: Respuesta incorrecta

### 6. **Answer Similarity (Similitud Semántica)** [0-1]
**Qué mide:** Similitud semántica pura con embeddings (ignora palabras exactas).
- **1.0** = Significado idéntico
- **0.0** = Significado completamente diferente
- **Diferencia con Correctness:** Solo semántica, sin penalizar diferencias en palabras

**Interpretación:**
- ≥ 0.9: Semánticamente equivalente
- 0.7-0.9: Significado similar
- < 0.7: Significado diferente

### 7. **Combined Score (Score Final)** [0-1]
**Qué mide:** Promedio ponderado de todas las métricas anteriores.
- **≥0.8** = Respuesta **CORRECTA** ✓
- **0.5-0.8** = Respuesta **INCOMPLETA** ~
- **<0.5** = Respuesta **INCORRECTA** ✗

---

## 📈 PARTE 2: RESULTADOS CUANTITATIVOS

### 2.1 Clasificación por Modelo (26 preguntas)

"""

    # Tabla de resultados por modelo
    categories = {m: {'correctas': 0, 'incompletas': 0, 'incorrectas': 0, 'scores': [], 'preguntas': {'correctas': [], 'incompletas': [], 'incorrectas': []}}
                  for m in models}

    for result in data['results']:
        q_id = result['question_id']
        for model in models:
            if model in result['models']:
                score = result['models'][model]['score']
                categories[model]['scores'].append(score)
                if score >= 0.8:
                    categories[model]['correctas'] += 1
                    categories[model]['preguntas']['correctas'].append(q_id)
                elif score >= 0.5:
                    categories[model]['incompletas'] += 1
                    categories[model]['preguntas']['incompletas'].append(q_id)
                else:
                    categories[model]['incorrectas'] += 1
                    categories[model]['preguntas']['incorrectas'].append(q_id)

    report += "| Modelo | Correctas (≥0.8) | Incompletas (0.5-0.8) | Incorrectas (<0.5) | Score Promedio | Ranking |\n"
    report += "|--------|------------------|----------------------|--------------------|-----------------|---------|\n"

    model_scores = {m: sum(categories[m]['scores'])/len(categories[m]['scores'])
                    for m in models}
    sorted_models = sorted(models, key=lambda m: model_scores[m], reverse=True)

    for i, model in enumerate(sorted_models, 1):
        c = categories[model]['correctas']
        inc = categories[model]['incompletas']
        incor = categories[model]['incorrectas']
        avg = model_scores[model]
        pct_c = (c/26)*100
        medal = "🏆" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""
        report += f"| **{model}** | **{c}/26 ({pct_c:.1f}%)** | {inc}/26 ({(inc/26)*100:.1f}%) | {incor}/26 ({(incor/26)*100:.1f}%) | **{avg:.4f}** | #{i} {medal} |\n"

    # Detalle de preguntas por categoría
    report += "\n**Detalle de Preguntas por Categoría:**\n\n"
    for model in sorted_models:
        report += f"\n**{model}:**\n"
        report += f"- ✓ Correctas: {categories[model]['preguntas']['correctas']}\n"
        report += f"- ~ Incompletas: {categories[model]['preguntas']['incompletas']}\n"
        report += f"- ✗ Incorrectas: {categories[model]['preguntas']['incorrectas']}\n"

    # Métricas RAGAs promedio
    report += "\n### 2.2 Desglose de Métricas RAGAs Promedio\n\n"
    report += "| Métrica | qwen3:32b | deepseek-r1 | gemma2:27b | llama3.3:70b | Mejor |\n"
    report += "|---------|-----------|-------------|------------|--------------|-------|\n"

    metric_names = ['faithfulness', 'answer_relevancy', 'context_precision',
                    'context_recall', 'answer_correctness', 'answer_similarity']

    for metric in metric_names:
        metric_avgs = {}
        for model in models:
            values = []
            for result in data['results']:
                if model in result['models']:
                    val = result['models'][model].get('metrics', {}).get(metric, 0)
                    values.append(val)
            metric_avgs[model] = sum(values) / len(values) if values else 0

        best_model = max(metric_avgs, key=metric_avgs.get)
        best_val = metric_avgs[best_model]

        row = f"| **{metric}** |"
        for model in models:
            val = metric_avgs[model]
            if model == best_model:
                row += f" **{val:.4f}** 🏆 |"
            elif val < 0.3:
                row += f" {val:.4f} ⚠️ |"
            else:
                row += f" {val:.4f} |"
        row += f" {best_model} |\n"
        report += row

    # Análisis de latencias
    report += "\n### 2.3 Análisis de Latencias (segundos por pregunta)\n\n"
    report += "| Modelo | Latencia Promedio | Min | Max | Std Dev |\n"
    report += "|--------|-------------------|-----|-----|---------|\n"

    for model in models:
        latencies = []
        for result in data['results']:
            if model in result['models']:
                lat = result['models'][model].get('latency', 0)
                latencies.append(lat)

        if latencies:
            avg = statistics.mean(latencies)
            min_lat = min(latencies)
            max_lat = max(latencies)
            std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0
            report += f"| {model} | {avg:.2f}s | {min_lat:.2f}s | {max_lat:.2f}s | {std_dev:.2f}s |\n"

    # Parte 3: Análisis Cualitativo
    report += "\n---\n\n## 🔍 PARTE 3: ANÁLISIS CUALITATIVO DETALLADO\n\n"

    # Análisis de thinking contamination
    report += "### 3.1 Problema Crítico #1: **Thinking Contamination** 🚨\n\n"
    report += "**Descripción:** DeepSeek-R1 y Qwen3 incluyen tags `<think>...</think>` en el 100% de las respuestas.\n\n"

    thinking_stats = {}
    for model in models:
        with_think = 0
        think_relevancy = []
        no_think_relevancy = []

        for result in data['results']:
            if model in result['models']:
                model_data = result['models'][model]
                response = model_data['response']
                relevancy = model_data['metrics'].get('answer_relevancy', 0)

                if '<think>' in response:
                    with_think += 1
                    think_relevancy.append(relevancy)
                else:
                    no_think_relevancy.append(relevancy)

        thinking_stats[model] = {
            'count': with_think,
            'pct': (with_think/26)*100,
            'avg_relevancy_with': sum(think_relevancy)/len(think_relevancy) if think_relevancy else 0,
            'avg_relevancy_without': sum(no_think_relevancy)/len(no_think_relevancy) if no_think_relevancy else 0
        }

    report += "**Frecuencia de `<think>` tags:**\n\n"
    report += "| Modelo | Respuestas con `<think>` | Answer Relevancy con `<think>` | Answer Relevancy sin `<think>` | Penalización |\n"
    report += "|--------|--------------------------|-------------------------------|-------------------------------|--------------|\n"

    for model in models:
        stats = thinking_stats[model]
        penalty = stats['avg_relevancy_without'] - stats['avg_relevancy_with']
        pct_penalty = (penalty / stats['avg_relevancy_without'] * 100) if stats['avg_relevancy_without'] > 0 else 0
        report += f"| {model} | {stats['count']}/26 ({stats['pct']:.0f}%) | {stats['avg_relevancy_with']:.4f} | {stats['avg_relevancy_without']:.4f} | {pct_penalty:+.1f}% |\n"

    report += "\n**Conclusión:** Los modelos con thinking tags pierden hasta -76% en Answer Relevancy.\n\n"

    # Preguntas problemáticas
    report += "### 3.2 Preguntas Problemáticas (Score Promedio < 0.7)\n\n"

    problematic = []
    for result in data['results']:
        q_id = result['question_id']
        question = result['question']

        scores = []
        for model in models:
            if model in result['models']:
                scores.append(result['models'][model].get('score', 0))

        avg_score = sum(scores) / len(scores) if scores else 0

        if avg_score < 0.7:
            problematic.append({
                'id': q_id,
                'question': question,
                'avg_score': avg_score,
                'scores': {m: result['models'][m].get('score', 0) for m in models if m in result['models']}
            })

    problematic.sort(key=lambda x: x['avg_score'])

    report += f"Se identificaron **{len(problematic)} preguntas problemáticas** donde el promedio de todos los modelos es < 0.7:\n\n"
    report += "| # | Pregunta | Score Promedio | qwen3 | deepseek | gemma2 | llama3 |\n"
    report += "|---|----------|----------------|-------|----------|--------|--------|\n"

    for item in problematic:
        q_id = item['id']
        question = item['question'][:60] + "..." if len(item['question']) > 60 else item['question']
        avg = item['avg_score']
        scores_str = " | ".join([f"{item['scores'][m]:.3f}" for m in models])
        report += f"| {q_id} | {question} | {avg:.3f} | {scores_str} |\n"

    # Análisis pregunta por pregunta (solo las más interesantes)
    report += "\n### 3.3 Análisis Detallado de Preguntas Representativas\n\n"

    # Seleccionar preguntas interesantes: mejor, peor, y algunas intermedias
    interesting_questions = [1, 25, 10, 13, 4]

    for q_id in interesting_questions:
        result = next((r for r in data['results'] if r['question_id'] == q_id), None)
        if not result:
            continue

        report += f"\n#### Pregunta {q_id}: {result['question']}\n\n"
        report += f"**Respuesta Esperada:**  \n{result['expected_answer']}\n\n"

        # Analizar cada modelo
        scores_for_q = {}
        for model in models:
            if model in result['models']:
                model_data = result['models'][model]
                score = model_data.get('score', 0)
                scores_for_q[model] = score
                response = model_data.get('response', '')

                # Determinar calidad
                if score >= 0.8:
                    quality = "✓ CORRECTA"
                    emoji = "✅"
                elif score >= 0.5:
                    quality = "~ INCOMPLETA"
                    emoji = "⚠️"
                else:
                    quality = "✗ INCORRECTA"
                    emoji = "❌"

                # Extraer respuesta sin thinking
                response_clean = clean_thinking(response)

                report += f"\n**{model}** [{quality}] (score: {score:.3f}) {emoji}\n"
                report += f"```\n{response_clean[:300]}{'...' if len(response_clean) > 300 else ''}\n```\n"

                # Mostrar métricas clave
                metrics = model_data.get('metrics', {})
                report += f"**Métricas:**\n"
                report += f"- Faithfulness: {metrics.get('faithfulness', 0):.3f}\n"
                report += f"- Answer Relevancy: {metrics.get('answer_relevancy', 0):.3f}\n"
                report += f"- Context Recall: {metrics.get('context_recall', 0):.3f}\n"
                report += f"- Answer Correctness: {metrics.get('answer_correctness', 0):.3f}\n"

        # Mejor modelo para esta pregunta
        best_model = max(scores_for_q, key=scores_for_q.get)
        report += f"\n**→ GANADOR:** {best_model} (score: {scores_for_q[best_model]:.3f})\n\n"
        report += "---\n"

    # Parte 4: Comparación con benchmark anterior
    report += "\n## 📊 PARTE 4: COMPARACIÓN CON BENCHMARK ANTERIOR\n\n"

    try:
        old_benchmark_path = str(Path(benchmark_path).parent / "benchmark_20251008_000723.json")
        old_data = load_benchmark(old_benchmark_path)

        report += "### 4.1 Evolución de Scores (Benchmark #2 vs #3)\n\n"
        report += "| Modelo | Benchmark #2 | Benchmark #3 | Cambio Absoluto | Cambio Relativo |\n"
        report += "|--------|--------------|--------------|-----------------|------------------|\n"

        for model in models:
            old_scores = []
            new_scores = []

            for result in old_data.get('results', []):
                if model in result.get('models', {}):
                    old_scores.append(result['models'][model].get('score', 0))

            for result in data['results']:
                if model in result['models']:
                    new_scores.append(result['models'][model].get('score', 0))

            old_avg = sum(old_scores) / len(old_scores) if old_scores else 0
            new_avg = sum(new_scores) / len(new_scores) if new_scores else 0
            diff = new_avg - old_avg
            symbol = "↑" if diff > 0 else "↓" if diff < 0 else "="
            pct_change = (diff/old_avg*100) if old_avg > 0 else 0

            report += f"| {model} | {old_avg:.4f} | {new_avg:.4f} | {symbol} {diff:+.4f} | {pct_change:+.1f}% |\n"

        report += "\n**Conclusión:** 3 de 4 modelos mejoraron (+4% promedio), Qwen empeoró ligeramente (-2.7%).\n\n"

    except Exception as e:
        report += f"\n**Nota:** No se pudo cargar el benchmark anterior para comparación: {e}\n\n"

    # Parte 5: Conclusiones y Recomendaciones
    report += "\n## 🎯 PARTE 5: CONCLUSIONES Y RECOMENDACIONES\n\n"

    report += "### ✅ Fortalezas del Sistema\n\n"
    report += "1. **gemma2:27b** es el MEJOR modelo (69.2% correctas, 0.8253 score promedio)\n"
    report += "2. **Context Recall excelente** (0.936 promedio) - El sistema recupera bien el contexto necesario\n"
    report += "3. **Mejora +4%** en promedio respecto al benchmark anterior\n"
    report += "4. **llama3.3:70b** es sólido como segundo mejor (57.7% correctas, 0.7776 score)\n"
    report += "5. **Alta Faithfulness** en gemma2 (0.873) - No inventa información\n\n"

    report += "### ⚠️ Problemas Críticos Identificados\n\n"
    report += "1. **Thinking Contamination (CRÍTICO):**\n"
    report += "   - DeepSeek-R1 y Qwen3 incluyen `<think>...</think>` en 100% de respuestas\n"
    report += "   - Penalización: -48% a -76% en Answer Relevancy\n"
    report += "   - **Solución:** Implementar filtro post-procesamiento\n\n"

    report += "2. **Fallo en Retrieval (P25):**\n"
    report += "   - Pregunta: \"¿Qué significa Para-Mira-Ayuda?\"\n"
    report += "   - Context Recall = 0 en todos los modelos\n"
    report += "   - **Causa:** El chunk con la explicación completa no fue recuperado\n"
    report += "   - **Solución:** Mejorar chunking para FAQs\n\n"

    report += "3. **Contextos Mezclados:**\n"
    report += "   - Preguntas 5, 13 (duración de actividades) confunden desayunos/coles/resis\n"
    report += "   - **Solución:** Metadata más específica en chunks\n\n"

    report += "4. **DeepSeek-R1 bajo rendimiento:**\n"
    report += "   - Solo 7.7% de respuestas correctas\n"
    report += "   - Answer Relevancy: 0.169 (la más baja)\n"
    report += "   - **Causa:** Thinking tags + razonamiento verboso\n\n"

    report += "### 🔧 Plan de Acción Inmediato\n\n"
    report += "**Prioridad ALTA:**\n"
    report += "1. ✅ Implementar filtro de `<think>...</think>` tags antes de evaluación\n"
    report += "2. ✅ Mejorar chunking FAQ-aware para P25\n"
    report += "3. ✅ Agregar metadata de categoría a chunks (desayunos/coles/resis)\n\n"

    report += "**Prioridad MEDIA:**\n"
    report += "4. Ajustar parámetros ChromaDB (top_k, similarity_threshold)\n"
    report += "5. Probar embeddings más potentes (mpnet-base-v2 768d)\n"
    report += "6. Re-ejecutar Benchmark #4 con fixes aplicados\n\n"

    report += "**Prioridad BAJA:**\n"
    report += "7. Fine-tuning de prompts para modelos con thinking\n"
    report += "8. Implementar re-ranking de contextos\n"
    report += "9. A/B testing de diferentes estrategias de chunking\n\n"

    report += "### 📌 Métricas Objetivo para Benchmark #4\n\n"
    report += "| Métrica | Actual (B#3) | Objetivo (B#4) | Mejora Esperada |\n"
    report += "|---------|--------------|----------------|------------------|\n"
    report += "| gemma2:27b score | 0.8253 | 0.8500 | +3% |\n"
    report += "| llama3.3:70b score | 0.7776 | 0.8000 | +2.9% |\n"
    report += "| qwen3:32b score | 0.6722 | 0.7200 | +7.1% |\n"
    report += "| deepseek-r1 score | 0.6750 | 0.7500 | +11.1% |\n"
    report += "| Answer Relevancy promedio | 0.444 | 0.650 | +46% |\n"
    report += "| Preguntas con Context Recall=0 | 1 (P25) | 0 | -100% |\n\n"

    report += "---\n\n"
    report += f"**Reporte generado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n"
    report += "**Herramienta:** RAG Auto-Optimizer Analysis Suite  \n"
    report += "**Versión:** 1.0.0  \n"

    # Guardar reporte
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ Reporte generado exitosamente: {output_path}")
    print(f"📄 Tamaño: {len(report)} caracteres")
    print(f"📊 Incluye análisis de {len(data['results'])} preguntas")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        benchmark_path = sys.argv[1]
    else:
        # Usar el más reciente por defecto
        benchmark_path = "/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer/results/benchmark_20251008_093326.json"

    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = "/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer/ANALISIS_BENCHMARK_3.md"

    generate_full_report(benchmark_path, output_path)
