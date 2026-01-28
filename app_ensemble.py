"""
Dashboard Especializado para Análisis de Ensemble RAG
=====================================================

Dashboard profesional para visualizar y comparar resultados de:
- Modelos individuales vs Estrategias Ensemble
- Métricas RAGAs detalladas
- Análisis por pregunta y comparación de respuestas
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import numpy as np

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Dashboard Ensemble RAG",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

@st.cache_data
def load_ensemble_results(file_path: str) -> Dict:
    """Carga resultados de ensemble desde JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error al cargar archivo: {str(e)}")
        return None

def calculate_model_statistics(data: Dict) -> pd.DataFrame:
    """Calcula estadísticas agregadas por modelo individual"""
    model_stats = {}
    
    for result in data['results']:
        for individual in result['individual']:
            model = individual['model_name']
            if model not in model_stats:
                model_stats[model] = {
                    'scores': [],
                    'faithfulness': [],
                    'answer_relevancy': [],
                    'context_precision': [],
                    'context_recall': [],
                    'answer_correctness': [],
                    'answer_similarity': [],
                    'generation_times': [],
                    'correct_count': 0,
                    'total_count': 0
                }
            
            metrics = individual['metrics']
            model_stats[model]['scores'].append(metrics['combined_score'])
            model_stats[model]['faithfulness'].append(metrics.get('faithfulness', 0))
            model_stats[model]['answer_relevancy'].append(metrics.get('answer_relevancy', 0))
            model_stats[model]['context_precision'].append(metrics.get('context_precision', 0))
            model_stats[model]['context_recall'].append(metrics.get('context_recall', 0))
            model_stats[model]['answer_correctness'].append(metrics.get('answer_correctness', 0))
            model_stats[model]['answer_similarity'].append(metrics.get('answer_similarity', 0))
            model_stats[model]['generation_times'].append(individual.get('generation_time', 0))
            model_stats[model]['total_count'] += 1
            
            if metrics['combined_score'] >= 0.8:
                model_stats[model]['correct_count'] += 1
    
    # Convertir a DataFrame
    rows = []
    for model, stats in model_stats.items():
        rows.append({
            'Modelo': model,
            'Score Promedio': np.mean(stats['scores']),
            'Faithfulness': np.mean(stats['faithfulness']),
            'Answer Relevancy': np.mean(stats['answer_relevancy']),
            'Context Precision': np.mean(stats['context_precision']),
            'Context Recall': np.mean(stats['context_recall']),
            'Answer Correctness': np.mean(stats['answer_correctness']),
            'Answer Similarity': np.mean(stats['answer_similarity']),
            'Tiempo Promedio (s)': np.mean(stats['generation_times']),
            'Correctas': stats['correct_count'],
            'Total': stats['total_count'],
            'Tasa Éxito': stats['correct_count'] / stats['total_count']
        })
    
    df = pd.DataFrame(rows)
    return df.sort_values('Score Promedio', ascending=False)

def calculate_strategy_statistics(data: Dict) -> pd.DataFrame:
    """Calcula estadísticas agregadas por estrategia ensemble"""
    strategy_stats = {}
    
    for result in data['results']:
        for strategy_name, strategy_data in result['ensemble'].items():
            if strategy_name not in strategy_stats:
                strategy_stats[strategy_name] = {
                    'scores': [],
                    'faithfulness': [],
                    'answer_relevancy': [],
                    'context_precision': [],
                    'context_recall': [],
                    'answer_correctness': [],
                    'answer_similarity': [],
                    'generation_times': [],
                    'correct_count': 0,
                    'total_count': 0
                }
            
            metrics = strategy_data['metrics']
            strategy_stats[strategy_name]['scores'].append(metrics['combined_score'])
            strategy_stats[strategy_name]['faithfulness'].append(metrics.get('faithfulness', 0))
            strategy_stats[strategy_name]['answer_relevancy'].append(metrics.get('answer_relevancy', 0))
            strategy_stats[strategy_name]['context_precision'].append(metrics.get('context_precision', 0))
            strategy_stats[strategy_name]['context_recall'].append(metrics.get('context_recall', 0))
            strategy_stats[strategy_name]['answer_correctness'].append(metrics.get('answer_correctness', 0))
            strategy_stats[strategy_name]['answer_similarity'].append(metrics.get('answer_similarity', 0))
            strategy_stats[strategy_name]['generation_times'].append(strategy_data.get('generation_time', 0))
            strategy_stats[strategy_name]['total_count'] += 1
            
            if metrics['combined_score'] >= 0.8:
                strategy_stats[strategy_name]['correct_count'] += 1
    
    # Convertir a DataFrame
    rows = []
    for strategy, stats in strategy_stats.items():
        rows.append({
            'Estrategia': strategy,
            'Score Promedio': np.mean(stats['scores']),
            'Faithfulness': np.mean(stats['faithfulness']),
            'Answer Relevancy': np.mean(stats['answer_relevancy']),
            'Context Precision': np.mean(stats['context_precision']),
            'Context Recall': np.mean(stats['context_recall']),
            'Answer Correctness': np.mean(stats['answer_correctness']),
            'Answer Similarity': np.mean(stats['answer_similarity']),
            'Tiempo Promedio (s)': np.mean(stats['generation_times']),
            'Correctas': stats['correct_count'],
            'Total': stats['total_count'],
            'Tasa Éxito': stats['correct_count'] / stats['total_count']
        })
    
    df = pd.DataFrame(rows)
    return df.sort_values('Score Promedio', ascending=False)

