#!/usr/bin/env python3
"""
Generador de PDF para Boceto de TFG
Convierte el Markdown del boceto a un PDF profesional
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, ListFlowable, ListItem
)
from reportlab.lib import colors
from datetime import datetime
import os
import sys

# Añadir directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def create_tfg_boceto_pdf(output_path="docs/BOCETO_TFG_RAG_OPTIMIZER.pdf"):
    """Genera el PDF del boceto del TFG"""
    
    # Configurar documento
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    # Estilo para secciones
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2980B9'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#3498DB'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#5DADE2'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para texto normal
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        leading=14
    )
    
    # Estilo para código
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=8,
        textColor=colors.HexColor('#C0392B'),
        backColor=colors.HexColor('#ECF0F1'),
        leftIndent=10,
        rightIndent=10,
        spaceBefore=6,
        spaceAfter=6
    )
    
    # Contenido del documento
    story = []
    
    # PORTADA
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("BOCETO DE TRABAJO DE FIN DE GRADO", title_style))
    story.append(Spacer(1, 1*cm))
    
    story.append(Paragraph(
        "Sistema de Generación Aumentada por Recuperación (RAG)<br/>"
        "para Automatización de Consultas FAQ<br/>"
        "en la Gestión de Voluntarios",
        subtitle_style
    ))
    
    story.append(Spacer(1, 2*cm))
    
    # Información del autor
    author_data = [
        ["Autor:", "Vicente Rivas Monferrer"],
        ["Grado:", "Ingeniería Informática"],
        ["Universidad:", "Universitat Politècnica de València"],
        ["Fecha:", "Octubre 2025"],
        ["Versión:", "1.0 (Boceto Inicial)"]
    ]
    
    author_table = Table(author_data, colWidths=[4*cm, 10*cm])
    author_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
    ]))
    
    story.append(author_table)
    story.append(PageBreak())
    
    # ÍNDICE
    story.append(Paragraph("ÍNDICE", heading1_style))
    story.append(Spacer(1, 0.5*cm))
    
    toc_items = [
        "1. Definición del Problema y Objetivos",
        "2. Diseño de Interacción y Experiencia de Usuario",
        "3. Programación Multimedia e Integración Tecnológica",
        "4. Metodología y Desarrollo del Proyecto",
        "5. Validación, Pruebas y Análisis de Resultados",
        "6. Innovación y Creatividad",
        "7. Impacto Social, Ético y Ambiental",
        "8. Documentación Técnica",
        "9. Cronograma y Planificación",
        "10. Bibliografía y Referencias"
    ]
    
    for item in toc_items:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(PageBreak())
    
    # SECCIÓN 1: DEFINICIÓN DEL PROBLEMA
    story.append(Paragraph("1. DEFINICIÓN DEL PROBLEMA Y OBJETIVOS", heading1_style))
    
    story.append(Paragraph("1.1. Contexto del Problema", heading2_style))
    story.append(Paragraph(
        "La asociación <b>Damos Nuestra Ilusión (DNI)</b> de la Universitat Politècnica de València "
        "gestiona múltiples actividades de voluntariado que incluyen Desayunos Solidarios (distribución "
        "de alimentos a personas sin hogar), COLES (refuerzo escolar), RESIS (residencias de mayores), "
        "y actividades generales de gestión.",
        body_style
    ))
    
    story.append(Paragraph(
        "Los coordinadores y voluntarios enfrentan diariamente <b>consultas repetitivas</b> sobre horarios, "
        "ubicaciones, procesos de inscripción, duración de eventos y requisitos. Esto genera:",
        body_style
    ))
    
    problemas = [
        "Saturación del staff: Responder manualmente consume tiempo valioso",
        "Información fragmentada: Datos dispersos en diferentes documentos",
        "Latencia en respuestas: Voluntarios esperan horas o días por información básica",
        "Inconsistencias: Respuestas varían según quién responda",
        "Barrera de entrada: Nuevos voluntarios se desmotivan por falta de información inmediata"
    ]
    
    for problema in problemas:
        story.append(Paragraph(f"• {problema}", body_style))
    
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("1.2. Motivación del Proyecto", heading2_style))
    story.append(Paragraph(
        "Los sistemas tradicionales de FAQ estáticos no contextualizan respuestas, requieren palabras clave "
        "exactas, no son escalables y tienen baja satisfacción de usuario. Los <b>Modelos de Lenguaje de Gran "
        "Escala (LLMs)</b> ofrecen una alternativa, pero sufren de alucinaciones, desactualización y costos elevados "
        "en APIs comerciales.",
        body_style
    ))
    
    story.append(Paragraph(
        "La arquitectura <b>RAG (Retrieval-Augmented Generation)</b> combina recuperación de información real "
        "con generación de respuestas naturales, ofreciendo:",
        body_style
    ))
    
    ventajas_rag = [
        "Recuperación: Busca información relevante en documentación real",
        "Generación: Utiliza LLMs para crear respuestas naturales y contextualizadas",
        "Verificabilidad: Cita fuentes específicas para cada respuesta",
        "Actualización: Basta con modificar documentos, no reentrenar modelos"
    ]
    
    for ventaja in ventajas_rag:
        story.append(Paragraph(f"• {ventaja}", body_style))
    
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("1.3. Objetivos del Proyecto", heading2_style))
    
    story.append(Paragraph("<b>Objetivo General</b>", heading3_style))
    story.append(Paragraph(
        "Desarrollar un <b>sistema RAG optimizado</b> que automatice la respuesta a consultas FAQ en la "
        "gestión de voluntarios de DNI, garantizando respuestas precisas, contextualizadas y verificables.",
        body_style
    ))
    
    story.append(Paragraph("<b>Objetivos Específicos</b>", heading3_style))
    
    objetivos = [
        "<b>OE1. Diseño e Implementación del Sistema RAG:</b> Implementar arquitectura RAG modular con retrieval "
        "híbrido (semántico + BM25) e integrar múltiples modelos LLM del servidor Ollama UPV.",
        
        "<b>OE2. Optimización del Rendimiento:</b> Implementar optimización bayesiana de hiperparámetros RAG, "
        "comparar rendimiento de 4 modelos LLM distintos y reducir tiempos de respuesta.",
        
        "<b>OE3. Sistema de Evaluación Robusto:</b> Implementar métricas RAGAs (Faithfulness, Context Precision, "
        "Answer Relevancy, etc.) y desarrollar métricas personalizadas adaptadas al dominio de voluntariado.",
        
        "<b>OE4. Interfaz de Usuario y Visualización:</b> Desarrollar dashboard interactivo con Streamlit para "
        "análisis cualitativo/cuantitativo e implementar exportación profesional (Excel, PDF, Markdown).",
        
        "<b>OE5. Validación Experimental:</b> Comparar rendimiento de 4 modelos LLM en 26 preguntas reales, "
        "analizar evolución del sistema a través de 3 versiones (v1.0 → v2.1) y documentar problemas críticos."
    ]
    
    for objetivo in objetivos:
        story.append(Paragraph(objetivo, body_style))
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # SECCIÓN 2: DISEÑO DE INTERACCIÓN
    story.append(Paragraph("2. DISEÑO DE INTERACCIÓN Y EXPERIENCIA DE USUARIO", heading1_style))
    
    story.append(Paragraph("2.1. Perfiles de Usuario", heading2_style))
    
    perfiles = [
        ("<b>Coordinador de Actividades:</b>", 
         "Responder consultas rápidamente sin perder tiempo. Conocimiento técnico bajo-medio. "
         "Espera respuestas precisas con citas verificables. Uso diario."),
        
        ("<b>Voluntario Nuevo:</b>", 
         "Información clara sobre cómo participar. Conocimiento técnico bajo. "
         "Espera lenguaje sencillo sin jerga técnica. Uso puntual (fase de incorporación)."),
        
        ("<b>Investigador/Evaluador:</b>", 
         "Métricas detalladas de rendimiento. Conocimiento técnico alto. "
         "Espera dashboard técnico con análisis profundo. Uso semanal (evaluación de mejoras).")
    ]
    
    for titulo, descripcion in perfiles:
        story.append(Paragraph(titulo, body_style))
        story.append(Paragraph(descripcion, body_style))
        story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("2.2. Principios de Diseño Aplicados", heading2_style))
    
    principios = [
        "Simplicidad: Interfaz minimalista sin sobrecargas visuales",
        "Transparencia: Mostrar fuentes y grado de confianza en respuestas",
        "Accesibilidad: Diseño responsive para móviles y desktop",
        "Eficiencia: Tiempos de respuesta < 15 segundos",
        "Profesionalidad: Estilo consistente tipo plataforma educativa (Moodle)"
    ]
    
    for principio in principios:
        story.append(Paragraph(f"• {principio}", body_style))
    
    story.append(PageBreak())
    
    # SECCIÓN 3: PROGRAMACIÓN MULTIMEDIA
    story.append(Paragraph("3. PROGRAMACIÓN MULTIMEDIA E INTEGRACIÓN TECNOLÓGICA", heading1_style))
    
    story.append(Paragraph("3.1. Stack Tecnológico", heading2_style))
    
    stack_data = [
        ["Componente", "Tecnología", "Versión"],
        ["Lenguaje", "Python", "3.12+"],
        ["Framework RAG", "LangChain", "0.1.0"],
        ["Vector Store", "ChromaDB", "0.4.22"],
        ["Embeddings", "sentence-transformers", "2.3.1"],
        ["Evaluación", "RAGAs", "0.1.7"],
        ["Frontend", "Streamlit", "1.31.0"],
        ["Visualización", "Plotly", "5.18.0"],
        ["Exportación", "openpyxl, reportlab", "3.1.2, 4.0.9"],
    ]
    
    stack_table = Table(stack_data, colWidths=[4*cm, 6*cm, 3*cm])
    stack_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ECF0F1'), colors.white]),
    ]))
    
    story.append(stack_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("3.2. Modelos LLM Evaluados", heading2_style))
    
    modelos_data = [
        ["Modelo", "Parámetros", "Proveedor", "Context Window"],
        ["gemma2:27b", "27B", "Google", "2048 tokens"],
        ["llama3.3:70b", "70B", "Meta", "4096 tokens"],
        ["qwen3:32b", "32B", "Alibaba", "2048 tokens"],
        ["deepseek-r1", "Variable", "DeepSeek", "2048 tokens"],
    ]
    
    modelos_table = Table(modelos_data, colWidths=[3.5*cm, 3*cm, 3*cm, 3.5*cm])
    modelos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    story.append(modelos_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph(
        "<b>Nota:</b> Todos los modelos se ejecutan en el servidor Ollama GTI-IA de la UPV, "
        "sin necesidad de API keys comerciales.",
        body_style
    ))
    
    story.append(PageBreak())
    
    # SECCIÓN 4: METODOLOGÍA
    story.append(Paragraph("4. METODOLOGÍA Y DESARROLLO DEL PROYECTO", heading1_style))
    
    story.append(Paragraph("4.1. Enfoque de Desarrollo", heading2_style))
    story.append(Paragraph(
        "Se adoptó una metodología de <b>desarrollo iterativo incremental</b> con evaluación continua. "
        "El proyecto se desarrolló en 6 días intensivos (07-12 de octubre de 2025), generando 15 commits "
        "distribuidos en 5 fases principales.",
        body_style
    ))
    
    story.append(Paragraph("4.2. Evolución del Sistema", heading2_style))
    
    evolucion_data = [
        ["Versión", "Fecha", "Score", "Mejora", "Característica Principal"],
        ["v1.0", "07/10", "0.770", "-", "RAG básico + FAISS"],
        ["v1.5", "08/10", "0.820", "+6.5%", "Hybrid Retrieval + FAQ Chunking"],
        ["v2.0", "10/10", "0.855", "+4.3%", "10 mejoras avanzadas RAG"],
        ["v2.1", "11/10", "0.855", "±0%", "Estabilización + Dashboard v3"],
    ]
    
    evolucion_table = Table(evolucion_data, colWidths=[2*cm, 2*cm, 2*cm, 2*cm, 5*cm])
    evolucion_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E67E22')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (4, 0), (4, -1), 'LEFT'),
    ]))
    
    story.append(evolucion_table)
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph(
        "<b>Mejora total:</b> +11.0% de score en 5 días de desarrollo intensivo.",
        body_style
    ))
    
    story.append(PageBreak())
    
    # SECCIÓN 5: VALIDACIÓN Y RESULTADOS
    story.append(Paragraph("5. VALIDACIÓN, PRUEBAS Y ANÁLISIS DE RESULTADOS", heading1_style))
    
    story.append(Paragraph("5.1. Dataset de Evaluación", heading2_style))
    story.append(Paragraph(
        "Se construyó un dataset de <b>26 preguntas</b> representativas, distribuidas en 4 categorías:",
        body_style
    ))
    
    dataset_stats = [
        "DESAYUNOS: 9 preguntas (34.6%) - Eventos de desayunos y cenas solidarias",
        "COLES: 10 preguntas (38.5%) - Refuerzo escolar y actividades con niños",
        "RESIS: 4 preguntas (15.4%) - Residencias y actividades con personas mayores",
        "GENERAL: 3 preguntas (11.5%) - Información administrativa y filosófica de DNI"
    ]
    
    for stat in dataset_stats:
        story.append(Paragraph(f"• {stat}", body_style))
    
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("5.2. Métricas RAGAs Implementadas", heading2_style))
    
    metricas_ragas = [
        "<b>Faithfulness:</b> Fidelidad de la respuesta al contexto recuperado (evita alucinaciones)",
        "<b>Answer Relevancy:</b> Relevancia de la respuesta para la pregunta original",
        "<b>Context Precision:</b> Proporción de chunks relevantes entre los recuperados",
        "<b>Context Recall:</b> Cobertura del contexto vs información necesaria",
        "<b>Answer Correctness:</b> Corrección factual comparada con respuesta esperada",
        "<b>Answer Similarity:</b> Similitud semántica con ground truth"
    ]
    
    for metrica in metricas_ragas:
        story.append(Paragraph(f"• {metrica}", body_style))
    
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("5.3. Resultados Comparativos de Modelos", heading2_style))
    
    resultados_data = [
        ["Modelo", "Score", "Correctas", "Incompletas", "Incorrectas", "Tiempo (s)"],
        ["gemma2:27b", "0.855", "22/26 (84.6%)", "3/26 (11.5%)", "1/26 (3.8%)", "8.5"],
        ["qwen3:32b", "0.834", "17/26 (65.4%)", "6/26 (23.1%)", "3/26 (11.5%)", "12.3"],
        ["llama3.3:70b", "0.824", "20/26 (76.9%)", "4/26 (15.4%)", "2/26 (7.7%)", "18.7"],
        ["deepseek-r1", "0.617", "10/26 (38.5%)", "8/26 (30.8%)", "8/26 (30.8%)", "10.2"],
    ]
    
    resultados_table = Table(resultados_data, colWidths=[3*cm, 2*cm, 3*cm, 3*cm, 3*cm, 2*cm])
    resultados_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9B59B6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#D5F4E6')),  # Highlight mejor modelo
    ]))
    
    story.append(resultados_table)
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph(
        "<b>Conclusión:</b> gemma2:27b es el mejor modelo individual con el mejor balance score/tiempo "
        "y mayor consistencia (84.6% de preguntas correctas).",
        body_style
    ))
    
    story.append(PageBreak())
    
    # SECCIÓN 6: INNOVACIÓN
    story.append(Paragraph("6. INNOVACIÓN Y CREATIVIDAD", heading1_style))
    
    story.append(Paragraph("6.1. Aspectos Innovadores del Proyecto", heading2_style))
    
    innovaciones = [
        ("<b>Arquitectura RAG Híbrida Optimizada:</b>", 
         "Combinación de retrieval semántico (ChromaDB) + keyword (BM25) con pesos optimizados "
         "empíricamente (60% semantic, 40% keyword). Mejora de +6.5% sobre retrieval semántico puro."),
        
        ("<b>Sistema de Evaluación sin API Keys Comerciales:</b>", 
         "RAGAs funcionando completamente con Ollama local (sin OpenAI/Anthropic). Coste $0 vs "
         "~$50-100 por benchmark con GPT-4. Privacidad total: datos nunca salen de infraestructura UPV."),
        
        ("<b>Dashboard de Análisis Cualitativo Automático:</b>", 
         "Evaluación automática Correcta/Incompleta/Incorrecta mediante heurísticas inteligentes. "
         "Reduce evaluación manual de ~4 horas a 5 minutos."),
        
        ("<b>Query Expansion con Sinónimos de Dominio:</b>", 
         "Diccionario específico de términos DNI UPV ('resis' → 'residencias', 'coles' → 'refuerzo escolar'). "
         "Mejora retrieval en +15% para preguntas con jerga específica."),
        
        ("<b>FAQ-Aware Chunking:</b>", 
         "Chunking que preserva pares pregunta-respuesta juntos, evitando cortar Q&A por la mitad. "
         "Mejora de +3% en preguntas tipo FAQ literal.")
    ]
    
    for titulo, descripcion in innovaciones:
        story.append(Paragraph(titulo, body_style))
        story.append(Paragraph(descripcion, body_style))
        story.append(Spacer(1, 0.4*cm))
    
    story.append(PageBreak())
    
    # SECCIÓN 7: IMPACTO
    story.append(Paragraph("7. IMPACTO SOCIAL, ÉTICO Y AMBIENTAL", heading1_style))
    
    story.append(Paragraph("7.1. Impacto Social", heading2_style))
    
    story.append(Paragraph("<b>Beneficiarios Directos:</b>", heading3_style))
    
    beneficiarios = [
        "Coordinadores de DNI (~15 personas): Ahorro de ~10 horas/semana respondiendo consultas",
        "Voluntarios Activos (~200 personas): Acceso inmediato a información, mayor autonomía",
        "Voluntarios Potenciales (~1000 contactos/año): Reducción de barrera de entrada, onboarding más rápido"
    ]
    
    for beneficiario in beneficiarios:
        story.append(Paragraph(f"• {beneficiario}", body_style))
    
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>Replicabilidad:</b>", heading3_style))
    story.append(Paragraph(
        "El sistema es completamente open-source (licencia MIT), sin dependencias de APIs de pago, "
        "y con documentación exhaustiva. Potenciales adoptantes: ~50 asociaciones de voluntariado "
        "universitario en España, ONGs con gestión de FAQ intensiva, plataformas de voluntariado nacional.",
        body_style
    ))
    
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("7.2. Consideraciones Éticas", heading2_style))
    
    etica_decisiones = [
        "No almacenamiento de PII (información personal identificable)",
        "Procesamiento local en Ollama UPV (infraestructura europea, GDPR-compliant)",
        "Sin tracking de usuarios en el dashboard",
        "Datos del benchmark anonimizados (solo preguntas genéricas)",
        "Citación de fuentes: Cada respuesta incluye chunks recuperados con scores",
        "Transparencia: Sistema indica claramente cuando no tiene información"
    ]
    
    for decision in etica_decisiones:
        story.append(Paragraph(f"✓ {decision}", body_style))
    
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("7.3. Impacto Ambiental", heading2_style))
    
    story.append(Paragraph(
        "<b>Huella de carbono estimada:</b> ~30 kg CO2e/año (inferencia en servidor compartido). "
        "<b>Balance neto:</b> -18 kg CO2e/año (positivo), ya que se ahorran ~48 kg CO2e/año por "
        "emails evitados (1000 consultas/mes × 4g CO2e/email).",
        body_style
    ))
    
    story.append(PageBreak())
    
    # SECCIÓN 8: DOCUMENTACIÓN TÉCNICA
    story.append(Paragraph("8. DOCUMENTACIÓN TÉCNICA", heading1_style))
    
    story.append(Paragraph("8.1. Requisitos del Sistema", heading2_style))
    
    requisitos = [
        "<b>Hardware:</b> CPU 4 cores, RAM 8GB mínimo (16GB recomendado), 10GB almacenamiento",
        "<b>Software:</b> Python 3.12+, pip 22.0+, git 2.30+",
        "<b>Red:</b> Conexión estable a servidor Ollama UPV"
    ]
    
    for req in requisitos:
        story.append(Paragraph(f"• {req}", body_style))
    
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("8.2. Instalación Rápida", heading2_style))
    
    instalacion_code = """
