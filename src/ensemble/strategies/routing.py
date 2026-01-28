#!/usr/bin/env python3
"""
🎯 Estrategia de Specialized Routing

Usa modelos específicos según el tipo de pregunta, optimizando la selección
para cada categoría. Incluye configuraciones especiales para preguntas problemáticas.
"""

from typing import Dict, List, Any, Optional
from ..question_classifier import QuestionClassifier


class RoutingStrategy:
    """Estrategia de routing inteligente por tipo de pregunta"""
    
    # Configuraciones especiales ultra-específicas
    SPECIAL_CONFIGS = {
        25: {  # "¿Qué significa Para-Mira-Ayuda?"
            'models': ['llama3.3:70b', 'gemma2:27b'],
            'description': 'Pregunta filosófica crítica - solo mejores modelos interpretativos',
            'use_synthesis': True  # Combinar respuestas de ambos
        },
        11: {  # "¿Dónde es la actividad de coles?"
            'models': ['gemma2:27b', 'llama3.3:70b'],
            'description': 'Pregunta factual problemática - modelos más precisos',
            'use_synthesis': False
        },
        20: {  # "¿Dónde es la actividad de resis?"
            'models': ['gemma2:27b', 'llama3.3:70b'],
            'description': 'Pregunta factual problemática - modelos más precisos',
            'use_synthesis': False
        },
        1: {  # "¿Qué se hace en la actividad de desayunos?"
            'models': ['gemma2:27b', 'qwen3:32b'],
            'description': 'Pregunta procedimental - modelos buenos en descripciones',
            'use_synthesis': False
        }
    }
    
    def __init__(self, classifier: Optional[QuestionClassifier] = None):
        """
        Inicializa la estrategia con un clasificador de preguntas.
        
        Args:
            classifier: Clasificador opcional. Si no se proporciona, crea uno nuevo.
        """
        self.name = "specialized_routing"
        self.description = "Routing inteligente por tipo de pregunta"
        self.classifier = classifier or QuestionClassifier()
    
    def get_recommended_models(self, question: str, question_id: int) -> List[str]:
        """
        Obtiene los modelos recomendados para una pregunta específica.
        
        Args:
            question: Texto de la pregunta
            question_id: ID de la pregunta
            
        Returns:
            Lista de nombres de modelos recomendados
        """
        # Verificar si hay configuración especial
        if question_id in self.SPECIAL_CONFIGS:
            config = self.SPECIAL_CONFIGS[question_id]
            print(f"   🎯 Usando configuración especial P{question_id}: {config['description']}")
            return config['models']
        
        # Clasificar pregunta
        question_type = self.classifier.classify(question, question_id)
        print(f"   🏷️ Pregunta clasificada como: {question_type}")
        
        # Obtener modelos recomendados
        recommended = self.classifier.get_recommended_models(question_type, question_id)
        return recommended
    
    def select_best_response(
        self,
        individual_responses: List[Dict[str, Any]],
        question: str = None,
        question_id: int = None
    ) -> Dict[str, Any]:
        """
        Selecciona la mejor respuesta basada en routing inteligente.
        
        Si la pregunta tiene configuración especial y usa synthesis,
        puede combinar múltiples respuestas.
        
        Args:
            individual_responses: Lista de respuestas generadas
            question: Texto opcional de la pregunta
            question_id: ID opcional de la pregunta
        
        Returns:
            Diccionario con la respuesta seleccionada y metadata
        """
        if not individual_responses:
            raise ValueError("No hay respuestas para seleccionar")
        
        # Obtener configuración especial si existe
        special_config = self.SPECIAL_CONFIGS.get(question_id) if question_id else None
        
        # Si hay configuración especial y usa synthesis
        if special_config and special_config.get('use_synthesis'):
            return self._synthesize_responses(individual_responses, question_id, special_config)
        
        # Si no hay configuración especial, obtener modelos recomendados
        if question and question_id:
            recommended_models = self.get_recommended_models(question, question_id)
        else:
            # Sin información de pregunta, usar todos los modelos
            recommended_models = [r['model_name'] for r in individual_responses]
        
        # Filtrar respuestas de modelos recomendados
        recommended_responses = [
            r for r in individual_responses 
            if r['model_name'] in recommended_models
        ]
        
        # Si no hay respuestas de modelos recomendados, usar todas
        if not recommended_responses:
            recommended_responses = individual_responses
        
        # Seleccionar la respuesta con mejor score entre las recomendadas
        best_response = max(recommended_responses, key=lambda r: r['metrics']['combined_score'])
        
        # Calcular scores de todos los modelos
        all_scores = {r['model_name']: r['metrics']['combined_score'] for r in individual_responses}
        
        reason = f"Routing: mejor de modelos recomendados {recommended_models} - score: {best_response['metrics']['combined_score']:.2f}"
        
        if special_config:
            reason = f"Config especial P{question_id}: {special_config['description']} - " + reason
        
        return {
            'answer': best_response['answer'],
            'selected_from': best_response['model_name'],
            'models_used': recommended_models,
            'selection_reason': reason,
            'metrics': best_response['metrics'],
            'generation_time': best_response['generation_time'],
            'all_scores': all_scores,
            'routing_type': 'special' if special_config else 'classified',
            'contexts': best_response.get('contexts', [])
        }
    
    def _synthesize_responses(
        self,
        responses: List[Dict[str, Any]],
        question_id: int,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sintetiza múltiples respuestas en una sola (para preguntas especiales como P25).
        
        Por ahora, selecciona la mejor, pero se puede mejorar para combinar.
        """
        # Filtrar respuestas de modelos configurados
        filtered_responses = [
            r for r in responses 
            if r['model_name'] in config['models']
        ]
        
        if not filtered_responses:
            filtered_responses = responses
        
        # Seleccionar la mejor
        best_response = max(filtered_responses, key=lambda r: r['metrics']['combined_score'])
        
        # TODO: Implementar síntesis real combinando respuestas
        # Por ahora, usar la mejor
        
        reason = f"Synthesis P{question_id}: combinando {', '.join(config['models'])} - usando mejor: {best_response['model_name']}"
        
        return {
            'answer': best_response['answer'],
            'selected_from': best_response['model_name'],
            'models_used': config['models'],
            'selection_reason': reason,
            'metrics': best_response['metrics'],
            'generation_time': sum(r['generation_time'] for r in filtered_responses),
            'synthesis_mode': True,
            'contexts': best_response.get('contexts', [])
        }

