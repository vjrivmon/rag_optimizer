"""
🎲 Estrategias de Ensemble para Combinar Modelos

Estrategias disponibles:
- VotingStrategy: Selecciona respuesta con mejor score individual
- WeightedStrategy: Combina scores con pesos por modelo
- RoutingStrategy: Usa modelos específicos según tipo de pregunta
- ConsensusStrategy: Busca consenso entre modelos
"""

from .voting import VotingStrategy
from .weighted import WeightedStrategy
from .routing import RoutingStrategy
from .consensus import ConsensusStrategy

__all__ = ['VotingStrategy', 'WeightedStrategy', 'RoutingStrategy', 'ConsensusStrategy']

