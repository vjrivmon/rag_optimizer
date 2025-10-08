#!/usr/bin/env python3
"""
Comparador de Benchmarks RAG

Compara múltiples archivos de benchmark para analizar la evolución del sistema.

Uso:
    python scripts/compare_benchmarks.py results/benchmark_1.json results/benchmark_2.json results/benchmark_3.json
    python scripts/compare_benchmarks.py results/*.json -o comparison_report.pdf
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


class BenchmarkComparator:
    """Compara múltiples benchmarks y genera reportes completos"""

    def __init__(self, benchmark_files: List[str]):
        self.benchmarks = []
        self.load_benchmarks(benchmark_files)

    def load_benchmarks(self, files: List[str]):
        """Carga todos los archivos de benchmark"""
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extraer timestamp del nombre del archivo
            filename = Path(file_path).stem
            try:
                timestamp_str = filename.split('_')[-2] + '_' + filename.split('_')[-1]
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            except:
                timestamp = datetime.now()

            self.benchmarks.append({
                'file': file_path,
                'filename': Path(file_path).name,
                'timestamp': timestamp,
                'data': data
            })

        # Ordenar por timestamp
        self.benchmarks.sort(key=lambda x: x['timestamp'])

        print(f"✅ Cargados {len(self.benchmarks)} benchmarks")
        for i, b in enumerate(self.benchmarks, 1):
            print(f"  [{i}] {b['filename']} - {b['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

    def compute_summary_stats(self) -> pd.DataFrame:
        """Calcula estadísticas resumen para cada benchmark"""
        summary_data = []

        for bench in self.benchmarks:
            data = bench['data']
            results = data['results']
            models = data['metadata']['models']

            # Métricas por modelo
            metrics_by_model = defaultdict(lambda: defaultdict(list))

            for q in results:
                for model_name, model_data in q['models'].items():
                    metrics = model_data.get('metrics', {})
                    for metric_name, value in metrics.items():
                        if isinstance(value, (int, float)):
                            metrics_by_model[model_name][metric_name].append(value)

            # Context recall promedio
            all_context_recall = []
            for model in models:
                if metrics_by_model[model]['context_recall']:
                    all_context_recall.extend(metrics_by_model[model]['context_recall'])

            avg_context_recall = sum(all_context_recall) / len(all_context_recall) if all_context_recall else 0

            # Preguntas fallidas
            zero_recall_count = 0
            for q in results:
                first_model = models[0]
                if q['models'][first_model]['metrics'].get('context_recall', 0) == 0:
                    zero_recall_count += 1

            # Chunks promedio
            total_chunks = sum(len(q['contexts']) for q in results)
            avg_chunks = total_chunks / len(results)

            # Scores por modelo
            model_scores = {}
            for model in models:
                m = metrics_by_model[model]
                avg_score = sum(m['combined_score']) / len(m['combined_score']) if m['combined_score'] else 0
                model_scores[model] = avg_score

            summary_data.append({
                'benchmark': bench['filename'],
                'timestamp': bench['timestamp'],
                'context_recall': avg_context_recall,
                'success_rate': (26 - zero_recall_count) / 26 * 100,
                'failed_questions': zero_recall_count,
                'avg_chunks': avg_chunks,
                **{f'score_{model}': score for model, score in model_scores.items()}
            })

        return pd.DataFrame(summary_data)

    def plot_evolution(self, df: pd.DataFrame):
        """Genera gráfico de evolución de métricas"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Context Recall Evolution',
                'Success Rate Evolution',
                'Avg Chunks Retrieved',
                'Failed Questions'
            ),
            specs=[[{'secondary_y': False}, {'secondary_y': False}],
                   [{'secondary_y': False}, {'secondary_y': False}]]
        )

        # Context Recall
        fig.add_trace(
            go.Scatter(
                x=list(range(1, len(df) + 1)),
                y=df['context_recall'],
                mode='lines+markers+text',
                name='Context Recall',
                text=[f"{val:.3f}" for val in df['context_recall']],
                textposition='top center',
                marker=dict(size=10, color='blue'),
                line=dict(width=3)
            ),
            row=1, col=1
        )

        # Success Rate
        fig.add_trace(
            go.Scatter(
                x=list(range(1, len(df) + 1)),
                y=df['success_rate'],
                mode='lines+markers+text',
                name='Success Rate (%)',
                text=[f"{val:.1f}%" for val in df['success_rate']],
                textposition='top center',
                marker=dict(size=10, color='green'),
                line=dict(width=3)
            ),
            row=1, col=2
        )

        # Avg Chunks
        fig.add_trace(
            go.Scatter(
                x=list(range(1, len(df) + 1)),
                y=df['avg_chunks'],
                mode='lines+markers+text',
                name='Avg Chunks',
                text=[f"{val:.1f}" for val in df['avg_chunks']],
                textposition='top center',
                marker=dict(size=10, color='orange'),
                line=dict(width=3)
            ),
            row=2, col=1
        )

        # Failed Questions
        fig.add_trace(
            go.Scatter(
                x=list(range(1, len(df) + 1)),
                y=df['failed_questions'],
                mode='lines+markers+text',
                name='Failed Questions',
                text=[f"{int(val)}" for val in df['failed_questions']],
                textposition='top center',
                marker=dict(size=10, color='red'),
                line=dict(width=3),
                fill='tozeroy'
            ),
            row=2, col=2
        )

        fig.update_xaxes(title_text="Benchmark #", row=1, col=1)
        fig.update_xaxes(title_text="Benchmark #", row=1, col=2)
        fig.update_xaxes(title_text="Benchmark #", row=2, col=1)
        fig.update_xaxes(title_text="Benchmark #", row=2, col=2)

        fig.update_yaxes(title_text="Score", row=1, col=1, range=[0, 1])
        fig.update_yaxes(title_text="Percentage", row=1, col=2, range=[0, 100])
        fig.update_yaxes(title_text="Chunks", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=2)

        fig.update_layout(
            title_text="Benchmark Evolution Dashboard",
            showlegend=False,
            height=800,
            font=dict(size=12)
        )

        return fig

    def plot_model_comparison(self, df: pd.DataFrame):
        """Compara scores de modelos a través del tiempo"""
        # Extraer columnas de scores de modelos
        score_cols = [col for col in df.columns if col.startswith('score_')]

        if not score_cols:
            return None

        fig = go.Figure()

        for col in score_cols:
            model_name = col.replace('score_', '')
            fig.add_trace(
                go.Scatter(
                    x=list(range(1, len(df) + 1)),
                    y=df[col],
                    mode='lines+markers',
                    name=model_name,
                    marker=dict(size=10),
                    line=dict(width=2)
                )
            )

        fig.update_layout(
            title="Model Scores Evolution",
            xaxis_title="Benchmark #",
            yaxis_title="Combined Score",
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig

    def analyze_question_changes(self) -> pd.DataFrame:
        """Analiza qué preguntas cambiaron de estado entre benchmarks"""
        if len(self.benchmarks) < 2:
            return pd.DataFrame()

        changes = []

        # Comparar último benchmark con el primero
        first_bench = self.benchmarks[0]['data']
        last_bench = self.benchmarks[-1]['data']

        first_results = first_bench['results']
        last_results = last_bench['results']
        models = first_bench['metadata']['models']

        for i, (q_first, q_last) in enumerate(zip(first_results, last_results), 1):
            question = q_first['question']

            # Usar primer modelo como referencia
            first_model = models[0]

            cr_first = q_first['models'][first_model]['metrics'].get('context_recall', 0)
            cr_last = q_last['models'][first_model]['metrics'].get('context_recall', 0)

            status_change = None
            if cr_first == 0 and cr_last > 0:
                status_change = "✅ RESOLVED (0 → {:.3f})".format(cr_last)
            elif cr_first > 0 and cr_last == 0:
                status_change = "❌ REGRESSED ({:.3f} → 0)".format(cr_first)
            elif cr_first == 0 and cr_last == 0:
                status_change = "⚠️  STILL FAILING"
            else:
                delta = cr_last - cr_first
                if abs(delta) > 0.1:
                    emoji = "📈" if delta > 0 else "📉"
                    status_change = f"{emoji} CHANGED ({cr_first:.3f} → {cr_last:.3f}, Δ={delta:+.3f})"

            if status_change and status_change != "":
                changes.append({
                    'question_id': i,
                    'question': question[:80] + '...' if len(question) > 80 else question,
                    'cr_first': cr_first,
                    'cr_last': cr_last,
                    'status': status_change
                })

        return pd.DataFrame(changes)

    def generate_report(self, output_file: str = None):
        """Genera reporte completo"""
        print("\n" + "=" * 100)
        print(" " * 30 + "BENCHMARK COMPARISON REPORT")
        print("=" * 100)

        # Tabla resumen
        df_summary = self.compute_summary_stats()

        print("\n📊 SUMMARY TABLE:\n")
        print(df_summary.to_string(index=False))

        # Calcular mejoras
        if len(df_summary) >= 2:
            first = df_summary.iloc[0]
            last = df_summary.iloc[-1]

            print("\n📈 OVERALL IMPROVEMENT (First → Last):\n")
            print(f"  Context Recall:   {first['context_recall']:.3f} → {last['context_recall']:.3f} "
                  f"(Δ={last['context_recall'] - first['context_recall']:+.3f}, "
                  f"{((last['context_recall'] / first['context_recall']) - 1) * 100:+.1f}%)")

            print(f"  Success Rate:     {first['success_rate']:.1f}% → {last['success_rate']:.1f}% "
                  f"(Δ={last['success_rate'] - first['success_rate']:+.1f}%)")

            print(f"  Failed Questions: {int(first['failed_questions'])} → {int(last['failed_questions'])} "
                  f"(Δ={int(last['failed_questions'] - first['failed_questions']):+d})")

            print(f"  Avg Chunks:       {first['avg_chunks']:.1f} → {last['avg_chunks']:.1f} "
                  f"(Δ={last['avg_chunks'] - first['avg_chunks']:+.1f})")

        # Analizar cambios en preguntas
        df_changes = self.analyze_question_changes()

        if not df_changes.empty:
            print("\n🔄 QUESTION STATUS CHANGES:\n")
            print(df_changes.to_string(index=False))

        # Generar gráficos
        print("\n📊 Generating visualizations...")

        fig_evolution = self.plot_evolution(df_summary)
        fig_evolution.write_html("benchmark_evolution.html")
        print("  ✓ Saved: benchmark_evolution.html")

        fig_models = self.plot_model_comparison(df_summary)
        if fig_models:
            fig_models.write_html("model_comparison.html")
            print("  ✓ Saved: model_comparison.html")

        # Exportar a CSV
        df_summary.to_csv("benchmark_comparison.csv", index=False)
        print("  ✓ Saved: benchmark_comparison.csv")

        if not df_changes.empty:
            df_changes.to_csv("question_changes.csv", index=False)
            print("  ✓ Saved: question_changes.csv")

        print("\n✅ Comparison complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Compare multiple RAG benchmark results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/compare_benchmarks.py results/benchmark_*.json
  python scripts/compare_benchmarks.py results/b1.json results/b2.json results/b3.json
        """
    )

    parser.add_argument(
        'benchmarks',
        nargs='+',
        help='Benchmark JSON files to compare'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file for PDF report (not implemented yet)',
        default=None
    )

    args = parser.parse_args()

    if len(args.benchmarks) < 2:
        print("❌ Error: Need at least 2 benchmark files to compare")
        sys.exit(1)

    # Verificar que los archivos existen
    for file in args.benchmarks:
        if not Path(file).exists():
            print(f"❌ Error: File not found: {file}")
            sys.exit(1)

    # Crear comparador
    comparator = BenchmarkComparator(args.benchmarks)

    # Generar reporte
    comparator.generate_report(args.output)


if __name__ == "__main__":
    main()