def get_question_comparison(data: Dict, question_id: int) -> Dict:
    """Obtiene comparación detallada para una pregunta específica"""
    for result in data['results']:
        if result.get('question_id') == question_id:
            return result
    return None

def clean_thinking_tags(text: str) -> str:
    """Elimina las etiquetas <think> de las respuestas"""
    if not text:
        return text
    
    # Remover <think>...</think>
    import re
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def main():
    # Header
    st.title("🎲 Dashboard Ensemble RAG")
    st.markdown("### Análisis Comparativo: Modelos Individuales vs Estrategias Ensemble")
    st.markdown("---")
    
    # Sidebar - Selección de archivo
    st.sidebar.title("⚙️ Configuración")
    
    # Buscar archivos de ensemble
    results_dir = Path("results")
    ensemble_files = sorted(
        [f for f in results_dir.glob("ensemble_*.json")],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if not ensemble_files:
        st.error("❌ No se encontraron archivos de resultados ensemble")
        st.info("💡 Ejecuta primero: `python benchmark_ensemble.py`")
        return
    
    # Selector de archivo
    file_names = [f.name for f in ensemble_files]
    
    def format_file_name(filename):
        """Formatea el nombre del archivo con timestamp"""
        file_path = Path('results') / filename
        timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
        return f"{filename} ({timestamp.strftime('%Y-%m-%d %H:%M')})"
    
    selected_file = st.sidebar.selectbox(
        "📂 Seleccionar resultado:",
        file_names,
        format_func=format_file_name
    )
    
    # Cargar datos
    data = load_ensemble_results(f"results/{selected_file}")
    
    if not data:
        st.error("❌ No se pudieron cargar los datos")
        return
    
    # Información general
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Información General")
    st.sidebar.metric("Total Preguntas", data['total_questions'])
    st.sidebar.metric("Modelos", len(data['models']))
    st.sidebar.metric("Estrategias", len(data['strategies']))
    st.sidebar.markdown(f"**Timestamp:** {data['timestamp']}")
    
    # Calcular estadísticas
    model_stats_df = calculate_model_statistics(data)
    strategy_stats_df = calculate_strategy_statistics(data)
    
    # ========================================================================
    # TAB 1: RESUMEN COMPARATIVO
    # ========================================================================
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Resumen",
        "🤖 Modelos Individuales",
        "🎲 Estrategias Ensemble",
        "🔍 Análisis por Pregunta",
        "📈 Métricas RAGAs"
    ])
    
    with tab1:
        st.header("📊 Resumen Comparativo General")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        best_model = model_stats_df.iloc[0]
        best_strategy = strategy_stats_df.iloc[0]
        
        with col1:
            st.metric(
                "🥇 Mejor Modelo Individual",
                best_model['Modelo'],
                f"{best_model['Score Promedio']:.3f}"
            )
        
        with col2:
            st.metric(
                "🎲 Mejor Estrategia Ensemble",
                best_strategy['Estrategia'],
                f"{best_strategy['Score Promedio']:.3f}"
            )
        
        improvement = best_strategy['Score Promedio'] - best_model['Score Promedio']
        improvement_pct = (improvement / best_model['Score Promedio'] * 100) if best_model['Score Promedio'] > 0 else 0
        
        with col3:
            st.metric(
                "📈 Mejora Ensemble",
                f"{improvement:+.3f}",
                f"{improvement_pct:+.1f}%"
            )
        
        with col4:
            winner = "Ensemble" if improvement > 0 else ("Empate" if improvement == 0 else "Individual")
            st.metric("🏆 Ganador", winner)
        
        st.markdown("---")
        
        # Gráfico comparativo de scores
        st.subheader("📊 Comparación de Scores Promedio")
        
        # Combinar datos para comparación
        comparison_data = []
        
        for _, row in model_stats_df.iterrows():
            comparison_data.append({
                'Nombre': row['Modelo'],
                'Tipo': 'Modelo Individual',
                'Score': row['Score Promedio'],
                'Correctas': f"{row['Correctas']}/{row['Total']}"
            })
        
        for _, row in strategy_stats_df.iterrows():
            comparison_data.append({
                'Nombre': row['Estrategia'],
                'Tipo': 'Estrategia Ensemble',
                'Score': row['Score Promedio'],
                'Correctas': f"{row['Correctas']}/{row['Total']}"
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        fig = px.bar(
            comparison_df,
            x='Nombre',
            y='Score',
            color='Tipo',
            text='Score',
            hover_data=['Correctas'],
            title="Comparación Global: Modelos vs Estrategias",
            color_discrete_map={
                'Modelo Individual': '#FF6B6B',
                'Estrategia Ensemble': '#4ECDC4'
            }
        )
        
        fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
        fig.update_layout(
            xaxis_title="",
            yaxis_title="Score Promedio",
            yaxis_range=[0, 1.1],
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla comparativa
        st.markdown("---")
        st.subheader("📋 Tabla Comparativa Detallada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🤖 Top 3 Modelos Individuales")
            st.dataframe(
                model_stats_df[['Modelo', 'Score Promedio', 'Correctas', 'Total', 'Tasa Éxito']].head(3),
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            st.markdown("#### 🎲 Top 3 Estrategias Ensemble")
            st.dataframe(
                strategy_stats_df[['Estrategia', 'Score Promedio', 'Correctas', 'Total', 'Tasa Éxito']].head(3),
                hide_index=True,
                use_container_width=True
            )
    
    # ========================================================================
    # TAB 2: MODELOS INDIVIDUALES
    # ========================================================================
    
    with tab2:
        st.header("🤖 Análisis Detallado de Modelos Individuales")
        
        # Tabla completa
        st.subheader("📊 Estadísticas Completas")
        st.dataframe(
            model_stats_df.style.format({
                'Score Promedio': '{:.3f}',
                'Faithfulness': '{:.3f}',
                'Answer Relevancy': '{:.3f}',
                'Context Precision': '{:.3f}',
                'Context Recall': '{:.3f}',
                'Answer Correctness': '{:.3f}',
                'Answer Similarity': '{:.3f}',
                'Tiempo Promedio (s)': '{:.2f}',
                'Tasa Éxito': '{:.1%}'
            }).background_gradient(subset=['Score Promedio'], cmap='RdYlGn'),
            use_container_width=True,
            hide_index=True
        )
        
        # Radar chart de métricas
        st.markdown("---")
        st.subheader("🎯 Comparación de Métricas RAGAs por Modelo")
        
        fig = go.Figure()
        
        metrics_to_compare = [
            'Faithfulness',
            'Answer Relevancy',
            'Context Precision',
            'Context Recall',
            'Answer Correctness',
            'Answer Similarity'
        ]
        
        for _, row in model_stats_df.iterrows():
            fig.add_trace(go.Scatterpolar(
                r=[row[metric] for metric in metrics_to_compare],
                theta=metrics_to_compare,
                fill='toself',
                name=row['Modelo']
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=True,
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de tiempos de generación
        st.markdown("---")
        st.subheader("⏱️ Tiempos de Generación")
        
        fig = px.bar(
            model_stats_df,
            x='Modelo',
            y='Tiempo Promedio (s)',
            text='Tiempo Promedio (s)',
            title="Tiempo Promedio de Generación por Modelo",
            color='Tiempo Promedio (s)',
            color_continuous_scale='Viridis'
        )
        
        fig.update_traces(texttemplate='%{text:.2f}s', textposition='outside')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========================================================================
    # TAB 3: ESTRATEGIAS ENSEMBLE
    # ========================================================================
    
    with tab3:
        st.header("🎲 Análisis Detallado de Estrategias Ensemble")
        
        # Tabla completa
        st.subheader("📊 Estadísticas Completas")
        st.dataframe(
            strategy_stats_df.style.format({
                'Score Promedio': '{:.3f}',
                'Faithfulness': '{:.3f}',
                'Answer Relevancy': '{:.3f}',
                'Context Precision': '{:.3f}',
                'Context Recall': '{:.3f}',
                'Answer Correctness': '{:.3f}',
                'Answer Similarity': '{:.3f}',
                'Tiempo Promedio (s)': '{:.2f}',
                'Tasa Éxito': '{:.1%}'
            }).background_gradient(subset=['Score Promedio'], cmap='RdYlGn'),
            use_container_width=True,
            hide_index=True
        )
        
        # Descripción de estrategias
        st.markdown("---")
        st.subheader("📖 Descripción de Estrategias")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🗳️ Voting (Votación Mayoritaria)**
            - Selecciona la respuesta con mayor `combined_score`
            - Usa tiebreaker: gemma2:27b si hay empate
            - Ideal para preguntas con respuestas claras
            
            **⚖️ Weighted (Votación Ponderada)**
            - Asigna pesos según rendimiento histórico
            - Gemma2: 40%, Qwen3: 30%, Llama3.3: 25%, DeepSeek: 5%
            - Favorece modelos consistentes
            """)
        
        with col2:
            st.markdown("""
            **🎯 Routing (Enrutamiento Inteligente)**
            - Rutas preguntas a modelos especializados
            - Config especial para P11, P20, P25
            - Adapta estrategia según tipo de pregunta
            
            **🤝 Consensus (Consenso con Fallback)**
            - Busca consenso entre modelos (stdev < 0.15)
            - Si hay divergencia → fallback a gemma2:27b
            - Robusto ante respuestas conflictivas
            """)
        
        # Radar chart de estrategias
        st.markdown("---")
        st.subheader("🎯 Comparación de Métricas RAGAs por Estrategia")
        
        fig = go.Figure()
        
        for _, row in strategy_stats_df.iterrows():
            fig.add_trace(go.Scatterpolar(
                r=[row[metric] for metric in metrics_to_compare],
                theta=metrics_to_compare,
                fill='toself',
                name=row['Estrategia']
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=True,
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ========================================================================
    # TAB 4: ANÁLISIS POR PREGUNTA
    # ========================================================================
    
    with tab4:
        st.header("🔍 Análisis Detallado por Pregunta")
        
        # Selector de pregunta
        question_ids = [r.get('question_id', 0) for r in data['results']]
        question_texts = [r.get('question', '') for r in data['results']]
        
        selected_q_idx = st.selectbox(
            "Seleccionar pregunta:",
            range(len(question_ids)),
            format_func=lambda i: f"P{question_ids[i]}: {question_texts[i]}"
        )
        
        question_data = data['results'][selected_q_idx]
        
        st.markdown(f"### Pregunta {question_data['question_id']}: {question_data['question']}")
        st.markdown("---")
        
        # Tabla de scores por modelo y estrategia
        st.subheader("📊 Scores de Modelos y Estrategias")
        
        scores_data = []
        
        # Modelos individuales
        for individual in question_data['individual']:
            scores_data.append({
                'Tipo': 'Modelo',
                'Nombre': individual['model_name'],
                'Score': individual['metrics']['combined_score'],
                'Faithfulness': individual['metrics'].get('faithfulness', 0),
                'Answer Relevancy': individual['metrics'].get('answer_relevancy', 0),
                'Tiempo (s)': individual.get('generation_time', 0)
            })
        
        # Estrategias ensemble
        for strategy_name, strategy_data in question_data['ensemble'].items():
            scores_data.append({
                'Tipo': 'Estrategia',
                'Nombre': strategy_name,
                'Score': strategy_data['metrics']['combined_score'],
                'Faithfulness': strategy_data['metrics'].get('faithfulness', 0),
                'Answer Relevancy': strategy_data['metrics'].get('answer_relevancy', 0),
                'Tiempo (s)': strategy_data.get('generation_time', 0)
            })
        
        scores_df = pd.DataFrame(scores_data)
        
        st.dataframe(
            scores_df.style.format({
                'Score': '{:.3f}',
                'Faithfulness': '{:.3f}',
                'Answer Relevancy': '{:.3f}',
                'Tiempo (s)': '{:.2f}'
            }).background_gradient(subset=['Score'], cmap='RdYlGn'),
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico comparativo
        fig = px.bar(
            scores_df,
            x='Nombre',
            y='Score',
            color='Tipo',
            text='Score',
            title=f"Comparación de Scores - P{question_data['question_id']}",
            color_discrete_map={
                'Modelo': '#FF6B6B',
                'Estrategia': '#4ECDC4'
            }
        )
        
        fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
        fig.update_layout(height=400, yaxis_range=[0, 1.1])
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Respuestas
        st.markdown("---")
        st.subheader("💬 Respuestas Generadas")
        
        # Selector de modelo/estrategia para ver respuesta
        all_options = ['Todos los modelos'] + [m['model_name'] for m in question_data['individual']] + \
                      ['---Estrategias---'] + list(question_data['ensemble'].keys())
        
        selected_option = st.selectbox("Ver respuesta de:", all_options)
        
        if selected_option == 'Todos los modelos':
            for individual in question_data['individual']:
                with st.expander(f"🤖 {individual['model_name']} - Score: {individual['metrics']['combined_score']:.3f}"):
                    answer = clean_thinking_tags(individual['answer'])
                    st.markdown(answer)
                    st.caption(f"Tiempo: {individual.get('generation_time', 0):.2f}s")
        elif selected_option == '---Estrategias---':
            st.info("Selecciona una estrategia específica")
        elif selected_option in [m['model_name'] for m in question_data['individual']]:
            individual = next(m for m in question_data['individual'] if m['model_name'] == selected_option)
            st.markdown("#### Respuesta:")
            answer = clean_thinking_tags(individual['answer'])
            st.markdown(answer)
            
            st.markdown("#### Métricas Detalladas:")
            metrics_cols = st.columns(6)
            metrics = individual['metrics']
            
            metrics_cols[0].metric("Faithfulness", f"{metrics.get('faithfulness', 0):.2f}")
            metrics_cols[1].metric("Relevancy", f"{metrics.get('answer_relevancy', 0):.2f}")
            metrics_cols[2].metric("Precision", f"{metrics.get('context_precision', 0):.2f}")
            metrics_cols[3].metric("Recall", f"{metrics.get('context_recall', 0):.2f}")
            metrics_cols[4].metric("Correctness", f"{metrics.get('answer_correctness', 0):.2f}")
            metrics_cols[5].metric("Similarity", f"{metrics.get('answer_similarity', 0):.2f}")
            
            st.caption(f"⏱️ Tiempo de generación: {individual.get('generation_time', 0):.2f}s")
        else:
            strategy_data = question_data['ensemble'][selected_option]
            st.markdown("#### Respuesta:")
            answer = clean_thinking_tags(strategy_data['answer'])
            st.markdown(answer)
            
            st.markdown("#### Información de la Estrategia:")
            st.info(f"**Seleccionada de:** {strategy_data['selected_from']}")
            st.info(f"**Razón:** {strategy_data['selection_reason']}")
            
            st.markdown("#### Métricas Detalladas:")
            metrics_cols = st.columns(6)
            metrics = strategy_data['metrics']
            
            metrics_cols[0].metric("Faithfulness", f"{metrics.get('faithfulness', 0):.2f}")
            metrics_cols[1].metric("Relevancy", f"{metrics.get('answer_relevancy', 0):.2f}")
            metrics_cols[2].metric("Precision", f"{metrics.get('context_precision', 0):.2f}")
            metrics_cols[3].metric("Recall", f"{metrics.get('context_recall', 0):.2f}")
            metrics_cols[4].metric("Correctness", f"{metrics.get('answer_correctness', 0):.2f}")
            metrics_cols[5].metric("Similarity", f"{metrics.get('answer_similarity', 0):.2f}")
            
            st.caption(f"⏱️ Tiempo: {strategy_data.get('generation_time', 0):.2f}s")
    
    # ========================================================================
    # TAB 5: MÉTRICAS RAGAS
    # ========================================================================
    
    with tab5:
        st.header("📈 Análisis Detallado de Métricas RAGAs")
        
        st.markdown("""
        ### 📚 Explicación de Métricas RAGAs
        
        Las métricas RAGAs evalúan diferentes aspectos de la calidad de las respuestas:
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎯 Faithfulness (25%)** - Fidelidad al contexto
            - ¿La respuesta es fiel al contexto recuperado?
            - Detecta alucinaciones o información inventada
            
            **💡 Answer Relevancy (20%)** - Relevancia de la respuesta
            - ¿La respuesta es relevante para la pregunta?
            - Evalúa si responde lo que se preguntó
            
            **🔍 Context Precision (15%)** - Precisión del contexto
            - ¿El contexto recuperado es preciso?
            - Evalúa la calidad de la recuperación
            """)
        
        with col2:
            st.markdown("""
            **📊 Context Recall (20%)** - Completitud del contexto
            - ¿Se recuperó todo el contexto necesario?
            - Evalúa si falta información importante
            
            **✅ Answer Correctness (10%)** - Corrección de la respuesta
            - ¿La respuesta es correcta vs ground truth?
            - Comparación con respuesta esperada
            
            **🎭 Answer Similarity (10%)** - Similitud semántica
            - ¿Qué tan similar es a la respuesta esperada?
            - Evalúa similitud de significado
            """)
        
        st.markdown("---")
        
        # Distribución de métricas por modelo
        st.subheader("📊 Distribución de Métricas por Modelo")
        
        metric_to_plot = st.selectbox(
            "Seleccionar métrica:",
            ['combined_score', 'faithfulness', 'answer_relevancy', 'context_precision', 
             'context_recall', 'answer_correctness', 'answer_similarity']
        )
        
        # Recolectar datos para la métrica seleccionada
        plot_data = []
        for result in data['results']:
            for individual in result['individual']:
                metric_key = 'Score' if metric_to_plot == 'combined_score' else metric_to_plot.replace('_', ' ').title()
                plot_data.append({
                    'Modelo': individual['model_name'],
                    'Tipo': 'Modelo Individual',
                    'Pregunta': f"P{result['question_id']}",
                    'Valor': individual['metrics'].get(metric_to_plot, 0)
                })
            
            for strategy_name, strategy_data in result['ensemble'].items():
                plot_data.append({
                    'Modelo': strategy_name,
                    'Tipo': 'Estrategia Ensemble',
                    'Pregunta': f"P{result['question_id']}",
                    'Valor': strategy_data['metrics'].get(metric_to_plot, 0)
                })
        
        plot_df = pd.DataFrame(plot_data)
        
        # Box plot
        fig = px.box(
            plot_df,
            x='Modelo',
            y='Valor',
            color='Tipo',
            title=f"Distribución de {metric_to_plot.replace('_', ' ').title()}",
            color_discrete_map={
                'Modelo Individual': '#FF6B6B',
                'Estrategia Ensemble': '#4ECDC4'
            }
        )
        
        fig.update_layout(
            yaxis_range=[0, 1],
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap de correlación
        st.markdown("---")
        st.subheader("🔥 Heatmap de Correlación de Métricas")
        
        # Preparar datos para correlación
        correlation_data = []
        for result in data['results']:
            for individual in result['individual']:
                correlation_data.append({
                    'Faithfulness': individual['metrics'].get('faithfulness', 0),
                    'Answer Relevancy': individual['metrics'].get('answer_relevancy', 0),
                    'Context Precision': individual['metrics'].get('context_precision', 0),
                    'Context Recall': individual['metrics'].get('context_recall', 0),
                    'Answer Correctness': individual['metrics'].get('answer_correctness', 0),
                    'Answer Similarity': individual['metrics'].get('answer_similarity', 0),
                    'Combined Score': individual['metrics'].get('combined_score', 0)
                })
        
        corr_df = pd.DataFrame(correlation_data)
        correlation_matrix = corr_df.corr()
        
        fig = px.imshow(
            correlation_matrix,
            text_auto='.2f',
            aspect='auto',
            color_continuous_scale='RdYlGn',
            title="Correlación entre Métricas RAGAs"
        )
        
        fig.update_layout(height=600)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        💡 **Interpretación del Heatmap:**
        - Valores cercanos a 1.0 (verde) → Alta correlación positiva
        - Valores cercanos a 0.0 (amarillo) → Sin correlación
        - Valores cercanos a -1.0 (rojo) → Alta correlación negativa
        """)

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    main()

