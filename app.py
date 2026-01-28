import streamlit as st
import json
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="RAG Optimizer", layout="wide")

st.title("🚀 RAG Auto-Optimizer - Resultados")

# Cargar resultados
try:
    with open('results/evaluation_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)
except FileNotFoundError:
    st.error("❌ No hay resultados. Ejecuta primero: python main.py")
    st.stop()
except Exception as e:
    st.error(f"❌ Error cargando resultados: {e}")
    st.stop()

# Sidebar: Selección de pregunta
st.sidebar.header("Selecciona Pregunta")
question_ids = [r['question_id'] for r in results]
selected_id = st.sidebar.selectbox("ID Pregunta:", question_ids, index=0)

# Obtener resultado seleccionado
result = next(r for r in results if r['question_id'] == selected_id)

# Mostrar pregunta
st.subheader("📝 Pregunta")
st.info(result['question'])

if result.get('expected_answer'):
    st.success(f"**Respuesta Esperada:** {result['expected_answer']}")

# Comparación de modelos
st.subheader("📊 Comparación de Modelos")

model_data = []
for model_name, data in result['models'].items():
    model_data.append({
        'Modelo': model_name,
        'Score': data['score'],
        'Latencia (s)': round(data['latency'], 2),
        'Ganador': '🏆' if model_name == result['winner'] else ''
    })

df = pd.DataFrame(model_data)
st.dataframe(df, use_container_width=True, hide_index=True)

# Gráfico de scores
fig = px.bar(
    df,
    x='Modelo',
    y='Score',
    title="Scores por Modelo",
    color='Modelo',
    text='Score'
)
fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# Tabs con respuestas
st.subheader("💬 Respuestas de Cada Modelo")

tabs = st.tabs(list(result['models'].keys()))

for tab, (model_name, data) in zip(tabs, result['models'].items()):
    with tab:
        is_winner = (model_name == result['winner'])

        if is_winner:
            st.success(f"🏆 **{model_name}** - GANADOR")
        else:
            st.info(f"**{model_name}**")

        st.markdown("**Respuesta:**")
        st.write(data['response'])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Score", f"{data['score']:.3f}")
        with col2:
            st.metric("Latencia", f"{data['latency']:.2f}s")
        with col3:
            metrics = data.get('metrics', {})
            faithfulness = metrics.get('faithfulness', 0)
            st.metric("Faithfulness", f"{faithfulness:.2f}")

        with st.expander("Ver Parámetros"):
            st.json(data['params'])

        with st.expander("Ver Todas las Métricas"):
            st.json(data['metrics'])

# Estadísticas generales
st.subheader("📈 Estadísticas Generales")

# Calcular stats
all_scores = {}
for r in results:
    for model_name, data in r['models'].items():
        if model_name not in all_scores:
            all_scores[model_name] = []
        all_scores[model_name].append(data['score'])

stats_data = []
for model_name, scores in all_scores.items():
    stats_data.append({
        'Modelo': model_name,
        'Promedio': round(sum(scores) / len(scores), 3),
        'Mejor': round(max(scores), 3),
        'Peor': round(min(scores), 3),
        'Victorias': sum(1 for r in results if r['winner'] == model_name)
    })

stats_df = pd.DataFrame(stats_data)
stats_df = stats_df.sort_values('Promedio', ascending=False)
st.dataframe(stats_df, use_container_width=True, hide_index=True)

# Gráfico de victorias
fig_wins = px.bar(
    stats_df,
    x='Modelo',
    y='Victorias',
    title="Total de Victorias por Modelo",
    color='Modelo',
    text='Victorias'
)
fig_wins.update_traces(textposition='outside')
fig_wins.update_layout(showlegend=False)
st.plotly_chart(fig_wins, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**📊 Sistema RAG Auto-Optimizer** | UPV - DNI Project")
