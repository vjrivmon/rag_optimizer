#!/usr/bin/env python3
"""
Script para exportar análisis detallado del benchmark a CSV
Genera múltiples archivos CSV con diferentes vistas de los datos.
"""

import json
import csv
from pathlib import Path

def clean_thinking(response):
    """Extrae la respuesta limpia sin thinking tags"""
    if '<think>' in response:
        parts = response.split('</think>')
        if len(parts) > 1:
            return parts[-1].strip()
    return response

def export_to_csv(benchmark_path, output_dir):
    """Exporta el benchmark a múltiples archivos CSV"""

    with open(benchmark_path, 'r') as f:
        data = json.load(f)

    models = ["qwen3:32b", "deepseek-r1:latest", "gemma2:27b", "llama3.3:70b"]
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # CSV 1: Resumen por modelo
    csv_summary = output_dir / "01_resumen_por_modelo.csv"
    with open(csv_summary, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Modelo', 'Score Promedio', 'Correctas (≥0.8)', 'Incompletas (0.5-0.8)',
                        'Incorrectas (<0.5)', 'Faithfulness', 'Answer Relevancy', 'Context Precision',
                        'Context Recall', 'Answer Correctness', 'Answer Similarity',
                        'Latencia Promedio (s)', 'Respuestas con <think>'])

        for model in models:
            scores = []
            correctas = 0
            incompletas = 0
            incorrectas = 0
            latencias = []
            with_thinking = 0

            metrics_sum = {
                'faithfulness': [],
                'answer_relevancy': [],
                'context_precision': [],
                'context_recall': [],
                'answer_correctness': [],
                'answer_similarity': []
            }

            for result in data['results']:
                if model in result['models']:
                    model_data = result['models'][model]
                    score = model_data['score']
                    scores.append(score)
                    latencias.append(model_data.get('latency', 0))

                    if '<think>' in model_data['response']:
                        with_thinking += 1

                    if score >= 0.8:
                        correctas += 1
                    elif score >= 0.5:
                        incompletas += 1
                    else:
                        incorrectas += 1

                    for metric in metrics_sum:
                        metrics_sum[metric].append(model_data['metrics'].get(metric, 0))

            avg_score = sum(scores) / len(scores)
            avg_latency = sum(latencias) / len(latencias)
            avg_metrics = {k: sum(v)/len(v) for k, v in metrics_sum.items()}

            writer.writerow([
                model,
                f"{avg_score:.4f}",
                f"{correctas}/26",
                f"{incompletas}/26",
                f"{incorrectas}/26",
                f"{avg_metrics['faithfulness']:.4f}",
                f"{avg_metrics['answer_relevancy']:.4f}",
                f"{avg_metrics['context_precision']:.4f}",
                f"{avg_metrics['context_recall']:.4f}",
                f"{avg_metrics['answer_correctness']:.4f}",
                f"{avg_metrics['answer_similarity']:.4f}",
                f"{avg_latency:.2f}",
                f"{with_thinking}/26"
            ])

    print(f"✅ Generado: {csv_summary}")

    # CSV 2: Detalle por pregunta
    csv_questions = output_dir / "02_detalle_por_pregunta.csv"
    with open(csv_questions, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Pregunta', 'Respuesta Esperada',
                        'qwen3_score', 'qwen3_calidad',
                        'deepseek_score', 'deepseek_calidad',
                        'gemma2_score', 'gemma2_calidad',
                        'llama3_score', 'llama3_calidad',
                        'Score Promedio', 'Ganador', 'Contexts Recuperados'])

        for result in data['results']:
            q_id = result['question_id']
            question = result['question']
            expected = result['expected_answer']
            contexts_count = len(result.get('contexts', []))

            row = [q_id, question, expected]
            scores = []

            for model in models:
                if model in result['models']:
                    score = result['models'][model]['score']
                    scores.append(score)

                    if score >= 0.8:
                        quality = "CORRECTA"
                    elif score >= 0.5:
                        quality = "INCOMPLETA"
                    else:
                        quality = "INCORRECTA"

                    row.extend([f"{score:.3f}", quality])
                else:
                    row.extend(['', ''])

            avg_score = sum(scores) / len(scores) if scores else 0
            best_model = max(models, key=lambda m: result['models'][m]['score'] if m in result['models'] else 0)

            row.extend([f"{avg_score:.3f}", best_model, contexts_count])
            writer.writerow(row)

    print(f"✅ Generado: {csv_questions}")

    # CSV 3: Métricas detalladas por pregunta y modelo
    csv_metrics = output_dir / "03_metricas_detalladas.csv"
    with open(csv_metrics, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Pregunta', 'Modelo', 'Score', 'Faithfulness', 'Answer Relevancy',
                        'Context Precision', 'Context Recall', 'Answer Correctness',
                        'Answer Similarity', 'Latencia (s)', 'Tiene <think>'])

        for result in data['results']:
            q_id = result['question_id']
            question = result['question']

            for model in models:
                if model in result['models']:
                    model_data = result['models'][model]
                    metrics = model_data['metrics']
                    has_thinking = "Sí" if '<think>' in model_data['response'] else "No"

                    writer.writerow([
                        q_id,
                        question,
                        model,
                        f"{model_data['score']:.4f}",
                        f"{metrics.get('faithfulness', 0):.4f}",
                        f"{metrics.get('answer_relevancy', 0):.4f}",
                        f"{metrics.get('context_precision', 0):.4f}",
                        f"{metrics.get('context_recall', 0):.4f}",
                        f"{metrics.get('answer_correctness', 0):.4f}",
                        f"{metrics.get('answer_similarity', 0):.4f}",
                        f"{model_data.get('latency', 0):.2f}",
                        has_thinking
                    ])

    print(f"✅ Generado: {csv_metrics}")

    # CSV 4: Respuestas completas
    csv_responses = output_dir / "04_respuestas_completas.csv"
    with open(csv_responses, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Pregunta', 'Respuesta Esperada', 'Modelo', 'Score',
                        'Respuesta Generada', 'Respuesta Limpia (sin <think>)'])

        for result in data['results']:
            q_id = result['question_id']
            question = result['question']
            expected = result['expected_answer']

            for model in models:
                if model in result['models']:
                    model_data = result['models'][model]
                    response = model_data['response']
                    response_clean = clean_thinking(response)

                    writer.writerow([
                        q_id,
                        question,
                        expected,
                        model,
                        f"{model_data['score']:.4f}",
                        response,
                        response_clean
                    ])

    print(f"✅ Generado: {csv_responses}")

    # CSV 5: Preguntas problemáticas
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
                'expected': result['expected_answer'],
                'avg_score': avg_score,
                'scores': {m: result['models'][m].get('score', 0) for m in models if m in result['models']},
                'context_recalls': {m: result['models'][m]['metrics'].get('context_recall', 0)
                                   for m in models if m in result['models']}
            })

    problematic.sort(key=lambda x: x['avg_score'])

    csv_problematic = output_dir / "05_preguntas_problematicas.csv"
    with open(csv_problematic, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Ranking', 'ID', 'Pregunta', 'Respuesta Esperada', 'Score Promedio',
                        'qwen3_score', 'deepseek_score', 'gemma2_score', 'llama3_score',
                        'qwen3_recall', 'deepseek_recall', 'gemma2_recall', 'llama3_recall',
                        'Tipo de Problema'])

        for i, item in enumerate(problematic, 1):
            # Determinar tipo de problema
            avg_recall = sum(item['context_recalls'].values()) / len(item['context_recalls'])
            if avg_recall < 0.3:
                problem_type = "Fallo en Retrieval"
            elif avg_recall >= 0.8:
                problem_type = "Fallo en Generación"
            else:
                problem_type = "Retrieval Parcial"

            writer.writerow([
                i,
                item['id'],
                item['question'],
                item['expected'],
                f"{item['avg_score']:.3f}",
                f"{item['scores']['qwen3:32b']:.3f}",
                f"{item['scores']['deepseek-r1:latest']:.3f}",
                f"{item['scores']['gemma2:27b']:.3f}",
                f"{item['scores']['llama3.3:70b']:.3f}",
                f"{item['context_recalls']['qwen3:32b']:.3f}",
                f"{item['context_recalls']['deepseek-r1:latest']:.3f}",
                f"{item['context_recalls']['gemma2:27b']:.3f}",
                f"{item['context_recalls']['llama3.3:70b']:.3f}",
                problem_type
            ])

    print(f"✅ Generado: {csv_problematic}")

    # CSV 6: Thinking contamination analysis
    csv_thinking = output_dir / "06_analisis_thinking_tags.csv"
    with open(csv_thinking, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Modelo', 'Total Respuestas', 'Con <think>', '% con <think>',
                        'Avg Relevancy Con <think>', 'Avg Relevancy Sin <think>',
                        'Penalización', '% Penalización'])

        for model in models:
            with_think_count = 0
            with_think_relevancy = []
            without_think_relevancy = []

            for result in data['results']:
                if model in result['models']:
                    model_data = result['models'][model]
                    response = model_data['response']
                    relevancy = model_data['metrics'].get('answer_relevancy', 0)

                    if '<think>' in response:
                        with_think_count += 1
                        with_think_relevancy.append(relevancy)
                    else:
                        without_think_relevancy.append(relevancy)

            total = with_think_count + len(without_think_relevancy)
            pct_with = (with_think_count / total * 100) if total > 0 else 0

            avg_with = sum(with_think_relevancy) / len(with_think_relevancy) if with_think_relevancy else 0
            avg_without = sum(without_think_relevancy) / len(without_think_relevancy) if without_think_relevancy else 0
            penalty = avg_without - avg_with
            pct_penalty = (penalty / avg_without * 100) if avg_without > 0 else 0

            writer.writerow([
                model,
                total,
                with_think_count,
                f"{pct_with:.1f}%",
                f"{avg_with:.4f}",
                f"{avg_without:.4f}",
                f"{penalty:.4f}",
                f"{pct_penalty:.1f}%"
            ])

    print(f"✅ Generado: {csv_thinking}")

    print(f"\n🎉 Exportación completa! 6 archivos CSV generados en: {output_dir}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        benchmark_path = sys.argv[1]
    else:
        benchmark_path = "/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer/results/benchmark_20251008_093326.json"

    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = "/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer/results/csv_analysis"

    export_to_csv(benchmark_path, output_dir)
