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
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend sin interfaz gráfica


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
   - Eliminación de tags de razonamiento interno (`</think>`, `<thinking>`)
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


def export_to_pdf(
    enriched_data: List[Dict[str, Any]],
    dataset: List[Dict[str, Any]],
    qualitative_stats: Dict[str, Any]
) -> BytesIO:
    """
    Genera un PDF profesional con todas las métricas y respuestas esperadas.
    
    Args:
        enriched_data: Lista de resultados del benchmark enriquecidos
        dataset: Dataset con preguntas esperadas
        qualitative_stats: Estadísticas cualitativas agregadas
        
    Returns:
        BytesIO con el contenido del PDF profesional
    """
    buffer = BytesIO()
    
    # FORMATO APAISADO para tablas anchas
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    # Estilos profesionales
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Estilo especial para texto en celdas con word wrap
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        alignment=TA_LEFT,
        fontName='Helvetica',
        wordWrap='CJK'  # Permite word wrap
    )
    
    # Preparar datos
    df = pd.DataFrame(enriched_data)
    models = sorted(df['model_name'].unique())
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    story = []
    
    # ===== PORTADA =====
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("INFORME DE EVALUACIÓN RAG - SISTEMA v3.1", title_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"<b>Fecha:</b> {timestamp} | <b>Preguntas:</b> {len(dataset)} | <b>Modelos:</b> {len(models)}", 
        ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9)
    ))
    story.append(Spacer(1, 1*cm))
    
    # Resumen ejecutivo compacto
    summary_data = [
        ['MÉTRICA', 'VALOR'],
        ['Correctas', f"{qualitative_stats['correctas']} ({qualitative_stats['pct_correctas']:.1f}%)"],
        ['Incompletas', f"{qualitative_stats['incompletas']} ({qualitative_stats['pct_incompletas']:.1f}%)"],
        ['Incorrectas', f"{qualitative_stats['incorrectas']} ({qualitative_stats['pct_incorrectas']:.1f}%)"]
    ]
    
    summary_table = Table(summary_data, colWidths=[6*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    story.append(summary_table)
    story.append(PageBreak())
    
    # ===== TABLA 1: RENDIMIENTO POR MODELO =====
    story.append(Paragraph("RENDIMIENTO GENERAL POR MODELO", heading_style))
    story.append(Spacer(1, 0.2*cm))
    
    model_data = [['Modelo', 'Score', 'Faith.', 'Relev.', 'Precis.', 'Recall', 'Correct.', 'Simil.', 'Tiempo', 'OK', 'Incomp.', 'Error']]
    
    for model in models:
        model_df = df[df['model_name'] == model]
        metrics_avg = {
            'combined_score': model_df['metrics'].apply(lambda x: x['combined_score']).mean(),
            'faithfulness': model_df['metrics'].apply(lambda x: x['faithfulness']).mean(),
            'answer_relevancy': model_df['metrics'].apply(lambda x: x['answer_relevancy']).mean(),
            'context_precision': model_df['metrics'].apply(lambda x: x['context_precision']).mean(),
            'context_recall': model_df['metrics'].apply(lambda x: x['context_recall']).mean(),
            'answer_correctness': model_df['metrics'].apply(lambda x: x['answer_correctness']).mean(),
            'answer_similarity': model_df['metrics'].apply(lambda x: x['answer_similarity']).mean()
        }
        avg_time = model_df['generation_time'].mean()
        
        num_correct = len(model_df[model_df['qualitative_eval'] == 'correcta'])
        num_incomplete = len(model_df[model_df['qualitative_eval'] == 'incompleta'])
        num_incorrect = len(model_df[model_df['qualitative_eval'] == 'incorrecta'])
        
        model_data.append([
            model,
            f"{metrics_avg['combined_score']:.2f}",
            f"{metrics_avg['faithfulness']:.2f}",
            f"{metrics_avg['answer_relevancy']:.2f}",
            f"{metrics_avg['context_precision']:.2f}",
            f"{metrics_avg['context_recall']:.2f}",
            f"{metrics_avg['answer_correctness']:.2f}",
            f"{metrics_avg['answer_similarity']:.2f}",
            f"{avg_time:.1f}s",
            str(num_correct),
            str(num_incomplete),
            str(num_incorrect)
        ])
    
    model_table = Table(model_data, colWidths=[3*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.2*cm, 1.5*cm, 1.2*cm])
    model_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    
    story.append(model_table)
    story.append(PageBreak())
    
    # ===== TABLA 2: COMPARATIVA DETALLADA POR PREGUNTA =====
    story.append(Paragraph("COMPARATIVA DETALLADA: PREGUNTAS 1-26", heading_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Agrupar por pregunta
    by_question = {}
    for item in enriched_data:
        qid = item['question_id']
        if qid not in by_question:
            by_question[qid] = {
                'question': item['question'],
                'expected_answer': item.get('expected_answer', 'N/A'),
                'models': {}
            }
        by_question[qid]['models'][item['model_name']] = item
    
    # Crear tabla grande con TODAS las columnas
    for qid in sorted(by_question.keys()):
        q_data = by_question[qid]
        
        # Título de pregunta con fondo
        title_data = [[f"PREGUNTA {qid}: {q_data['question']}"]]
        title_table = Table(title_data, colWidths=[25*cm])
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5)
        ]))
        story.append(title_table)
        story.append(Spacer(1, 0.1*cm))
        
        # TABLA CON RESPUESTA ESPERADA + RESPUESTAS DE MODELOS
        table_data = [['Modelo', 'Respuesta Esperada / Respuesta del Modelo', 'Score', 'Tiempo']]
        
        # Primera fila: Respuesta esperada
        expected_para = Paragraph(q_data['expected_answer'], cell_style)
        table_data.append([
            Paragraph('<b>ESPERADA</b>', ParagraphStyle('Bold', parent=cell_style, fontName='Helvetica-Bold')),
            expected_para,
            '-',
            '-'
        ])
        
        # Filas de modelos
        for model_name in models:
            if model_name in q_data['models']:
                model_item = q_data['models'][model_name]
                answer_para = Paragraph(model_item['answer'], cell_style)
                
                table_data.append([
                    Paragraph(f'<b>{model_name}</b>', ParagraphStyle('Bold', parent=cell_style, fontName='Helvetica-Bold')),
                    answer_para,
                    f"{model_item['metrics']['combined_score']:.2f}",
                    f"{model_item['generation_time']:.1f}s"
                ])
        
        # Crear tabla con word wrap
        detail_table = Table(table_data, colWidths=[3*cm, 17.5*cm, 2*cm, 2.5*cm])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fff5e1')),  # Fondo amarillo claro para esperada
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTSIZE', (2, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 2), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(detail_table)
        story.append(Spacer(1, 0.4*cm))
        
        # Page break cada 2 preguntas para mejor distribución
        if qid % 2 == 0 and qid < max(by_question.keys()):
            story.append(PageBreak())
    
    # ===== CONCLUSIONES =====
    story.append(PageBreak())
    story.append(Paragraph("CONCLUSIONES", heading_style))
    story.append(Paragraph(
        f"El sistema evaluó {len(dataset)} preguntas con {len(models)} modelos LLM. "
        f"Precisión global: {qualitative_stats['pct_correctas']:.1f}%. "
        f"Tiempo promedio: {df['generation_time'].mean():.1f}s.",
        ParagraphStyle('Normal', parent=styles['Normal'], fontSize=9)
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"<i>Generado el {timestamp} por RAG Optimizer v3.1</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER)
    ))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer


# Código obsoleto eliminado - usar export_to_pdf() directamente