# 1. Clonar repositorio
git clone https://github.com/vicenteR/rag_optimizer.git
cd rag_optimizer

# 2. Crear entorno virtual
python3.12 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear vector store
python scripts/01_create_vector_store_chroma.py

# 5. Lanzar dashboard
streamlit run app_v3.py
"""
    
    story.append(Paragraph(instalacion_code, code_style))
    
    story.append(PageBreak())
    
    # SECCIÓN 9: CRONOGRAMA
    story.append(Paragraph("9. CRONOGRAMA Y PLANIFICACIÓN", heading1_style))
    
    story.append(Paragraph("9.1. Cronograma Real del Desarrollo (Octubre 2025)", heading2_style))
    
    cronograma_data = [
        ["Día", "Fecha", "Fase", "Horas", "Commits"],
        ["1", "07/10", "Investigación + Prototipo v1.0", "12h", "5"],
        ["2", "08/10", "Optimización inicial", "10h", "3"],
        ["3", "09/10", "Crisis técnica + Solución", "6h", "1"],
        ["4", "10/10", "RAG v2.0 completo", "12h", "4"],
        ["5", "11/10", "Consolidación v2.1", "8h", "2"],
        ["6", "12/10", "Documentación exhaustiva", "6h", "1"],
        ["", "", "<b>TOTAL</b>", "<b>54h</b>", "<b>16</b>"],
    ]
    
    cronograma_table = Table(cronograma_data, colWidths=[1.5*cm, 2*cm, 5*cm, 2*cm, 2*cm])
    cronograma_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1ABC9C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#ECF0F1')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D5F4E6')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(cronograma_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("9.2. Cronograma Propuesto para TFG Completo (4 Meses)", heading2_style))
    
    tfg_cronograma = [
        ["Mes", "Fase", "Entregables"],
        ["1", "Estado del Arte + Diseño", "Cap. 2 (Marco Teórico) + Cap. 3 (Análisis y Diseño)"],
        ["2", "Implementación + Optimización", "Código funcional v1.0 + v2.0"],
        ["3", "Evaluación + Dashboard", "Cap. 5 (Validación) + Dashboard v3"],
        ["4", "Documentación + Defensa", "Memoria TFG + Presentación"],
    ]
    
    tfg_table = Table(tfg_cronograma, colWidths=[2*cm, 5*cm, 6*cm])
    tfg_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E74C3C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (1, 0), (2, -1), 'LEFT'),
    ]))
    
    story.append(tfg_table)
    
    story.append(PageBreak())
    
    # SECCIÓN 10: BIBLIOGRAFÍA
    story.append(Paragraph("10. BIBLIOGRAFÍA Y REFERENCIAS", heading1_style))
    
    story.append(Paragraph("10.1. Referencias Académicas Principales", heading2_style))
    
    referencias = [
        "[1] Lewis, P., et al. (2020). <i>Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks</i>. Proceedings of NeurIPS 2020.",
        "[2] Guu, K., et al. (2020). <i>REALM: Retrieval-Augmented Language Model Pre-Training</i>. Proceedings of ICML 2020.",
        "[3] Es, S., et al. (2023). <i>RAGAs: Automated Evaluation of Retrieval Augmented Generation</i>. arXiv preprint.",
        "[4] Reimers, N., & Gurevych, I. (2019). <i>Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks</i>. Proceedings of EMNLP 2019.",
        "[5] Touvron, H., et al. (2023). <i>Llama 2: Open Foundation and Fine-Tuned Chat Models</i>. arXiv preprint.",
        "[6] Team, G., et al. (2024). <i>Gemma 2: Improving Open Language Models at a Practical Size</i>. arXiv preprint.",
        "[7] Bai, J., et al. (2023). <i>Qwen Technical Report</i>. arXiv preprint.",
    ]
    
    for ref in referencias:
        story.append(Paragraph(ref, body_style))
        story.append(Spacer(1, 0.2*cm))
    
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("10.2. Frameworks y Herramientas", heading2_style))
    
    herramientas = [
        "[8] LangChain Documentation. https://python.langchain.com/",
        "[9] ChromaDB Documentation. https://docs.trychroma.com/",
        "[10] RAGAs Framework. https://docs.ragas.io/",
        "[11] Streamlit Documentation. https://docs.streamlit.io/",
        "[12] Ollama Documentation. https://ollama.ai/",
    ]
    
    for herr in herramientas:
        story.append(Paragraph(herr, body_style))
        story.append(Spacer(1, 0.2*cm))
    
    story.append(PageBreak())
    
    # PÁGINA FINAL
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph("FIN DEL BOCETO DEL TFG", title_style))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "Este documento es un boceto inicial sujeto a revisión y ampliación<br/>"
        "durante el desarrollo del Trabajo de Fin de Grado.",
        subtitle_style
    ))
    
    story.append(Spacer(1, 2*cm))
    
    contacto_text = """
<b>Contacto:</b><br/>
Vicente Rivas Monferrer<br/>
vicente.rivas@upv.edu.es<br/>
Universitat Politècnica de València<br/>
Grado en Ingeniería Informática<br/><br/>

<b>Fecha de elaboración:</b> 16 de Octubre de 2025<br/>
<b>Versión del documento:</b> 1.0 (Boceto Inicial)
"""
    
    story.append(Paragraph(contacto_text, body_style))
    
    # Generar PDF
    doc.build(story)
    print(f"✅ PDF generado exitosamente: {output_path}")
    return output_path


if __name__ == "__main__":
    output_file = create_tfg_boceto_pdf()
    print(f"\n📄 Documento PDF completo:")
    print(f"   Ubicación: {output_file}")
    print(f"   Tamaño: {os.path.getsize(output_file) / 1024:.1f} KB")
    print("\n✅ ¡Boceto del TFG exportado a PDF correctamente!")

