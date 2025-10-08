#!/usr/bin/env python3
"""
Script para generar visualizaciones del benchmark usando Matplotlib
"""

import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Para generar sin display
import numpy as np
from pathlib import Path

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

def load_benchmark(filepath):
    """Carga el archivo JSON del benchmark"""
    with open(filepath, 'r') as f:
        return json.load(f)

def generate_visualizations(benchmark_path, output_dir):
    """Genera todas las visualizaciones"""

    data = load_benchmark(benchmark_path)
    models = ["qwen3:32b", "deepseek-r1:latest", "gemma2:27b", "llama3.3:70b"]
    model_labels = ["Qwen3", "DeepSeek-R1", "Gemma2", "Llama3.3"]

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Colores para cada modelo
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']

    # ========== Gráfico 1: Distribución de scores por modelo ==========
    fig, ax = plt.subplots(figsize=(12, 6))

    model_scores = {m: [] for m in models}
    for result in data['results']:
        for model in models:
            if model in result['models']:
                model_scores[model].append(result['models'][model]['score'])

    positions = np.arange(len(models))
    bp = ax.boxplot([model_scores[m] for m in models],
                     positions=positions,
                     labels=model_labels,
                     patch_artist=True,
                     widths=0.6)

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Distribución de Scores por Modelo (26 preguntas)', fontsize=14, fontweight='bold')
    ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.5, label='Umbral CORRECTA (≥0.8)')
    ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Umbral INCOMPLETA (≥0.5)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = output_dir / '01_distribucion_scores.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Generado: {output_path}")

    # ========== Gráfico 2: Comparación de métricas RAGAs ==========
    fig, ax = plt.subplots(figsize=(14, 8))

    metric_names = ['faithfulness', 'answer_relevancy', 'context_precision',
                    'context_recall', 'answer_correctness', 'answer_similarity']
    metric_labels = ['Faithfulness', 'Answer Relevancy', 'Context Precision',
                     'Context Recall', 'Answer Correctness', 'Answer Similarity']

    x = np.arange(len(metric_names))
    width = 0.2

    for i, model in enumerate(models):
        metrics_avg = []
        for metric in metric_names:
            values = []
            for result in data['results']:
                if model in result['models']:
                    val = result['models'][model]['metrics'].get(metric, 0)
                    values.append(val)
            metrics_avg.append(sum(values) / len(values) if values else 0)

        offset = width * (i - 1.5)
        ax.bar(x + offset, metrics_avg, width, label=model_labels[i],
               color=colors[i], alpha=0.8)

    ax.set_ylabel('Valor Promedio', fontsize=12, fontweight='bold')
    ax.set_title('Comparación de Métricas RAGAs por Modelo', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 1.0)

    plt.tight_layout()
    output_path = output_dir / '02_comparacion_metricas_ragas.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Generado: {output_path}")

    # ========== Gráfico 3: Rendimiento por pregunta ==========
    fig, ax = plt.subplots(figsize=(16, 6))

    question_ids = [r['question_id'] for r in data['results']]
    for i, model in enumerate(models):
        scores = []
        for result in data['results']:
            if model in result['models']:
                scores.append(result['models'][model]['score'])
            else:
                scores.append(0)

        ax.plot(question_ids, scores, marker='o', label=model_labels[i],
                color=colors[i], linewidth=2, markersize=6, alpha=0.8)

    ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.3, label='Umbral CORRECTA')
    ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.3, label='Umbral INCOMPLETA')
    ax.set_xlabel('ID Pregunta', fontsize=12, fontweight='bold')
    ax.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax.set_title('Evolución de Scores por Pregunta', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    output_path = output_dir / '03_scores_por_pregunta.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Generado: {output_path}")

    # ========== Gráfico 4: Correctas/Incompletas/Incorrectas ==========
    fig, ax = plt.subplots(figsize=(10, 6))

    categories_data = {m: {'correctas': 0, 'incompletas': 0, 'incorrectas': 0} for m in models}
    for result in data['results']:
        for model in models:
            if model in result['models']:
                score = result['models'][model]['score']
                if score >= 0.8:
                    categories_data[model]['correctas'] += 1
                elif score >= 0.5:
                    categories_data[model]['incompletas'] += 1
                else:
                    categories_data[model]['incorrectas'] += 1

    x = np.arange(len(models))
    width = 0.25

    correctas = [categories_data[m]['correctas'] for m in models]
    incompletas = [categories_data[m]['incompletas'] for m in models]
    incorrectas = [categories_data[m]['incorrectas'] for m in models]

    ax.bar(x - width, correctas, width, label='Correctas (≥0.8)', color='#2ecc71', alpha=0.8)
    ax.bar(x, incompletas, width, label='Incompletas (0.5-0.8)', color='#f39c12', alpha=0.8)
    ax.bar(x + width, incorrectas, width, label='Incorrectas (<0.5)', color='#e74c3c', alpha=0.8)

    ax.set_ylabel('Cantidad de Respuestas', fontsize=12, fontweight='bold')
    ax.set_title('Distribución de Calidad de Respuestas por Modelo', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Añadir valores encima de las barras
    for i in range(len(models)):
        ax.text(i - width, correctas[i] + 0.5, str(correctas[i]), ha='center', fontweight='bold')
        ax.text(i, incompletas[i] + 0.5, str(incompletas[i]), ha='center', fontweight='bold')
        ax.text(i + width, incorrectas[i] + 0.5, str(incorrectas[i]), ha='center', fontweight='bold')

    plt.tight_layout()
    output_path = output_dir / '04_distribucion_calidad.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Generado: {output_path}")

    # ========== Gráfico 5: Latencias por modelo ==========
    fig, ax = plt.subplots(figsize=(10, 6))

    latencies = {m: [] for m in models}
    for result in data['results']:
        for model in models:
            if model in result['models']:
                latencies[model].append(result['models'][model].get('latency', 0))

    positions = np.arange(len(models))
    bp = ax.boxplot([latencies[m] for m in models],
                     positions=positions,
                     labels=model_labels,
                     patch_artist=True,
                     widths=0.6)

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel('Latencia (segundos)', fontsize=12, fontweight='bold')
    ax.set_title('Distribución de Latencias por Modelo', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    output_path = output_dir / '05_latencias_por_modelo.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Generado: {output_path}")

    # ========== Gráfico 6: Impacto de thinking tags ==========
    fig, ax = plt.subplots(figsize=(10, 6))

    thinking_data = {}
    for model in models:
        with_think = []
        without_think = []

        for result in data['results']:
            if model in result['models']:
                model_data = result['models'][model]
                relevancy = model_data['metrics'].get('answer_relevancy', 0)

                if '<think>' in model_data['response']:
                    with_think.append(relevancy)
                else:
                    without_think.append(relevancy)

        thinking_data[model] = {
            'with': sum(with_think) / len(with_think) if with_think else 0,
            'without': sum(without_think) / len(without_think) if without_think else 0
        }

    x = np.arange(len(models))
    width = 0.35

    with_vals = [thinking_data[m]['with'] for m in models]
    without_vals = [thinking_data[m]['without'] for m in models]

    ax.bar(x - width/2, with_vals, width, label='Con <think> tags', color='#e74c3c', alpha=0.8)
    ax.bar(x + width/2, without_vals, width, label='Sin <think> tags', color='#2ecc71', alpha=0.8)

    ax.set_ylabel('Answer Relevancy Promedio', fontsize=12, fontweight='bold')
    ax.set_title('Impacto de <think> Tags en Answer Relevancy', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 1.0)

    # Añadir porcentaje de penalización
    for i, model in enumerate(models):
        if without_vals[i] > 0:
            penalty = ((without_vals[i] - with_vals[i]) / without_vals[i]) * 100
            ax.text(i, max(with_vals[i], without_vals[i]) + 0.05,
                   f'{penalty:+.0f}%', ha='center', fontweight='bold', color='red')

    plt.tight_layout()
    output_path = output_dir / '06_impacto_thinking_tags.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Generado: {output_path}")

    # ========== Gráfico 7: Radar chart de métricas ==========
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))

    metric_names = ['Faithfulness', 'Answer\nRelevancy', 'Context\nPrecision',
                    'Context\nRecall', 'Answer\nCorrectness', 'Answer\nSimilarity']

    angles = np.linspace(0, 2 * np.pi, len(metric_names), endpoint=False).tolist()
    angles += angles[:1]  # Cerrar el círculo

    for i, model in enumerate(models):
        values = []
        for metric in ['faithfulness', 'answer_relevancy', 'context_precision',
                      'context_recall', 'answer_correctness', 'answer_similarity']:
            metric_vals = []
            for result in data['results']:
                if model in result['models']:
                    val = result['models'][model]['metrics'].get(metric, 0)
                    metric_vals.append(val)
            values.append(sum(metric_vals) / len(metric_vals) if metric_vals else 0)

        values += values[:1]  # Cerrar el círculo

        ax.plot(angles, values, 'o-', linewidth=2, label=model_labels[i],
               color=colors[i], markersize=8)
        ax.fill(angles, values, alpha=0.15, color=colors[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_names, size=10)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], size=8)
    ax.set_title('Radar de Métricas RAGAs por Modelo', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = output_dir / '07_radar_metricas.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Generado: {output_path}")

    # ========== Gráfico 8: Heatmap de scores por pregunta ==========
    fig, ax = plt.subplots(figsize=(16, 8))

    # Crear matriz de scores
    score_matrix = []
    for model in models:
        model_scores = []
        for result in data['results']:
            if model in result['models']:
                model_scores.append(result['models'][model]['score'])
            else:
                model_scores.append(0)
        score_matrix.append(model_scores)

    score_matrix = np.array(score_matrix)

    im = ax.imshow(score_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

    # Configurar ticks
    ax.set_xticks(np.arange(len(question_ids)))
    ax.set_yticks(np.arange(len(models)))
    ax.set_xticklabels(question_ids)
    ax.set_yticklabels(model_labels)

    # Rotar etiquetas
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Añadir valores en cada celda
    for i in range(len(models)):
        for j in range(len(question_ids)):
            text = ax.text(j, i, f'{score_matrix[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=6)

    ax.set_title('Heatmap de Scores por Modelo y Pregunta', fontsize=14, fontweight='bold')
    ax.set_xlabel('ID Pregunta', fontsize=12, fontweight='bold')
    ax.set_ylabel('Modelo', fontsize=12, fontweight='bold')

    # Añadir colorbar
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('Score', rotation=270, labelpad=15, fontweight='bold')

    plt.tight_layout()
    output_path = output_dir / '08_heatmap_scores.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Generado: {output_path}")

    print(f"\n🎉 Visualizaciones completas! 8 gráficos generados en: {output_dir}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        benchmark_path = sys.argv[1]
    else:
        benchmark_path = "/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer/results/benchmark_20251008_093326.json"

    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = "/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer/results/visualizations"

    generate_visualizations(benchmark_path, output_dir)
