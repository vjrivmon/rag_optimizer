#!/usr/bin/env python3
"""
🎯 Motor de Ensemble Multi-Modelo

Coordina múltiples modelos LLM y aplica diferentes estrategias de ensemble
para generar la mejor respuesta posible.
"""

from typing import Dict, List, Any, Optional
import time

from .question_classifier import QuestionClassifier
from .strategies import VotingStrategy, WeightedStrategy, RoutingStrategy, ConsensusStrategy


class EnsembleRAGEngine:
    """Motor principal que coordina múltiples modelos con estrategias de ensemble"""
    
    AVAILABLE_STRATEGIES = {
        'voting': VotingStrategy,
        'weighted': WeightedStrategy,
        'routing': RoutingStrategy,
        'consensus': ConsensusStrategy
    }
    
    def __init__(
        self,
        rag_engines: Dict[str, Any],  # {model_name: enhanced_rag_engine}
        enabled_strategies: List[str] = None
    ):
        """
        Inicializa el motor de ensemble.
        
        Args:
            rag_engines: Diccionario de engines RAG por modelo
            enabled_strategies: Lista de estrategias a usar. Si None, usa todas.
        """
        self.rag_engines = rag_engines
        self.classifier = QuestionClassifier()
        
        # Inicializar estrategias
        if enabled_strategies is None:
            enabled_strategies = list(self.AVAILABLE_STRATEGIES.keys())
        
        self.strategies = {}
        for strategy_name in enabled_strategies:
            if strategy_name in self.AVAILABLE_STRATEGIES:
                if strategy_name == 'routing':
                    self.strategies[strategy_name] = RoutingStrategy(self.classifier)
                else:
                    self.strategies[strategy_name] = self.AVAILABLE_STRATEGIES[strategy_name]()
        
        print(f"✅ Ensemble Engine inicializado con {len(self.rag_engines)} modelos")
        print(f"   Modelos: {list(self.rag_engines.keys())}")
        print(f"   Estrategias: {list(self.strategies.keys())}")
    
    def generate_individual_responses(
        self,
        question: str,
        question_id: int,
        models_to_use: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Genera respuestas con todos los modelos individuales.
        
        Args:
            question: Pregunta a responder
            question_id: ID de la pregunta
            models_to_use: Lista opcional de modelos específicos a usar
        
        Returns:
            Lista de respuestas individuales de cada modelo
        """
        if models_to_use is None:
            models_to_use = list(self.rag_engines.keys())
        
        individual_responses = []
        
        for model_name in models_to_use:
            if model_name not in self.rag_engines:
                print(f"   ⚠️ Modelo {model_name} no disponible, skipping")
                continue
            
            print(f"   🤖 Generando con {model_name}...")
            
            try:
                engine = self.rag_engines[model_name]
                
                # Generar respuesta usando el engine RAG
                start_time = time.time()
                result = engine.process_query_with_validation(
                    question=question,
                    question_id=question_id
                )
                gen_time = time.time() - start_time
                
                # Convertir validation a dict si es un objeto
                validation_data = result.get('validation', {})
                if hasattr(validation_data, '__dict__'):
                    # Es un objeto, convertir a dict
                    validation_data = {
                        'is_valid': getattr(validation_data, 'is_valid', False),
                        'confidence': getattr(validation_data, 'confidence', 0.0),
                        'issues': getattr(validation_data, 'issues', []),
                        'protocol_used': getattr(validation_data, 'protocol_used', 'unknown')
                    }
                
                # Construir respuesta individual
                individual_response = {
                    'model_name': model_name,
                    'question': question,
                    'question_id': question_id,
                    'answer': result['answer'],
                    'contexts': result['contexts'],
                    'generation_time': gen_time,
                    'metrics': {
                        'combined_score': 0.0,  # Se llenará después de evaluación
                        'faithfulness': 0.0,
                        'answer_relevancy': 0.0,
                        'context_precision': 0.0,
                        'context_recall': 0.0,
                        'answer_correctness': 0.0,
                        'answer_similarity': 0.0
                    },
                    'validation': validation_data,
                    'config_used': result.get('config_used', {}),
                    'retrieval_stats': result.get('retrieval_stats', {})
                }
                
                individual_responses.append(individual_response)
                print(f"      ✅ Generado en {gen_time:.1f}s")
                
            except Exception as e:
                print(f"      ❌ Error con {model_name}: {str(e)}")
                continue
        
        return individual_responses
    
    def generate_with_strategy(
        self,
        strategy_name: str,
        individual_responses: List[Dict[str, Any]],
        question: str = None,
        question_id: int = None
    ) -> Dict[str, Any]:
        """
        Aplica una estrategia de ensemble a las respuestas individuales.
        
        Args:
            strategy_name: Nombre de la estrategia a aplicar
            individual_responses: Respuestas individuales ya generadas
            question: Texto opcional de la pregunta (para routing)
            question_id: ID opcional de la pregunta (para routing)
        
        Returns:
            Resultado de aplicar la estrategia
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Estrategia '{strategy_name}' no disponible")
        
        strategy = self.strategies[strategy_name]
        
        # Aplicar estrategia
        if strategy_name == 'routing' and question and question_id:
            result = strategy.select_best_response(
                individual_responses,
                question=question,
                question_id=question_id
            )
        else:
            result = strategy.select_best_response(individual_responses)
        
        # Añadir metadata de estrategia
        result['strategy'] = strategy_name
        result['strategy_description'] = strategy.description
        
        return result
    
    def generate_all_strategies(
        self,
        question: str,
        question_id: int,
        individual_responses: List[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Genera respuestas usando TODAS las estrategias de ensemble.
        
        Args:
            question: Pregunta a responder
            question_id: ID de la pregunta
            individual_responses: Respuestas individuales pre-generadas (opcional)
        
        Returns:
            Diccionario con resultados de cada estrategia:
            {
                'voting_majority': {...},
                'weighted_voting': {...},
                'specialized_routing': {...},
                'consensus_fallback': {...}
            }
        """
        # Generar respuestas individuales si no se proporcionaron
        if individual_responses is None:
            print(f"\n🎯 Generando respuestas individuales para P{question_id}...")
            individual_responses = self.generate_individual_responses(question, question_id)
        
        if not individual_responses:
            raise ValueError("No se pudieron generar respuestas individuales")
        
        # Aplicar cada estrategia
        ensemble_results = {}
        
        for strategy_name in self.strategies.keys():
            print(f"\n   🎲 Aplicando estrategia: {strategy_name}")
            
            try:
                result = self.generate_with_strategy(
                    strategy_name,
                    individual_responses,
                    question=question,
                    question_id=question_id
                )
                ensemble_results[strategy_name] = result
                print(f"      ✅ Respuesta seleccionada de: {result['selected_from']}")
                
            except Exception as e:
                print(f"      ❌ Error aplicando {strategy_name}: {str(e)}")
                ensemble_results[strategy_name] = {
                    'error': str(e),
                    'strategy': strategy_name
                }
        
        return ensemble_results
    
    def process_question_complete(
        self,
        question: str,
        question_id: int
    ) -> Dict[str, Any]:
        """
        Procesa una pregunta completa: genera individuales + todas las estrategias.
        
        Returns:
            {
                'question': str,
                'question_id': int,
                'individual': List[Dict],
                'ensemble': Dict[str, Dict],
                'summary': {
                    'total_models': int,
                    'total_strategies': int,
                    'total_time': float
                }
            }
        """
        start_time = time.time()
        
        print(f"\n{'='*80}")
        print(f"🎯 Procesando P{question_id}: {question}")
        print(f"{'='*80}")
        
        # Fase 1: Generar respuestas individuales
        individual_responses = self.generate_individual_responses(question, question_id)
        
        # Fase 2: Aplicar estrategias de ensemble
        ensemble_results = self.generate_all_strategies(
            question,
            question_id,
            individual_responses
        )
        
        total_time = time.time() - start_time
        
        print(f"\n✅ Pregunta P{question_id} completada en {total_time:.1f}s")
        
        return {
            'question': question,
            'question_id': question_id,
            'individual': individual_responses,
            'ensemble': ensemble_results,
            'summary': {
                'total_models': len(individual_responses),
                'total_strategies': len(ensemble_results),
                'total_time': total_time
            }
        }

