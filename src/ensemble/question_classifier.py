#!/usr/bin/env python3
"""
🎯 Clasificador de Preguntas para Routing Inteligente

Clasifica preguntas en categorías para seleccionar los mejores modelos:
- filosofica: Preguntas sobre significado, valores, filosofía
- factual: Preguntas sobre hechos concretos (dónde, cuándo, cuánto)
- procedural: Preguntas sobre cómo hacer algo
- normativa: Preguntas sobre reglas, requisitos, permisos
"""

from typing import Dict, List
import re


class QuestionClassifier:
    """Clasifica preguntas por tipo para routing inteligente de modelos"""
    
    # Palabras clave por tipo de pregunta
    KEYWORDS = {
        'filosofica': [
            'significa', 'significado', 'caracteriza', 'filosofía', 'esencia',
            'valores', 'principios', 'por qué dni', 'qué es dni', 'representa',
            'para-mira-ayuda', 'para mira ayuda'
        ],
        'factual': [
            'dónde', 'donde', 'cuándo', 'cuando', 'a qué hora', 'a que hora',
            'cada cuánto', 'cada cuando', 'qué días', 'que dias', 'cuánto dura',
            'cuanto dura', 'cuántos', 'cuantos'
        ],
        'procedural': [
            'cómo', 'como', 'qué se hace', 'que se hace', 'qué hacer', 'que hacer',
            'proceso', 'pasos', 'forma'
        ],
        'normativa': [
            'puedo', 'necesito', 'tengo que', 'debo', 'requisito', 'obligatorio',
            'documentación', 'documentacion', 'permiso'
        ]
    }
    
    # Configuraciones especiales por ID de pregunta
    SPECIAL_QUESTIONS = {
        25: 'filosofica',  # "¿Qué significa Para-Mira-Ayuda?"
        26: 'filosofica',  # "¿Cómo se caracteriza el voluntariado de DNI?"
        1: 'procedural',   # "¿Qué se hace en la actividad de desayunos?"
        11: 'factual',     # "¿Dónde es la actividad de coles?"
        20: 'factual',     # "¿Dónde es la actividad de resis?"
    }
    
    def __init__(self):
        """Inicializa el clasificador"""
        self.cache = {}  # Cache de clasificaciones
    
    def classify(self, question: str, question_id: int = None) -> str:
        """
        Clasifica una pregunta en una categoría.
        
        Args:
            question: Texto de la pregunta
            question_id: ID opcional de la pregunta (para casos especiales)
            
        Returns:
            Tipo de pregunta: 'filosofica', 'factual', 'procedural', 'normativa', 'general'
        """
        # Si tiene ID y está en casos especiales, usar esa clasificación
        if question_id and question_id in self.SPECIAL_QUESTIONS:
            return self.SPECIAL_QUESTIONS[question_id]
        
        # Verificar cache
        if question in self.cache:
            return self.cache[question]
        
        # Normalizar pregunta
        question_lower = question.lower()
        
        # Contar coincidencias por tipo
        scores = {qtype: 0 for qtype in self.KEYWORDS.keys()}
        
        for qtype, keywords in self.KEYWORDS.items():
            for keyword in keywords:
                if keyword in question_lower:
                    scores[qtype] += 1
        
        # Seleccionar tipo con más coincidencias
        if max(scores.values()) > 0:
            classified_type = max(scores, key=scores.get)
        else:
            classified_type = 'general'
        
        # Guardar en cache
        self.cache[question] = classified_type
        
        return classified_type
    
    def get_recommended_models(self, question_type: str, question_id: int = None) -> List[str]:
        """
        Obtiene los modelos recomendados para un tipo de pregunta.
        
        Args:
            question_type: Tipo de pregunta clasificada
            question_id: ID opcional para configuraciones especiales
            
        Returns:
            Lista de nombres de modelos recomendados (ordenados por prioridad)
        """
        # Configuraciones especiales ultra-específicas
        if question_id == 25:  # Para-Mira-Ayuda
            return ['llama3.3:70b', 'gemma2:27b']
        
        if question_id in [11, 20]:  # Preguntas de ubicación problemáticas
            return ['gemma2:27b', 'llama3.3:70b']
        
        # Configuraciones por tipo
        model_recommendations = {
            'filosofica': ['llama3.3:70b', 'gemma2:27b'],  # Mejor en interpretación
            'factual': ['gemma2:27b', 'llama3.3:70b'],     # Más preciso
            'procedural': ['gemma2:27b', 'qwen3:32b'],     # Buenos en descripciones
            'normativa': ['gemma2:27b', 'llama3.3:70b'],   # Buenos en reglas
            'general': ['gemma2:27b']                       # Default: el mejor
        }
        
        return model_recommendations.get(question_type, ['gemma2:27b'])
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estadísticas de uso del clasificador"""
        type_counts = {}
        for qtype in self.cache.values():
            type_counts[qtype] = type_counts.get(qtype, 0) + 1
        return type_counts

