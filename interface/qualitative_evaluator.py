#!/usr/bin/env python3
"""
🎯 Evaluador Cualitativo para Respuestas RAG

Clasifica las respuestas en:
- ✅ Correcta: Respuesta completa y precisa
- ⚠️ Incompleta: Respuesta parcial o poco clara
- ❌ Incorrecta: Respuesta errónea o sin información
"""

from typing import Dict, Literal

QualitativeResult = Literal['correcta', 'incompleta', 'incorrecta']


def evaluate_qualitative(
    answer: str,
    expected: str,
    metrics: Dict[str, float]
) -> tuple[QualitativeResult, str]:
    """
    Evalúa cualitativamente una respuesta comparándola con la esperada.
    
    Args:
        answer: Respuesta generada por el modelo
        expected: Respuesta esperada del dataset
        metrics: Métricas RAGAs de la respuesta
        
    Returns:
        (resultado, explicación) donde resultado es 'correcta', 'incompleta' o 'incorrecta'
        
    Criterios:
        - Correcta: combined_score >= 0.8 y no contiene frases de rechazo
        - Incorrecta: combined_score < 0.3 o contiene frases de rechazo
        - Incompleta: 0.3 <= combined_score < 0.8
    """
    answer_lower = answer.lower()
    combined_score = metrics.get('combined_score', 0.0)
    
    # Frases que indican que el modelo no puede responder
    rejection_phrases = [
        'no hay información',
        'no está disponible',
        'no se encuentra',
        'no dispongo',
        'no puedo responder',
        'no menciona',
        'no se especifica',
        'información no disponible'
    ]
    
    # Verificar si la respuesta contiene frases de rechazo
    has_rejection = any(phrase in answer_lower for phrase in rejection_phrases)
    
    # Clasificación basada en score y contenido
    if has_rejection:
        return 'incorrecta', 'Modelo indica que no tiene información (pero podría estar en el contexto)'
    
    if combined_score >= 0.8:
        return 'correcta', f'Score alto ({combined_score:.2f}) - Respuesta completa y precisa'
    
    elif combined_score < 0.3:
        return 'incorrecta', f'Score muy bajo ({combined_score:.2f}) - Respuesta errónea o sin fundamento'
    
    else:
        # Análisis más detallado para rango medio
        faithfulness = metrics.get('faithfulness', 0.0)
        relevancy = metrics.get('answer_relevancy', 0.0)
        correctness = metrics.get('answer_correctness', 0.0)
        
        if faithfulness < 0.5:
            return 'incorrecta', f'Baja fidelidad ({faithfulness:.2f}) - Respuesta inventa información'
        
        if relevancy < 0.5:
            return 'incompleta', f'Baja relevancia ({relevancy:.2f}) - Respuesta no directa'
        
        if correctness < 0.5:
            return 'incompleta', f'Baja corrección ({correctness:.2f}) - Respuesta parcialmente correcta'
        
        return 'incompleta', f'Score medio ({combined_score:.2f}) - Respuesta parcial o incompleta'


def get_evaluation_icon(result: QualitativeResult) -> str:
    """Retorna el icono correspondiente al resultado cualitativo"""
    icons = {
        'correcta': '✅',
        'incompleta': '⚠️',
        'incorrecta': '❌'
    }
    return icons.get(result, '❓')


def get_evaluation_color(result: QualitativeResult) -> str:
    """Retorna el color correspondiente al resultado cualitativo"""
    colors = {
        'correcta': '#28a745',   # Verde
        'incompleta': '#ffc107',  # Amarillo
        'incorrecta': '#dc3545'   # Rojo
    }
    return colors.get(result, '#6c757d')  # Gris por defecto


def calculate_qualitative_stats(evaluations: list[QualitativeResult]) -> Dict[str, any]:
    """
    Calcula estadísticas agregadas de evaluaciones cualitativas.
    
    Args:
        evaluations: Lista de resultados cualitativos
        
    Returns:
        Diccionario con estadísticas (total, correctas, incorrectas, incompletas, porcentajes)
    """
    total = len(evaluations)
    
    if total == 0:
        return {
            'total': 0,
            'correctas': 0,
            'incorrectas': 0,
            'incompletas': 0,
            'pct_correctas': 0.0,
            'pct_incorrectas': 0.0,
            'pct_incompletas': 0.0
        }
    
    correctas = evaluations.count('correcta')
    incorrectas = evaluations.count('incorrecta')
    incompletas = evaluations.count('incompleta')
    
    return {
        'total': total,
        'correctas': correctas,
        'incorrectas': incorrectas,
        'incompletas': incompletas,
        'pct_correctas': (correctas / total) * 100,
        'pct_incorrectas': (incorrectas / total) * 100,
        'pct_incompletas': (incompletas / total) * 100
    }


def format_qualitative_summary(stats: Dict[str, any]) -> str:
    """
    Formatea un resumen legible de las estadísticas cualitativas.
    
    Args:
        stats: Diccionario con estadísticas de calculate_qualitative_stats()
        
    Returns:
        String formateado con el resumen
    """
    return f"""
📊 Resumen de Evaluación Cualitativa

Total de respuestas evaluadas: {stats['total']}

✅ Correctas: {stats['correctas']} ({stats['pct_correctas']:.1f}%)
⚠️ Incompletas: {stats['incompletas']} ({stats['pct_incompletas']:.1f}%)
❌ Incorrectas: {stats['incorrectas']} ({stats['pct_incorrectas']:.1f}%)
"""

