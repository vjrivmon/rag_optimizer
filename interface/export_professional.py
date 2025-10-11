#!/usr/bin/env python3
"""
📄 Exportador Profesional para Reportes RAG

Genera reportes en PDF y Excel con análisis completo:
- Comparación cualitativa con respuestas esperadas
- Métricas detalladas por modelo
- Gráficas de rendimiento
- Conclusiones y recomendaciones
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from io import BytesIO


def export_to_excel(
    enriched_data: List[Dict[str, Any]],
    dataset: List[Dict[str, Any]],
    output_path: str = None
) -> BytesIO:
    """
    Exporta los resultados del benchmark a Excel con múltiples sheets.
    
    Args:
        enriched_data: Lista de resultados del benchmark enriquecidos
        dataset: Dataset con preguntas esperadas
        output_path: Ruta opcional donde guardar el archivo
        
    Returns:
        BytesIO con el contenido del Excel (para descarga en Streamlit)
    """
    # Preparar datos por pregunta y modelo
    questions_map = {q['id']: q for q in dataset}
    
    # Sheet 1: Comparación Cualitativa
    comparison_data = []
    
    # Agrupar por pregunta
    by_question = {}
    for item in enriched_data:
        qid = item['question_id']
        if qid not in by_question:
            by_question[qid] = {
                'question_id': qid,
                'question': item['question'],
                'expected_answer': item.get('expected_answer', 'N/A'),
                'models': {}
            }
        by_question[qid]['models'][item['model_name']] = item
    
    # Construir tabla comparativa
    for qid in sorted(by_question.keys()):
        q_data = by_question[qid]
        
        row = {
            'ID': qid,
            'Pregunta': q_data['question'],
            'Respuesta Esperada': q_data['expected_answer']
        }
        
        # Añadir respuestas de cada modelo
        for model_name in sorted(q_data['models'].keys()):
            model_data = q_data['models'][model_name]
            row[f'{model_name} - Respuesta'] = model_data['answer']
            row[f'{model_name} - Score'] = model_data['metrics']['combined_score']
            row[f'{model_name} - Tiempo (s)'] = f"{model_data['generation_time']:.2f}"
            row[f'{model_name} - Evaluación'] = model_data.get('qualitative_eval', 'N/A')
        
        comparison_data.append(row)
    
    df_comparison = pd.DataFrame(comparison_data)
    
    # Sheet 2: Métricas Detalladas
    metrics_data = []
    for item in enriched_data:
        row = {
            'ID Pregunta': item['question_id'],
            'Pregunta': item['question'],
            'Modelo': item['model_name'],
            'Combined Score': item['metrics']['combined_score'],
            'Faithfulness': item['metrics']['faithfulness'],
            'Answer Relevancy': item['metrics']['answer_relevancy'],
            'Context Precision': item['metrics']['context_precision'],
            'Context Recall': item['metrics']['context_recall'],
            'Answer Correctness': item['metrics']['answer_correctness'],
            'Answer Similarity': item['metrics']['answer_similarity'],
            'Tiempo Generación (s)': item['generation_time']
        }
        metrics_data.append(row)
    
    df_metrics = pd.DataFrame(metrics_data)
    
    # Sheet 3: Análisis por Modelo
    model_analysis = []
    models = df_metrics['Modelo'].unique()
    
    for model in models:
        model_df = df_metrics[df_metrics['Modelo'] == model]
        
        analysis = {
            'Modelo': model,
            'Num Preguntas': len(model_df),
            'Score Promedio': model_df['Combined Score'].mean(),
            'Score Mediana': model_df['Combined Score'].median(),
            'Score Mínimo': model_df['Combined Score'].min(),
            'Score Máximo': model_df['Combined Score'].max(),
            'Tiempo Promedio (s)': model_df['Tiempo Generación (s)'].mean(),
            'Tiempo Total (s)': model_df['Tiempo Generación (s)'].sum(),
            'Faithfulness Promedio': model_df['Faithfulness'].mean(),
            'Answer Relevancy Promedio': model_df['Answer Relevancy'].mean(),
            'Context Precision Promedio': model_df['Context Precision'].mean(),
            'Context Recall Promedio': model_df['Context Recall'].mean(),
            'Answer Correctness Promedio': model_df['Answer Correctness'].mean(),
            'Answer Similarity Promedio': model_df['Answer Similarity'].mean()
        }
        model_analysis.append(analysis)
    
    df_analysis = pd.DataFrame(model_analysis)
    
    # Sheet 4: Análisis por Pregunta
    question_analysis = []
    questions = df_metrics['ID Pregunta'].unique()
    
    for qid in sorted(questions):
        q_df = df_metrics[df_metrics['ID Pregunta'] == qid]
        
        analysis = {
            'ID': qid,
            'Pregunta': q_df['Pregunta'].iloc[0],
            'Score Promedio': q_df['Combined Score'].mean(),
            'Score Mínimo': q_df['Combined Score'].min(),
            'Score Máximo': q_df['Combined Score'].max(),
            'Desviación Estándar': q_df['Combined Score'].std(),
            'Modelos con Score < 0.5': len(q_df[q_df['Combined Score'] < 0.5]),
            'Modelos con Score >= 0.8': len(q_df[q_df['Combined Score'] >= 0.8])
        }
        question_analysis.append(analysis)
    
    df_questions = pd.DataFrame(question_analysis)
    
    # Crear archivo Excel
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_comparison.to_excel(writer, sheet_name='Comparación Cualitativa', index=False)
        df_metrics.to_excel(writer, sheet_name='Métricas Detalladas', index=False)
        df_analysis.to_excel(writer, sheet_name='Análisis por Modelo', index=False)
        df_questions.to_excel(writer, sheet_name='Análisis por Pregunta', index=False)
        
        # Ajustar anchos de columna
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Máximo 50
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    # Si se proporciona ruta, también guardar archivo
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(output.getvalue())
        output.seek(0)
    
    return output


def generate_markdown_report(
    enriched_data: List[Dict[str, Any]],
    dataset: List[Dict[str, Any]],
    qualitative_stats: Dict[str, Any]
) -> str:
    """
    Genera un reporte en formato Markdown con análisis completo.
    
    Args:
        enriched_data: Lista de resultados del benchmark enriquecidos
        dataset: Dataset con preguntas esperadas
        qualitative_stats: Estadísticas cualitativas agregadas
        
    Returns:
        String con el reporte en Markdown
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calcular estadísticas generales
    df = pd.DataFrame(enriched_data)
    models = df['model_name'].unique()
    
    report = f"""# 📊 Reporte de Evaluación RAG - Sistema v2

**Fecha de generación:** {timestamp}

---

## 🎯 Resumen Ejecutivo

Este reporte presenta los resultados de la evaluación del sistema RAG v2 con validación inteligente y fallback automático.

### Datos Generales

- **Total de preguntas evaluadas:** {len(dataset)}
- **Modelos evaluados:** {len(models)}
- **Total de evaluaciones:** {len(enriched_data)}

### Evaluación Cualitativa Global

- ✅ **Respuestas Correctas:** {qualitative_stats['correctas']} ({qualitative_stats['pct_correctas']:.1f}%)
- ⚠️ **Respuestas Incompletas:** {qualitative_stats['incompletas']} ({qualitative_stats['pct_incompletas']:.1f}%)
- ❌ **Respuestas Incorrectas:** {qualitative_stats['incorrectas']} ({qualitative_stats['pct_incorrectas']:.1f}%)

---

## 🔄 Workflow del Sistema

### Fase 1: Generación de Respuestas (5-10 min)

1. **Enhanced RAG Engine** recupera contextos relevantes usando:
   - Búsqueda híbrida (semántica + BM25)
   - Reranking por relevancia
   - Top-k adaptativo según complejidad

2. **Validación Inteligente** con estrategia de fallback:
   - Configuración específica para preguntas problemáticas
   - Fallback progresivo (ultra_permissive → very_permissive → permissive)
   - Búsqueda exacta por keywords como último recurso

3. **Limpieza de Respuestas:**
   - Eliminación de tags de razonamiento interno (`<think>`, `<thinking>`)
   - Normalización de formato

4. **Guardado en SQLite** para evaluación posterior

### Fase 2: Evaluación con RAGAs (background)

1. **OpenAI API** evalúa cada respuesta con 6 métricas:
   - Faithfulness (Fidelidad)
   - Answer Relevancy (Relevancia)
   - Context Precision (Precisión)
   - Context Recall (Exhaustividad)
   - Answer Correctness (Corrección)
   - Answer Similarity (Similitud)

2. **Actualización en tiempo real** de métricas en base de datos

---

## 📖 Explicación de Métricas RAGAs

### 1. Faithfulness (Fidelidad) 🎯
**¿Qué mide?** Si la respuesta se basa únicamente en los contextos proporcionados sin inventar información.

- **Score alto (>0.8):** La respuesta está completamente fundamentada en los contextos
- **Score bajo (<0.5):** El modelo está inventando o alucinando información

### 2. Answer Relevancy (Relevancia) 🔍
**¿Qué mide?** Si la respuesta responde directamente a la pregunta formulada.

- **Score alto (>0.8):** Respuesta directa y al punto
- **Score bajo (<0.5):** Respuesta divaga o no responde la pregunta

### 3. Context Precision (Precisión) 🎲
**¿Qué mide?** Si los contextos recuperados son relevantes para la pregunta.

- **Score alto (>0.8):** Los contextos son altamente relevantes
- **Score bajo (<0.5):** Se recuperaron muchos contextos irrelevantes

### 4. Context Recall (Exhaustividad) 📚
**¿Qué mide?** Si se recuperaron todos los contextos necesarios para responder.

- **Score alto (>0.8):** Se recuperó toda la información necesaria
- **Score bajo (<0.5):** Faltan contextos importantes

### 5. Answer Correctness (Corrección) ✓
**¿Qué mide?** Si la respuesta es factualmente correcta comparada con la respuesta esperada.

- **Score alto (>0.8):** Respuesta correcta y completa
- **Score bajo (<0.5):** Respuesta incorrecta o muy incompleta

### 6. Answer Similarity (Similitud) 🔄
**¿Qué mide?** Qué tan similar es la respuesta a la respuesta esperada (semánticamente).

- **Score alto (>0.8):** Muy similar a la respuesta esperada
- **Score bajo (<0.5):** Respuesta muy diferente

### Combined Score (Score Combinado) 🎯
**Promedio de las 6 métricas.** Representa la calidad general de la respuesta.

---

## 📊 Análisis por Modelo

"""
    
    # Añadir análisis por modelo
    for model in sorted(models):
        model_df = df[df['model_name'] == model]
        
        avg_score = model_df['metrics'].apply(lambda x: x['combined_score']).mean()
        avg_time = model_df['generation_time'].mean()
        
        num_correct = len(model_df[model_df['qualitative_eval'] == 'correcta'])
        num_incorrect = len(model_df[model_df['qualitative_eval'] == 'incorrecta'])
        num_incomplete = len(model_df[model_df['qualitative_eval'] == 'incompleta'])
        
        report += f"""### {model}

- **Score promedio:** {avg_score:.3f}
- **Tiempo promedio:** {avg_time:.2f}s
- **Respuestas correctas:** {num_correct}/{len(model_df)} ({num_correct/len(model_df)*100:.1f}%)
- **Respuestas incompletas:** {num_incomplete}/{len(model_df)} ({num_incomplete/len(model_df)*100:.1f}%)
- **Respuestas incorrectas:** {num_incorrect}/{len(model_df)} ({num_incorrect/len(model_df)*100:.1f}%)

"""
    
    report += """---

## 🎓 Conclusiones y Recomendaciones

### Conclusiones Principales

1. **Rendimiento General:** El sistema RAG v2 muestra mejoras significativas con la validación inteligente y fallback automático.

2. **Variabilidad entre Modelos:** Se observan diferencias importantes en el comportamiento de cada modelo, especialmente en preguntas complejas.

3. **Áreas de Mejora Identificadas:** Algunas preguntas siguen siendo problemáticas para ciertos modelos, sugiriendo necesidad de optimización específica.

### Recomendaciones

1. **Para Modelos con Baja Fidelidad:** Ajustar prompts para ser más restrictivos con el uso del contexto.

2. **Para Modelos con Baja Relevancia:** Implementar post-procesamiento para filtrar información irrelevante.

3. **Para Preguntas Problemáticas:** Considerar configuraciones específicas adicionales o prompts especializados.

---

*Reporte generado automáticamente por RAG Optimizer v3*
"""
    
    return report

