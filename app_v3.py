#!/usr/bin/env python3
"""
🚀 RAG Optimizer Dashboard v3 - Análisis Cualitativo y Cuantitativo

Versión profesional para evaluación completa del sistema RAG v2:
- Comparación directa con respuestas esperadas
- Evaluación cualitativa automática
- Métricas RAGAs explicadas
- Exportación profesional (Excel + Markdown)
- Análisis visual avanzado
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import sys

# Añadir directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from interface.qualitative_evaluator import (
    evaluate_qualitative,
    get_evaluation_icon,
    get_evaluation_color,
    calculate_qualitative_stats,
    format_qualitative_summary
)
from interface.export_professional import (
    export_to_excel,
    generate_markdown_report,
    export_to_pdf
)

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="RAG Optimizer v3",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .correct-badge {
        background-color: #28a745;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: bold;
    }
    
    .incomplete-badge {
        background-color: #ffc107;
        color: #000;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: bold;
    }
    
    .incorrect-badge {
        background-color: #dc3545;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: bold;
    }
    
    .workflow-box {
        background-color: #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNCIONES DE CARGA Y PROCESAMIENTO
# ============================================================================

@st.cache_data
def load_benchmark_files():
    """Obtiene lista de archivos de benchmark disponibles"""
    results_dir = Path('results')
    files = sorted(
        [f for f in results_dir.glob('benchmark_*.json')],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return files


@st.cache_data
def load_dataset():
    """Carga el dataset con respuestas esperadas"""
    dataset_path = Path('data/evaluation_dataset.json')
    with open(dataset_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@st.cache_data
def load_and_enrich_benchmark(benchmark_path: Path):
    """Carga benchmark y lo enriquece con respuestas esperadas y evaluación cualitativa"""
    
    # Cargar benchmark
    with open(benchmark_path, 'r', encoding='utf-8') as f:
        benchmark_data = json.load(f)
    
    # Cargar dataset
    dataset = load_dataset()
    expected_map = {q['id']: q for q in dataset}
    
    # Enriquecer datos
    enriched = []
    for item in benchmark_data:
        qid = item['question_id']
        expected_q = expected_map.get(qid, {})
        
        # Añadir respuesta esperada
        item['expected_answer'] = expected_q.get('expected_answer', 'No disponible')
        item['category'] = expected_q.get('category', 'N/A')
        item['difficulty'] = expected_q.get('difficulty', 'N/A')
        item['keywords'] = expected_q.get('keywords', [])
        
        # Evaluación cualitativa
        eval_result, eval_explanation = evaluate_qualitative(
            item['answer'],
            item['expected_answer'],
            item['metrics']
        )
        item['qualitative_eval'] = eval_result
        item['qualitative_explanation'] = eval_explanation
        
        enriched.append(item)
    
    return enriched, dataset


# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

def main():
    # Header
    st.markdown('<div class="main-header">🚀 RAG Optimizer Dashboard v3</div>', unsafe_allow_html=True)
    st.markdown("### Análisis Cualitativo y Cuantitativo del Sistema RAG")
    
    # Sidebar - Selección de benchmark
    st.sidebar.title("⚙️ Configuración")
    
    benchmark_files = load_benchmark_files()
    
    if not benchmark_files:
        st.error("❌ No se encontraron archivos de benchmark en results/")
        st.stop()
    
    selected_file = st.sidebar.selectbox(
        "Selecciona un benchmark:",
        benchmark_files,
        format_func=lambda x: f"{x.name} ({datetime.fromtimestamp(x.stat().st_mtime).strftime('%Y-%m-%d %H:%M')})"
    )
    
    # Cargar datos
    with st.spinner("Cargando y procesando datos..."):
        enriched_data, dataset = load_and_enrich_benchmark(selected_file)
    
    # Calcular estadísticas
    df = pd.DataFrame(enriched_data)
    models = sorted(df['model_name'].unique())
    total_questions = len(dataset)
    
    # Estadísticas cualitativas
    all_evals = df['qualitative_eval'].tolist()
    qual_stats = calculate_qualitative_stats(all_evals)
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Resumen",
        "📋 Comparación Detallada",
        "📈 Análisis Cuantitativo",
        "🔄 Workflow del Sistema",
        "📖 Guía de Métricas",
        "💾 Exportar Reporte"
    ])
    
    # ========================================================================
    # TAB 1: RESUMEN EJECUTIVO
    # ========================================================================
    with tab1:
        st.header("📊 Resumen Ejecutivo")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Preguntas", total_questions)
        with col2:
            st.metric("Modelos Evaluados", len(models))
        with col3:
            avg_score = df['metrics'].apply(lambda x: x['combined_score']).mean()
            st.metric("Score Promedio", f"{avg_score:.3f}")
        with col4:
            avg_time = df['generation_time'].mean()
            st.metric("Tiempo Promedio", f"{avg_time:.1f}s")
        
        st.markdown("---")
        
        # Evaluación cualitativa global
        st.subheader("🎯 Evaluación Cualitativa Global")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #28a745;">✅ Correctas</h3>
                <h1>{qual_stats['correctas']}</h1>
                <p style="font-size: 1.2rem;">{qual_stats['pct_correctas']:.1f}% del total</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #ffc107;">⚠️ Incompletas</h3>
                <h1>{qual_stats['incompletas']}</h1>
                <p style="font-size: 1.2rem;">{qual_stats['pct_incompletas']:.1f}% del total</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: #dc3545;">❌ Incorrectas</h3>
                <h1>{qual_stats['incorrectas']}</h1>
                <p style="font-size: 1.2rem;">{qual_stats['pct_incorrectas']:.1f}% del total</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Gráfica de distribución
        st.subheader("📊 Distribución de Evaluación Cualitativa")
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=['✅ Correctas', '⚠️ Incompletas', '❌ Incorrectas'],
            values=[qual_stats['correctas'], qual_stats['incompletas'], qual_stats['incorrectas']],
            marker=dict(colors=['#28a745', '#ffc107', '#dc3545']),
            hole=0.4
        )])
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("---")
        
        # Rendimiento por modelo
        st.subheader("🤖 Rendimiento por Modelo")
        
        model_stats = []
        for model in models:
            model_df = df[df['model_name'] == model]
            model_evals = model_df['qualitative_eval'].tolist()
            model_qual_stats = calculate_qualitative_stats(model_evals)
            
            model_stats.append({
                'Modelo': model,
                'Score Promedio': model_df['metrics'].apply(lambda x: x['combined_score']).mean(),
                'Correctas (%)': model_qual_stats['pct_correctas'],
                'Incompletas (%)': model_qual_stats['pct_incompletas'],
                'Incorrectas (%)': model_qual_stats['pct_incorrectas'],
                'Tiempo Promedio (s)': model_df['generation_time'].mean()
            })
        
        df_model_stats = pd.DataFrame(model_stats)
        st.dataframe(df_model_stats, use_container_width=True, hide_index=True)
    
    # ========================================================================
    # TAB 2: COMPARACIÓN DETALLADA
    # ========================================================================
    with tab2:
        st.header("📋 Comparación Detallada de Respuestas")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_category = st.multiselect(
                "Filtrar por categoría:",
                options=sorted(df['category'].unique()),
                default=[]
            )
        with col2:
            filter_difficulty = st.multiselect(
                "Filtrar por dificultad:",
                options=sorted(df['difficulty'].unique()),
                default=[]
            )
        with col3:
            filter_evaluation = st.multiselect(
                "Filtrar por evaluación:",
                options=['correcta', 'incompleta', 'incorrecta'],
                default=[]
            )
        
        # Aplicar filtros
        filtered_df = df.copy()
        if filter_category:
            filtered_df = filtered_df[filtered_df['category'].isin(filter_category)]
        if filter_difficulty:
            filtered_df = filtered_df[filtered_df['difficulty'].isin(filter_difficulty)]
        if filter_evaluation:
            filtered_df = filtered_df[filtered_df['qualitative_eval'].isin(filter_evaluation)]
        
        # Agrupar por pregunta
        questions_grouped = {}
        for _, row in filtered_df.iterrows():
            qid = row['question_id']
            if qid not in questions_grouped:
                questions_grouped[qid] = {
                    'question': row['question'],
                    'expected': row['expected_answer'],
                    'category': row['category'],
                    'difficulty': row['difficulty'],
                    'models': {}
                }
            questions_grouped[qid]['models'][row['model_name']] = row
        
        # Mostrar cada pregunta
        for qid in sorted(questions_grouped.keys()):
            q_data = questions_grouped[qid]
            
            with st.expander(f"**P{qid}: {q_data['question']}** [{q_data['category']} - {q_data['difficulty']}]", expanded=False):
                # Respuesta esperada
                st.markdown("**📝 Respuesta Esperada:**")
                st.info(q_data['expected'])
                
                st.markdown("---")
                
                # Respuestas de cada modelo
                for model_name in models:
                    if model_name in q_data['models']:
                        model_data = q_data['models'][model_name]
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.markdown(f"**🤖 {model_name}**")
                        
                        with col2:
                            eval_result = model_data['qualitative_eval']
                            icon = get_evaluation_icon(eval_result)
                            st.markdown(f"**{icon} {eval_result.capitalize()}**")
                        
                        with col3:
                            score = model_data['metrics']['combined_score']
                            time = model_data['generation_time']
                            st.markdown(f"Score: **{score:.2f}** | Tiempo: **{time:.1f}s**")
                        
                        # Respuesta del modelo
                        st.markdown(model_data['answer'])
                        
                        # Métricas detalladas (colapsable)
                        with st.expander("Ver métricas detalladas"):
                            metrics = model_data['metrics']
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Faithfulness", f"{metrics['faithfulness']:.2f}")
                                st.metric("Context Precision", f"{metrics['context_precision']:.2f}")
                            with col2:
                                st.metric("Answer Relevancy", f"{metrics['answer_relevancy']:.2f}")
                                st.metric("Context Recall", f"{metrics['context_recall']:.2f}")
                            with col3:
                                st.metric("Answer Correctness", f"{metrics['answer_correctness']:.2f}")
                                st.metric("Answer Similarity", f"{metrics['answer_similarity']:.2f}")
                        
                        st.markdown("---")
    
    # ========================================================================
    # TAB 3: ANÁLISIS CUANTITATIVO
    # ========================================================================
    with tab3:
        st.header("📈 Análisis Cuantitativo")
        
        # Gráfica de evolución de scores por pregunta
        st.subheader("📊 Evolución de Scores por Pregunta")
        
        # Preparar datos para la gráfica
        plot_data = []
        for _, row in df.iterrows():
            plot_data.append({
                'Pregunta': row['question_id'],
                'Score': row['metrics']['combined_score'],
                'Modelo': row['model_name']
            })
        
        df_plot = pd.DataFrame(plot_data)
        
        fig_evolution = px.line(
            df_plot,
            x='Pregunta',
            y='Score',
            color='Modelo',
            markers=True,
            title="Evolución de Scores a lo largo de las Preguntas"
        )
        fig_evolution.update_layout(height=500)
        st.plotly_chart(fig_evolution, use_container_width=True)
        
        st.markdown("---")
        
        # Heatmap de métricas
        st.subheader("🔥 Heatmap de Métricas por Modelo y Pregunta")
        
        selected_metric = st.selectbox(
            "Selecciona métrica:",
            ['combined_score', 'faithfulness', 'answer_relevancy', 'context_precision', 
             'context_recall', 'answer_correctness', 'answer_similarity']
        )
        
        # Preparar datos para heatmap
        heatmap_data = []
        for qid in sorted(df['question_id'].unique()):
            row_data = {'Pregunta': f"P{qid}"}
            for model in models:
                model_row = df[(df['question_id'] == qid) & (df['model_name'] == model)]
                if not model_row.empty:
                    row_data[model] = model_row.iloc[0]['metrics'][selected_metric]
                else:
                    row_data[model] = None
            heatmap_data.append(row_data)
        
        df_heatmap = pd.DataFrame(heatmap_data)
        df_heatmap.set_index('Pregunta', inplace=True)
        
        fig_heatmap = px.imshow(
            df_heatmap.values,
            labels=dict(x="Modelo", y="Pregunta", color=selected_metric),
            x=df_heatmap.columns,
            y=df_heatmap.index,
            color_continuous_scale='RdYlGn',
            aspect="auto"
        )
        fig_heatmap.update_layout(height=800)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        st.markdown("---")
        
        # Análisis de tiempos de respuesta
        st.subheader("⏱️ Análisis de Tiempos de Respuesta")
        
        fig_time = px.box(
            df,
            x='model_name',
            y='generation_time',
            color='model_name',
            title="Distribución de Tiempos de Respuesta por Modelo"
        )
        fig_time.update_layout(height=400)
        st.plotly_chart(fig_time, use_container_width=True)
    
    # ========================================================================
    # TAB 4: WORKFLOW DEL SISTEMA
    # ========================================================================
    with tab4:
        st.header("🔄 Workflow del Sistema RAG v2")
        
        st.markdown("""
        El sistema RAG v2 utiliza un enfoque de **dos fases** que optimiza tanto la velocidad 
        de generación como la calidad de la evaluación.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="workflow-box">
                <h3>⚡ FASE 1: Generación (5-10 min)</h3>
                <p><strong>Objetivo:</strong> Generar respuestas rápidamente para todos los modelos</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            **Pasos:**
            
            1. **Enhanced RAG Engine**
               - Búsqueda híbrida (semántica + BM25)
               - Recuperación de contextos relevantes
               - Top-k adaptativo
            
            2. **Validación Inteligente**
               - Detección de preguntas problemáticas
               - Estrategia de fallback progresivo:
                 * ultra_permissive
                 * very_permissive
                 * permissive
               - Búsqueda exacta por keywords (último recurso)
            
            3. **Generación de Respuesta**
               - Prompt optimizado según tipo de pregunta
               - Temperatura adaptativa
               - Control de tokens
            
            4. **Limpieza de Respuestas**
               - Eliminación de tags `<think>`, `<thinking>`
               - Normalización de formato
            
            5. **Guardado en SQLite**
               - Almacenamiento estructurado
               - Listo para evaluación posterior
            """)
        
        with col2:
            st.markdown("""
            <div class="workflow-box">
                <h3>🎯 FASE 2: Evaluación (background)</h3>
                <p><strong>Objetivo:</strong> Evaluar calidad con métricas RAGAs usando OpenAI API</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            **Pasos:**
            
            1. **Carga de Respuestas**
               - Lee respuestas de SQLite
               - Batch processing eficiente
            
            2. **Evaluación con RAGAs**
               - **OpenAI API** (100x más rápido que Ollama)
               - 6 métricas por respuesta:
                 * Faithfulness (Fidelidad)
                 * Answer Relevancy (Relevancia)
                 * Context Precision (Precisión)
                 * Context Recall (Exhaustividad)
                 * Answer Correctness (Corrección)
                 * Answer Similarity (Similitud)
            
            3. **Cálculo de Combined Score**
               - Promedio ponderado de las 6 métricas
               - Normalización 0.0 - 1.0
            
            4. **Actualización en Tiempo Real**
               - Updates progresivos en BD
               - Recuperable si falla
               - Dashboard actualizable en vivo
            """)
        
        st.markdown("---")
        
        st.subheader("💡 Ventajas de este Enfoque")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("""
            **⚡ Velocidad**
            
            - Generación paralela
            - No espera por evaluación
            - 5-10 min vs. 2-3 horas
            """)
        
        with col2:
            st.info("""
            **🎯 Calidad**
            
            - Evaluación con OpenAI
            - Métricas estándar RAGAs
            - Reproducible y confiable
            """)
        
        with col3:
            st.warning("""
            **🔄 Robustez**
            
            - Recuperable si falla
            - Guardado persistente
            - Re-evaluable sin regenerar
            """)
    
    # ========================================================================
    # TAB 5: GUÍA DE MÉTRICAS
    # ========================================================================
    with tab5:
        st.header("📖 Guía de Métricas RAGAs")
        
        st.markdown("""
        Las **métricas RAGAs** (Retrieval-Augmented Generation Assessment) son estándares de la industria 
        para evaluar sistemas RAG. A continuación se explica cada una en detalle:
        """)
        
        # Faithfulness
        with st.expander("🎯 Faithfulness (Fidelidad)", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                ### ¿Qué mide?
                Si la respuesta se basa **únicamente** en los contextos proporcionados, sin inventar información.
                
                ### ¿Por qué es importante?
                Es crucial para evitar **alucinaciones** - cuando el modelo inventa información que no está 
                en los documentos fuente.
                
                ### Interpretación
                - **Score alto (>0.8):** ✅ La respuesta está completamente fundamentada en los contextos
                - **Score medio (0.5-0.8):** ⚠️ Algunas partes pueden no estar fundamentadas
                - **Score bajo (<0.5):** ❌ El modelo está inventando información
                
                ### Ejemplo
                **Contexto:** "La reunión es el lunes a las 10am"
                - ✅ Alta fidelidad: "La reunión es el lunes a las 10am"
                - ❌ Baja fidelidad: "La reunión es el lunes a las 10am en la sala 301" (inventó la sala)
                """)
            
            with col2:
                # Gráfica ejemplo
                faithfulness_scores = df['metrics'].apply(lambda x: x['faithfulness']).tolist()
                fig = go.Figure(data=[go.Histogram(x=faithfulness_scores, nbinsx=20)])
                fig.update_layout(
                    title="Distribución de Faithfulness",
                    xaxis_title="Score",
                    yaxis_title="Frecuencia",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Answer Relevancy
        with st.expander("🔍 Answer Relevancy (Relevancia)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                ### ¿Qué mide?
                Si la respuesta responde **directamente** a la pregunta formulada.
                
                ### ¿Por qué es importante?
                Evita respuestas que divagan o proporcionan información irrelevante aunque sea correcta.
                
                ### Interpretación
                - **Score alto (>0.8):** ✅ Respuesta directa y al punto
                - **Score medio (0.5-0.8):** ⚠️ Respuesta parcialmente relevante
                - **Score bajo (<0.5):** ❌ Respuesta divaga o no responde la pregunta
                
                ### Ejemplo
                **Pregunta:** "¿A qué hora es la reunión?"
                - ✅ Alta relevancia: "La reunión es a las 10am"
                - ❌ Baja relevancia: "Las reuniones son importantes para la coordinación del equipo..." (no responde)
                """)
            
            with col2:
                relevancy_scores = df['metrics'].apply(lambda x: x['answer_relevancy']).tolist()
                fig = go.Figure(data=[go.Histogram(x=relevancy_scores, nbinsx=20)])
                fig.update_layout(
                    title="Distribución de Relevancy",
                    xaxis_title="Score",
                    yaxis_title="Frecuencia",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Context Precision
        with st.expander("🎲 Context Precision (Precisión de Contexto)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                ### ¿Qué mide?
                Qué tan **relevantes** son los contextos recuperados para responder la pregunta.
                
                ### ¿Por qué es importante?
                Alta precisión significa que el sistema de retrieval está funcionando bien, 
                trayendo información útil y no "ruido".
                
                ### Interpretación
                - **Score alto (>0.8):** ✅ Los contextos son altamente relevantes
                - **Score medio (0.5-0.8):** ⚠️ Mezcla de contextos relevantes e irrelevantes
                - **Score bajo (<0.5):** ❌ Muchos contextos irrelevantes recuperados
                
                ### Impacto
                Baja precisión → El modelo recibe información confusa → Respuestas de menor calidad
                """)
            
            with col2:
                precision_scores = df['metrics'].apply(lambda x: x['context_precision']).tolist()
                fig = go.Figure(data=[go.Histogram(x=precision_scores, nbinsx=20)])
                fig.update_layout(
                    title="Distribución de Precision",
                    xaxis_title="Score",
                    yaxis_title="Frecuencia",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Context Recall
        with st.expander("📚 Context Recall (Exhaustividad de Contexto)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                ### ¿Qué mide?
                Si se recuperaron **todos** los contextos necesarios para responder completamente la pregunta.
                
                ### ¿Por qué es importante?
                Si falta información importante, la respuesta será incompleta aunque sea correcta 
                con lo que tiene.
                
                ### Interpretación
                - **Score alto (>0.8):** ✅ Se recuperó toda la información necesaria
                - **Score medio (0.5-0.8):** ⚠️ Falta alguna información complementaria
                - **Score bajo (<0.5):** ❌ Faltan contextos importantes
                
                ### Trade-off
                Alta recall vs. Alta precision: balance entre traer todo vs. traer solo lo relevante
                """)
            
            with col2:
                recall_scores = df['metrics'].apply(lambda x: x['context_recall']).tolist()
                fig = go.Figure(data=[go.Histogram(x=recall_scores, nbinsx=20)])
                fig.update_layout(
                    title="Distribución de Recall",
                    xaxis_title="Score",
                    yaxis_title="Frecuencia",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Answer Correctness
        with st.expander("✓ Answer Correctness (Corrección)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                ### ¿Qué mide?
                Si la respuesta es **factualmente correcta** comparada con la respuesta esperada.
                
                ### ¿Por qué es importante?
                Es la métrica más importante para el usuario final: ¿la respuesta es correcta o no?
                
                ### Interpretación
                - **Score alto (>0.8):** ✅ Respuesta correcta y completa
                - **Score medio (0.5-0.8):** ⚠️ Respuesta parcialmente correcta
                - **Score bajo (<0.5):** ❌ Respuesta incorrecta o muy incompleta
                
                ### Evaluación
                Compara tanto hechos específicos como completitud de la respuesta
                """)
            
            with col2:
                correctness_scores = df['metrics'].apply(lambda x: x['answer_correctness']).tolist()
                fig = go.Figure(data=[go.Histogram(x=correctness_scores, nbinsx=20)])
                fig.update_layout(
                    title="Distribución de Correctness",
                    xaxis_title="Score",
                    yaxis_title="Frecuencia",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Answer Similarity
        with st.expander("🔄 Answer Similarity (Similitud)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("""
                ### ¿Qué mide?
                Qué tan **similar semánticamente** es la respuesta a la respuesta esperada.
                
                ### ¿Por qué es importante?
                Dos respuestas pueden ser correctas pero expresadas de forma diferente. 
                Esta métrica captura similitud en el contenido, no solo en las palabras exactas.
                
                ### Interpretación
                - **Score alto (>0.8):** ✅ Muy similar a la respuesta esperada
                - **Score medio (0.5-0.8):** ⚠️ Similar pero con diferencias notables
                - **Score bajo (<0.5):** ❌ Respuesta muy diferente
                
                ### Nota
                Baja similitud NO significa necesariamente incorrecta - puede estar expresada diferente
                """)
            
            with col2:
                similarity_scores = df['metrics'].apply(lambda x: x['answer_similarity']).tolist()
                fig = go.Figure(data=[go.Histogram(x=similarity_scores, nbinsx=20)])
                fig.update_layout(
                    title="Distribución de Similarity",
                    xaxis_title="Score",
                    yaxis_title="Frecuencia",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Combined Score
        st.markdown("---")
        st.subheader("🎯 Combined Score (Score Combinado)")
        
        st.info("""
        El **Combined Score** es el **promedio de las 6 métricas** anteriores. 
        Representa la calidad general de la respuesta en una escala de 0.0 a 1.0.
        
        **Interpretación:**
        - **0.8 - 1.0:** ✅ Excelente - Respuesta de muy alta calidad
        - **0.6 - 0.8:** ⚠️ Buena - Respuesta aceptable con margen de mejora
        - **0.4 - 0.6:** ⚠️ Regular - Respuesta con problemas significativos
        - **0.0 - 0.4:** ❌ Mala - Respuesta de baja calidad o incorrecta
        """)
    
    # ========================================================================
    # TAB 6: EXPORTAR REPORTE
    # ========================================================================
    with tab6:
        st.header("💾 Exportar Reporte")
        
        st.markdown("""
        Genera reportes profesionales para presentar a evaluadores, stakeholders o para 
        documentación del proyecto.
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📊 Exportar a Excel")
            st.markdown("""
            El archivo Excel incluye:
            - **Sheet 1:** Comparación cualitativa completa
            - **Sheet 2:** Métricas detalladas por evaluación
            - **Sheet 3:** Análisis agregado por modelo
            - **Sheet 4:** Análisis agregado por pregunta
            """)
            
            if st.button("📥 Generar Excel", type="primary"):
                with st.spinner("Generando archivo Excel..."):
                    excel_buffer = export_to_excel(enriched_data, dataset)
                    
                    st.download_button(
                        label="⬇️ Descargar Excel",
                        data=excel_buffer,
                        file_name=f"rag_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                st.success("✅ Excel generado correctamente!")
        
        with col2:
            st.subheader("📄 Exportar a PDF")
            st.markdown("""
            El reporte PDF incluye:
            - **Portada** con información general
            - **Resumen ejecutivo** con métricas agregadas
            - **Análisis por modelo** con tablas comparativas
            - **Guía de métricas RAGAs** explicadas
            - **Tabla completa** de preguntas, respuestas esperadas, respuestas de cada modelo y tiempos
            - **Conclusiones** y recomendaciones
            """)
            
            if st.button("📄 Generar PDF", type="primary"):
                with st.spinner("Generando reporte PDF profesional..."):
                    try:
                        pdf_buffer = export_to_pdf(enriched_data, dataset, qual_stats)
                        
                        st.download_button(
                            label="⬇️ Descargar PDF",
                            data=pdf_buffer,
                            file_name=f"rag_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                        st.success("✅ PDF generado correctamente!")
                    except Exception as e:
                        st.error(f"❌ Error al generar PDF: {str(e)}")
                        st.info("Asegúrate de tener instaladas las dependencias: pip install reportlab matplotlib")
        
        with col3:
            st.subheader("📝 Exportar a Markdown")
            st.markdown("""
            El reporte Markdown incluye:
            - Resumen ejecutivo
            - Explicación del workflow
            - Guía de métricas RAGAs
            - Análisis detallado por modelo
            - Conclusiones y recomendaciones
            """)
            
            if st.button("📄 Generar Markdown", type="primary"):
                with st.spinner("Generando reporte Markdown..."):
                    markdown_content = generate_markdown_report(enriched_data, dataset, qual_stats)
                    
                    st.download_button(
                        label="⬇️ Descargar Markdown",
                        data=markdown_content,
                        file_name=f"rag_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
                st.success("✅ Markdown generado correctamente!")
        
        st.markdown("---")
        
        # Preview del reporte Markdown
        with st.expander("👁️ Vista Previa del Reporte Markdown"):
            markdown_preview = generate_markdown_report(enriched_data, dataset, qual_stats)
            st.markdown(markdown_preview)


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    main()

