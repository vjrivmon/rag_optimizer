#!/usr/bin/env python3
"""
Exporta resultados del benchmark a PDF para el cliente
Muestra tabla con preguntas, respuestas esperadas, respuestas de cada modelo y tiempos
"""

import json
import argparse
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


class PDFExporter:
    """Exporta resultados a PDF profesional"""

    def __init__(self, results_file: str, output_file: str = None):
        """
        Args:
            results_file: Ruta al archivo JSON de resultados
            output_file: Ruta del PDF de salida (opcional)
        """
        self.results_file = results_file

        # Nombre del archivo de salida
        if output_file:
            self.output_file = output_file
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.output_file = f"results/benchmark_report_{timestamp}.pdf"

        # Cargar resultados
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.metadata = data['metadata']
        self.results = data['results']

        # Estilos
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Configura estilos personalizados"""

        # Título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))

        # Texto normal pequeño
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
            fontName='Helvetica'
        ))

        # Texto para thinking de DeepSeek
        self.styles.add(ParagraphStyle(
            name='ThinkingText',
            parent=self.styles['Normal'],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor('#7f8c8d'),
            fontName='Helvetica-Oblique',
            leftIndent=10,
            rightIndent=10
        ))

    def _extract_thinking(self, response: str) -> tuple:
        """
        Extrae el pensamiento <think> de DeepSeek

        Returns:
            (thinking_text, answer_text)
        """
        if '<think>' not in response:
            return None, response

        # Extraer pensamiento
        start = response.find('<think>')
        end = response.find('</think>')

        if start != -1 and end != -1:
            thinking = response[start+7:end].strip()
            answer = response[end+8:].strip()
            return thinking, answer

        return None, response

    def _truncate_text(self, text: str, max_chars: int = 500) -> str:
        """Trunca texto si es muy largo"""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    def generate_pdf(self):
        """Genera el PDF completo"""

        print(f"📄 Generando PDF: {self.output_file}")

        # Crear documento en orientación horizontal (landscape)
        doc = SimpleDocTemplate(
            self.output_file,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        # Contenido del PDF
        story = []

        # Título
        title = Paragraph("RAG Auto-Optimizer - Informe de Evaluación", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.2*inch))

        # Metadata
        metadata_text = f"""
        <b>Fecha:</b> {self.metadata['timestamp']}<br/>
        <b>Total preguntas evaluadas:</b> {self.metadata['total_questions']}<br/>
        <b>Tiempo total:</b> {self.metadata['total_time']:.1f}s ({self.metadata['total_time']/60:.1f} minutos)<br/>
        <b>Modelos:</b> {', '.join(self.metadata['models'])}
        """
        story.append(Paragraph(metadata_text, self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        # Procesar cada pregunta
        for idx, result in enumerate(self.results, 1):
            # _create_question_section devuelve una lista de elementos
            elements = self._create_question_section(idx, result)
            story.extend(elements)  # Usar extend en lugar de append

            # Page break después de cada pregunta excepto la última
            if idx < len(self.results):
                story.append(PageBreak())

        # Build PDF
        doc.build(story)
        print(f"✅ PDF generado exitosamente: {self.output_file}")

    def _create_question_section(self, idx: int, result: dict):
        """Crea sección para una pregunta"""

        elements = []

        # Título de la pregunta
        question_title = Paragraph(
            f"<b>Pregunta {idx}:</b> {result['question']}",
            self.styles['CustomHeading']
        )
        elements.append(question_title)
        elements.append(Spacer(1, 0.1*inch))

        # Respuesta esperada
        if result.get('expected_answer'):
            expected = Paragraph(
                f"<b>Respuesta esperada:</b><br/>{self._truncate_text(result['expected_answer'], 400)}",
                self.styles['SmallText']
            )
            elements.append(expected)
            elements.append(Spacer(1, 0.15*inch))

        # Tabla de respuestas de modelos
        table_data = []

        # Cabecera
        table_data.append([
            Paragraph('<b>Modelo</b>', self.styles['SmallText']),
            Paragraph('<b>Tiempo (s)</b>', self.styles['SmallText']),
            Paragraph('<b>Respuesta</b>', self.styles['SmallText'])
        ])

        # Datos de cada modelo
        for model_name, model_data in result['models'].items():
            if not model_data.get('success', False):
                # Modelo que falló
                table_data.append([
                    Paragraph(f"<b>{model_name}</b>", self.styles['SmallText']),
                    Paragraph("N/A", self.styles['SmallText']),
                    Paragraph("<i>Error en generación</i>", self.styles['SmallText'])
                ])
                continue

            response = model_data['response']
            latency = model_data['latency']

            # Para DeepSeek, extraer thinking
            if 'deepseek' in model_name.lower():
                thinking, answer = self._extract_thinking(response)

                if thinking:
                    # Crear celda con thinking + respuesta
                    thinking_para = Paragraph(
                        f"<i>Pensamiento:</i><br/>{self._truncate_text(thinking, 300)}",
                        self.styles['ThinkingText']
                    )
                    answer_para = Paragraph(
                        f"<br/><b>Respuesta:</b><br/>{self._truncate_text(answer, 300)}",
                        self.styles['SmallText']
                    )

                    # Combinar en una lista para la celda
                    response_cell = [thinking_para, answer_para]
                else:
                    response_cell = Paragraph(
                        self._truncate_text(answer, 400),
                        self.styles['SmallText']
                    )
            else:
                # Otros modelos: solo respuesta
                response_cell = Paragraph(
                    self._truncate_text(response, 400),
                    self.styles['SmallText']
                )

            table_data.append([
                Paragraph(f"<b>{model_name}</b>", self.styles['SmallText']),
                Paragraph(f"{latency:.2f}", self.styles['SmallText']),
                response_cell
            ])

        # Crear tabla
        col_widths = [1.5*inch, 0.8*inch, 7.5*inch]  # Ajustado para landscape

        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        # Estilo de tabla
        table.setStyle(TableStyle([
            # Cabecera
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Celdas de datos
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Centrar tiempos
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),

            # Alternar colores de filas
            *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ecf0f1'))
              for i in range(2, len(table_data), 2)]
        ]))

        elements.append(table)

        return elements


def main():
    """Función principal"""

    parser = argparse.ArgumentParser(description='Exporta resultados de benchmark a PDF')
    parser.add_argument('results_file', type=str,
                       help='Archivo JSON con resultados del benchmark')
    parser.add_argument('-o', '--output', type=str, default=None,
                       help='Archivo PDF de salida (opcional)')

    args = parser.parse_args()

    # Verificar que existe el archivo
    if not os.path.exists(args.results_file):
        print(f"❌ Error: No se encuentra el archivo {args.results_file}")
        return

    try:
        # Crear exportador
        exporter = PDFExporter(args.results_file, args.output)

        # Generar PDF
        exporter.generate_pdf()

        print(f"\n🎉 PDF generado correctamente!")
        print(f"📂 Ubicación: {exporter.output_file}")

    except Exception as e:
        print(f"❌ Error al generar PDF: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
