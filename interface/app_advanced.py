import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="RAG Optimizer Advanced", layout="wide", page_icon="🚀")

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .winner-badge {
        background-color: #ffd700;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 RAG Auto-Optimizer - Dashboard Avanzado")

# Cargar resultados
@st.cache_data
def load_results():
    results_dir = Path('results')

    # Try to find a working benchmark file in the expected format
    possible_files = [
        'benchmark_20251010_113940.json'
    ]

    data = None
    filename = None

    for file_name in possible_files:
        target_file = results_dir / file_name
        if target_file.exists():
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Check if data has the expected structure
                if isinstance(data, dict) and 'results' in data:
                    filename = target_file.name
                    break
                elif isinstance(data, list) and len(data) > 0:
                    # Handle flat list format - convert to expected format
                    if 'model_name' in data[0]:
                        # This is the new format, convert it
                        converted_data = convert_flat_format(data)
                        data = converted_data
                        filename = target_file.name
                        break

            except (json.JSONDecodeError, KeyError):
                continue

    if data is None:
        return None

    return data, filename

def convert_flat_format(flat_data):
    """Convert flat list format to expected format with models structure"""
    # Group by question_id
    questions = {}
    models_set = set()

    for item in flat_data:
        q_id = item['question_id']
        if q_id not in questions:
            questions[q_id] = {
                'question_id': q_id,
                'question': item['question'],
                'contexts': item['contexts'],
                'models': {}
            }

        model_name = item['model_name']
        models_set.add(model_name)

        # Enhanced metrics with missing ones calculated
        enhanced_metrics = item['metrics'].copy()
        if 'context_overlap' not in enhanced_metrics:
            # Simple context overlap calculation (can be improved)
            enhanced_metrics['context_overlap'] = enhanced_metrics.get('context_recall', 0.0) * 0.5

        questions[q_id]['models'][model_name] = {
            'answer': item['answer'],
            'response': item['answer'],  # Add 'response' key for compatibility
            'score': item['metrics'].get('combined_score', 0.0),
            'latency': item['generation_time'],
            'success': True,
            'metrics': enhanced_metrics
        }

        # Determine winner for this question
        if 'winner' not in questions[q_id]:
            questions[q_id]['winner'] = model_name
            questions[q_id]['winner_score'] = item['metrics'].get('combined_score', 0.0)
        else:
            current_score = item['metrics'].get('combined_score', 0.0)
            if current_score > questions[q_id]['winner_score']:
                questions[q_id]['winner'] = model_name
                questions[q_id]['winner_score'] = current_score

    # Create the final structure
    results_list = list(questions.values())

    # Create metadata
    metadata = {
        'timestamp': 'converted',
        'total_questions': len(results_list),
        'models': list(models_set),
        'converted_from_flat_format': True
    }

    return {
        'metadata': metadata,
        'results': results_list
    }

data = load_results()

if data is None:
    st.error("❌ No se encontraron archivos de benchmark válidos. Ejecuta primero: `python benchmark.py` o `python benchmark_parallel.py`")
    st.stop()

results, filename = data

# Si es el nuevo formato con metadata
if 'metadata' in results:
    metadata = results['metadata']
    results_list = results['results']
    st.sidebar.success(f"📊 {metadata['total_questions']} preguntas evaluadas")

    # Handle converted format
    if metadata.get('converted_from_flat_format'):
        st.sidebar.warning("🔄 Formato convertido automáticamente")
    else:
        st.sidebar.info(f"⏱️ Tiempo total: {metadata.get('total_time', 'N/A')}")
else:
    results_list = results
    metadata = None

st.sidebar.header("📁 Archivo")
st.sidebar.text(filename)

# ============= SECCIÓN 1: OVERVIEW =============
st.header("📊 Overview General")

# Calcular estadísticas
model_stats = {}
all_models = set()

for r in results_list:
    for model_name, data in r['models'].items():
        all_models.add(model_name)
        if model_name not in model_stats:
            model_stats[model_name] = {
                'scores': [],
                'latencies': [],
                'wins': 0,
                'total_questions': 0
            }

        model_stats[model_name]['total_questions'] += 1
        if data.get('success', True):
            model_stats[model_name]['scores'].append(data['score'])
            model_stats[model_name]['latencies'].append(data['latency'])

        if r['winner'] == model_name:
            model_stats[model_name]['wins'] += 1

# Métricas principales
cols = st.columns(len(all_models))
for idx, (model_name, stats) in enumerate(model_stats.items()):
    with cols[idx]:
        avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
        avg_latency = sum(stats['latencies']) / len(stats['latencies']) if stats['latencies'] else 0

        st.metric(
            label=f"🤖 {model_name}",
            value=f"{avg_score:.3f}",
            delta=f"{stats['wins']} victorias"
        )
        st.caption(f"⏱️ {avg_latency:.1f}s promedio")

# ============= SECCIÓN 2: COMPARACIÓN DE SCORES =============
st.header("📈 Comparación de Scores")

# Gráfico de scores promedio
score_data = []
for model_name, stats in model_stats.items():
    if stats['scores']:
        score_data.append({
            'Modelo': model_name,
            'Score Promedio': sum(stats['scores']) / len(stats['scores']),
            'Score Máximo': max(stats['scores']),
            'Score Mínimo': min(stats['scores'])
        })

df_scores = pd.DataFrame(score_data)
df_scores = df_scores.sort_values('Score Promedio', ascending=False)

fig_scores = go.Figure()
fig_scores.add_trace(go.Bar(
    name='Promedio',
    x=df_scores['Modelo'],
    y=df_scores['Score Promedio'],
    marker_color='lightblue'
))
fig_scores.add_trace(go.Bar(
    name='Máximo',
    x=df_scores['Modelo'],
    y=df_scores['Score Máximo'],
    marker_color='darkblue'
))
fig_scores.update_layout(
    title="Scores por Modelo",
    xaxis_title="Modelo",
    yaxis_title="Score",
    barmode='group'
)
st.plotly_chart(fig_scores, use_container_width=True)

# ============= SECCIÓN 3: LATENCIAS =============
st.header("⏱️ Análisis de Latencias")

col1, col2 = st.columns(2)

with col1:
    # Latencias promedio
    latency_data = []
    for model_name, stats in model_stats.items():
        if stats['latencies']:
            latency_data.append({
                'Modelo': model_name,
                'Latencia Promedio (s)': sum(stats['latencies']) / len(stats['latencies']),
                'Latencia Total (s)': sum(stats['latencies'])
            })

    df_latency = pd.DataFrame(latency_data)
    df_latency = df_latency.sort_values('Latencia Promedio (s)')

    fig_latency = px.bar(
        df_latency,
        x='Modelo',
        y='Latencia Promedio (s)',
        title="Latencia Promedio por Modelo",
        color='Latencia Promedio (s)',
        color_continuous_scale='Reds'
    )
    st.plotly_chart(fig_latency, use_container_width=True)

with col2:
    # Tiempo total
    fig_total = px.pie(
        df_latency,
        values='Latencia Total (s)',
        names='Modelo',
        title="Distribución de Tiempo Total"
    )
    st.plotly_chart(fig_total, use_container_width=True)

# ============= SECCIÓN 4: VICTORIAS =============
st.header("🏆 Victorias por Modelo")

wins_data = [{'Modelo': model, 'Victorias': stats['wins']}
             for model, stats in model_stats.items()]
df_wins = pd.DataFrame(wins_data)
df_wins = df_wins.sort_values('Victorias', ascending=False)

fig_wins = px.bar(
    df_wins,
    x='Modelo',
    y='Victorias',
    title="Total de Victorias",
    color='Victorias',
    color_continuous_scale='Greens',
    text='Victorias'
)
fig_wins.update_traces(textposition='outside')
st.plotly_chart(fig_wins, use_container_width=True)

# ============= SECCIÓN 5: DETALLE POR PREGUNTA =============
st.header("🔍 Detalle por Pregunta")

# Selector de pregunta
question_ids = [r['question_id'] for r in results_list]
selected_id = st.selectbox("Selecciona una pregunta:", question_ids,
                           format_func=lambda x: f"Q{x}")

# Obtener resultado
result = next(r for r in results_list if r['question_id'] == selected_id)

# Mostrar pregunta
st.subheader(f"📝 {result['question']}")

if result.get('expected_answer'):
    st.info(f"**Respuesta Esperada:** {result['expected_answer']}")

# Tabla comparativa
st.subheader("Comparación de Respuestas")

comparison_data = []
for model_name, model_data in result['models'].items():
    is_winner = (model_name == result['winner'])

    comparison_data.append({
        '🏆': '🏆' if is_winner else '',
        'Modelo': model_name,
        'Score': f"{model_data['score']:.3f}",
        'Tiempo (s)': f"{model_data['latency']:.2f}",
        'Longitud': len(model_data['response']),
        'Context Overlap': f"{model_data['metrics'].get('context_overlap', 0):.2f}"
    })

df_comparison = pd.DataFrame(comparison_data)
df_comparison = df_comparison.sort_values('Score', ascending=False)
st.dataframe(df_comparison, use_container_width=True, hide_index=True)

# Tabs con respuestas completas
st.subheader("💬 Respuestas Completas")

tabs = st.tabs(list(result['models'].keys()))

for tab, (model_name, model_data) in zip(tabs, result['models'].items()):
    with tab:
        is_winner = (model_name == result['winner'])

        if is_winner:
            st.success(f"🏆 **{model_name}** - GANADOR")
        else:
            st.info(f"**{model_name}**")

        # Respuesta
        st.markdown("**Respuesta:**")
        st.write(model_data['response'])

        # Métricas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Score", f"{model_data['score']:.3f}")
        with col2:
            st.metric("Latencia", f"{model_data['latency']:.2f}s")
        with col3:
            overlap = model_data['metrics'].get('context_overlap', 0)
            st.metric("Context Overlap", f"{overlap:.2f}")
        with col4:
            st.metric("Longitud", len(model_data['response']))

        # Métricas detalladas
        with st.expander("📊 Ver Métricas Detalladas"):
            metrics_display = {}
            for k, v in model_data['metrics'].items():
                if isinstance(v, float):
                    metrics_display[k] = f"{v:.4f}"
                else:
                    metrics_display[k] = v
            st.json(metrics_display)

        # Parámetros utilizados
        with st.expander("⚙️ Ver Parámetros"):
            st.json(model_data.get('params', {}))

# ============= SECCIÓN 6: EVOLUCIÓN DE SCORES =============
st.header("📉 Evolución de Scores")

# Crear gráfico de evolución
evolution_data = []
for idx, r in enumerate(results_list, 1):
    for model_name, model_data in r['models'].items():
        evolution_data.append({
            'Pregunta': idx,
            'Modelo': model_name,
            'Score': model_data['score']
        })

df_evolution = pd.DataFrame(evolution_data)

fig_evolution = px.line(
    df_evolution,
    x='Pregunta',
    y='Score',
    color='Modelo',
    title="Evolución de Scores a lo largo de las Preguntas",
    markers=True
)
fig_evolution.update_layout(hovermode='x unified')
st.plotly_chart(fig_evolution, use_container_width=True)

# ============= SECCIÓN 7: ANÁLISIS DE MÉTRICAS =============
st.header("🎯 Análisis de Métricas")

# Recopilar todas las métricas
all_metrics = {}
for r in results_list:
    for model_name, model_data in r['models'].items():
        if model_name not in all_metrics:
            all_metrics[model_name] = {}

        for metric, value in model_data['metrics'].items():
            if isinstance(value, (int, float)) and metric != 'response_length':
                if metric not in all_metrics[model_name]:
                    all_metrics[model_name][metric] = []
                all_metrics[model_name][metric].append(value)

# Seleccionar métrica a visualizar
available_metrics = set()
for metrics_dict in all_metrics.values():
    available_metrics.update(metrics_dict.keys())

if available_metrics:
    selected_metric = st.selectbox("Selecciona métrica:", sorted(available_metrics))

    # Crear gráfico de boxplot
    boxplot_data = []
    for model_name, metrics_dict in all_metrics.items():
        if selected_metric in metrics_dict:
            for value in metrics_dict[selected_metric]:
                boxplot_data.append({
                    'Modelo': model_name,
                    selected_metric: value
                })

    if boxplot_data:
        df_boxplot = pd.DataFrame(boxplot_data)

        fig_box = px.box(
            df_boxplot,
            x='Modelo',
            y=selected_metric,
            title=f"Distribución de {selected_metric}",
            color='Modelo'
        )
        st.plotly_chart(fig_box, use_container_width=True)

# ============= SECCIÓN 8: TABLA RESUMEN FINAL =============
st.header("📋 Tabla Resumen Final")

summary_data = []
for model_name, stats in model_stats.items():
    if stats['scores']:
        summary_data.append({
            'Modelo': model_name,
            'Score Promedio': f"{sum(stats['scores'])/len(stats['scores']):.3f}",
            'Score Máximo': f"{max(stats['scores']):.3f}",
            'Score Mínimo': f"{min(stats['scores']):.3f}",
            'Latencia Promedio': f"{sum(stats['latencies'])/len(stats['latencies']):.2f}s",
            'Tiempo Total': f"{sum(stats['latencies']):.0f}s",
            'Victorias': stats['wins'],
            'Tasa de Éxito': f"{len(stats['scores'])/stats['total_questions']*100:.0f}%"
        })

df_summary = pd.DataFrame(summary_data)
df_summary = df_summary.sort_values('Score Promedio', ascending=False)

st.dataframe(
    df_summary,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Modelo': st.column_config.TextColumn('Modelo', width='medium'),
        'Score Promedio': st.column_config.TextColumn('Score Avg', width='small'),
        'Victorias': st.column_config.NumberColumn('Wins', width='small')
    }
)

