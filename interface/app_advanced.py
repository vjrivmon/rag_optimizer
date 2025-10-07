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
    json_files = list(results_dir.glob('*.json'))

    if not json_files:
        return None

    # Cargar el archivo más reciente
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)

    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data, latest_file.name

data = load_results()

if data is None:
    st.error("❌ No hay resultados. Ejecuta primero: `python benchmark.py`")
    st.stop()

results, filename = data

# Si es el nuevo formato con metadata
if 'metadata' in results:
    metadata = results['metadata']
    results_list = results['results']
    st.sidebar.success(f"📊 {metadata['total_questions']} preguntas evaluadas")
    st.sidebar.info(f"⏱️ Tiempo total: {metadata['total_time']:.0f}s")
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

# Footer
st.markdown("---")
st.markdown("**📊 Sistema RAG Auto-Optimizer con RAGAs** | UPV - DNI Project")
