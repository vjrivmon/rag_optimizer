"""
🎯 Sistema de Ensemble Multi-Modelo para RAG

Este módulo implementa estrategias de ensemble que combinan múltiples modelos
para superar el rendimiento individual del mejor modelo.

Estrategias disponibles:
- Voting Majority: Selecciona respuesta con mejor score
- Weighted Voting: Combina scores con pesos por modelo
- Specialized Routing: Usa modelos específicos según tipo de pregunta
- Consensus Fallback: Busca consenso o usa fallback inteligente
"""

from .question_classifier import QuestionClassifier
from .ensemble_engine import EnsembleRAGEngine

__all__ = ['QuestionClassifier', 'EnsembleRAGEngine']