# ============= SECCIÓN 9: COMPARADOR DE BENCHMARKS =============
st.header("📈 Comparador de Benchmarks")

st.info("🔍 Compara múltiples benchmarks para ver la evolución del sistema")

# Listar todos los benchmarks disponibles
results_dir = Path('results')
all_benchmarks = sorted(results_dir.glob('benchmark_*.json'), key=lambda p: p.stat().st_mtime)

if len(all_benchmarks) > 1:
    # Selector de benchmarks a comparar
    selected_files = st.multiselect(
        "Selecciona benchmarks a comparar:",
        all_benchmarks,
        default=all_benchmarks[-3:] if len(all_benchmarks) >= 3 else all_benchmarks,
        format_func=lambda p: p.name
    )

    if len(selected_files) >= 2:
        # Cargar benchmarks seleccionados
        benchmarks_data = []
        for file_path in selected_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                bench_data = json.load(f)
                benchmarks_data.append({
                    'name': file_path.name,
                    'data': bench_data,
                    'timestamp': file_path.stat().st_mtime
                })

        # Ordenar por timestamp
        benchmarks_data.sort(key=lambda x: x['timestamp'])

        # Calcular métricas para cada benchmark
        comparison_metrics = []
        for idx, bench in enumerate(benchmarks_data, 1):
            data = bench['data']
            results_list = data['results']
            models = data['metadata']['models']

            # Context recall promedio
            all_cr = []
            for model in models:
                for q in results_list:
                    cr = q['models'][model]['metrics'].get('context_recall', 0)
                    all_cr.append(cr)
            avg_cr = sum(all_cr) / len(all_cr) if all_cr else 0

            # Preguntas fallidas
            failed = sum(1 for q in results_list
                        if q['models'][models[0]]['metrics'].get('context_recall', 0) == 0)

            # Scores por modelo
            model_scores = {}
            for model in models:
                scores = [q['models'][model]['metrics'].get('combined_score', 0)
                         for q in results_list]
                model_scores[model] = sum(scores) / len(scores) if scores else 0

            comparison_metrics.append({
                'benchmark': f"#{idx}",
                'name': bench['name'][:30] + '...' if len(bench['name']) > 30 else bench['name'],
                'context_recall': avg_cr,
                'success_rate': (len(results_list) - failed) / len(results_list) * 100,
                'failed': failed,
                'avg_chunks': sum(len(q['contexts']) for q in results_list) / len(results_list),
                **{f'score_{model}': score for model, score in model_scores.items()}
            })

        # Crear DataFrame
        df_comparison = pd.DataFrame(comparison_metrics)

        # Gráfico de evolución de Context Recall
        col1, col2 = st.columns(2)

        with col1:
            fig_cr = go.Figure()
            fig_cr.add_trace(go.Scatter(
                x=df_comparison['benchmark'],
                y=df_comparison['context_recall'],
                mode='lines+markers+text',
                name='Context Recall',
                text=[f"{val:.3f}" for val in df_comparison['context_recall']],
                textposition='top center',
                marker=dict(size=12, color='blue'),
                line=dict(width=3)
            ))
            fig_cr.update_layout(
                title="Context Recall Evolution",
                xaxis_title="Benchmark",
                yaxis_title="Score",
                yaxis=dict(range=[0, 1]),
                height=400
            )
            st.plotly_chart(fig_cr, use_container_width=True)

        with col2:
            fig_sr = go.Figure()
            fig_sr.add_trace(go.Scatter(
                x=df_comparison['benchmark'],
                y=df_comparison['success_rate'],
                mode='lines+markers+text',
                name='Success Rate',
                text=[f"{val:.1f}%" for val in df_comparison['success_rate']],
                textposition='top center',
                marker=dict(size=12, color='green'),
                line=dict(width=3)
            ))
            fig_sr.update_layout(
                title="Success Rate Evolution",
                xaxis_title="Benchmark",
                yaxis_title="Percentage",
                yaxis=dict(range=[0, 100]),
                height=400
            )
            st.plotly_chart(fig_sr, use_container_width=True)

        # Gráfico de comparación de modelos
        st.subheader("📊 Model Scores Comparison")

        # Preparar datos para gráfico de modelos
        model_cols = [col for col in df_comparison.columns if col.startswith('score_')]

        if model_cols:
            fig_models = go.Figure()

            for col in model_cols:
                model_name = col.replace('score_', '')
                fig_models.add_trace(go.Scatter(
                    x=df_comparison['benchmark'],
                    y=df_comparison[col],
                    mode='lines+markers',
                    name=model_name,
                    marker=dict(size=10),
                    line=dict(width=2)
                ))

            fig_models.update_layout(
                title="Model Scores Evolution",
                xaxis_title="Benchmark",
                yaxis_title="Combined Score",
                height=500,
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_models, use_container_width=True)

        # Tabla comparativa
        st.subheader("📋 Comparison Table")

        # Formatear tabla para display
        display_df = df_comparison.copy()
        display_df['context_recall'] = display_df['context_recall'].apply(lambda x: f"{x:.3f}")
        display_df['success_rate'] = display_df['success_rate'].apply(lambda x: f"{x:.1f}%")
        display_df['avg_chunks'] = display_df['avg_chunks'].apply(lambda x: f"{x:.1f}")

        # Formatear scores de modelos
        for col in model_cols:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.3f}")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Calcular mejoras
        if len(df_comparison) >= 2:
            st.subheader("📈 Overall Improvements (First → Last)")

            first = df_comparison.iloc[0]
            last = df_comparison.iloc[-1]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                cr_delta = last['context_recall'] - first['context_recall']
                cr_pct = (cr_delta / first['context_recall']) * 100 if first['context_recall'] > 0 else 0
                st.metric(
                    "Context Recall",
                    f"{last['context_recall']:.3f}",
                    f"{cr_delta:+.3f} ({cr_pct:+.1f}%)"
                )

            with col2:
                sr_delta = last['success_rate'] - first['success_rate']
                st.metric(
                    "Success Rate",
                    f"{last['success_rate']:.1f}%",
                    f"{sr_delta:+.1f}%"
                )

            with col3:
                failed_delta = last['failed'] - first['failed']
                st.metric(
                    "Failed Questions",
                    f"{int(last['failed'])}",
                    f"{int(failed_delta):+d}"
                )

            with col4:
                chunks_delta = last['avg_chunks'] - first['avg_chunks']
                st.metric(
                    "Avg Chunks",
                    f"{last['avg_chunks']:.1f}",
                    f"{chunks_delta:+.1f}"
                )

    else:
        st.warning("⚠️ Selecciona al menos 2 benchmarks para comparar")

else:
    st.info("📊 Solo hay 1 benchmark disponible. Ejecuta más benchmarks para habilitar la comparación.")

# ============= SECCIÓN 10: EXPORTADOR COMPLETO =============
st.header("📥 Exportador de Resultados")

st.info("💾 Exporta los resultados del benchmark actual con todas las métricas")

col1, col2 = st.columns(2)

with col1:
    st.subheader("PDF Export")
    st.write("Exporta a PDF con formato profesional incluyendo:")
    st.write("- ✅ 11 métricas completas (RAGAs + personalizadas)")
    st.write("- ✅ Tabla de métricas por pregunta/modelo")
    st.write("- ✅ Respuestas completas de cada modelo")
    st.write("- ✅ Formato A3 landscape")

    if st.button("📄 Generar PDF Completo", type="primary"):
        # Ejecutar export_pdf.py
        import subprocess
        import datetime

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"results/benchmark_report_{timestamp}.pdf"

        with st.spinner("Generando PDF..."):
            try:
                result = subprocess.run(
                    ['python', 'export_pdf.py', f'results/{filename}', '-o', output_file],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    st.success(f"✅ PDF generado: `{output_file}`")

                    # Ofrecer descarga
                    with open(output_file, 'rb') as f:
                        pdf_data = f.read()

                    st.download_button(
                        label="⬇️ Descargar PDF",
                        data=pdf_data,
                        file_name=f"benchmark_report_{timestamp}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error(f"❌ Error al generar PDF:\n{result.stderr}")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

with col2:
    st.subheader("Excel Export")
    st.write("Exporta todas las métricas a Excel para análisis:")
    st.write("- ✅ Una hoja por modelo")
    st.write("- ✅ Todas las 11 métricas")
    st.write("- ✅ Formato tabla para análisis")

    if st.button("📊 Generar Excel", type="primary"):
        # Crear Excel con pandas
        import datetime

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"results/benchmark_metrics_{timestamp}.xlsx"

        with st.spinner("Generando Excel..."):
            try:
                # Crear Excel con múltiples hojas
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    # Hoja resumen
                    df_summary.to_excel(writer, sheet_name='Summary', index=False)

                    # Hoja por cada modelo
                    for model_name in all_models:
                        model_data = []

                        for idx, r in enumerate(results_list, 1):
                            if model_name in r['models']:
                                model_result = r['models'][model_name]
                                metrics = model_result['metrics']

                                row = {
                                    'Question_ID': idx,
                                    'Question': r['question'],
                                    'Score': model_result['score'],
                                    'Latency': model_result['latency'],
                                    **metrics
                                }
                                model_data.append(row)

                        df_model = pd.DataFrame(model_data)
                        df_model.to_excel(writer, sheet_name=model_name[:31], index=False)

                st.success(f"✅ Excel generado: `{output_file}`")

                # Ofrecer descarga
                with open(output_file, 'rb') as f:
                    excel_data = f.read()

                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=excel_data,
                    file_name=f"benchmark_metrics_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("**📊 Sistema RAG Auto-Optimizer con RAGAs** | UPV - DNI Project")
st.caption("v3.1 - Hybrid Retrieval + FAQ-Aware Chunks + Comparador + Exportador Completo")
