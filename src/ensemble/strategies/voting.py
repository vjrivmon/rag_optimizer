#!/usr/bin/env python3
"""
🗳️ Estrategia de Voting Majority

Genera respuestas con todos los modelos y selecciona la que tiene
el mayor combined_score. En caso de empate, usa gemma2:27b como tiebreaker.
"""

from typing import Dict, List, Any


class VotingStrategy:
    """Estrategia de voting por mejor score individual"""
    
    def __init__(self):
        self.name = "voting_majority"
        self.description = "Selecciona respuesta con mayor combined_score"
        self.tiebreaker_model = "gemma2:27b"
    
    def select_best_response(
        self,
        individual_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Selecciona la mejor respuesta entre las individuales.
        
        Args:
            individual_responses: Lista de respuestas generadas por cada modelo
                Cada respuesta debe tener: {
                    'model_name': str,
                    'answer': str,
                    'metrics': dict,
                    'generation_time': float,
                    ...
                }
        
        Returns:
            Diccionario con la respuesta seleccionada y metadata:
            {
                'answer': str,
                'selected_from': str,
                'models_used': List[str],
                'selection_reason': str,
                'metrics': dict,
                'generation_time': float,
                'all_scores': Dict[str, float]
            }
        """
        if not individual_responses:
            raise ValueError("No hay respuestas para seleccionar")
        
        # Extraer scores de cada modelo
        scores = {}
        for response in individual_responses:
            model_name = response['model_name']
            score = response['metrics']['combined_score']
            scores[model_name] = score
        
        # Encontrar el score máximo
        max_score = max(scores.values())
        
        # Encontrar modelos con el score máximo (puede haber empate)
        best_models = [model for model, score in scores.items() if score == max_score]
        
        # Resolver empate
        if len(best_models) > 1:
            # Si el tiebreaker está entre los mejores, usarlo
            if self.tiebreaker_model in best_models:
                selected_model = self.tiebreaker_model
                reason = f"Empate en score ({max_score:.2f}) - usando tiebreaker {self.tiebreaker_model}"
            else:
                # Usar el primero alfabéticamente
                selected_model = sorted(best_models)[0]
                reason = f"Empate en score ({max_score:.2f}) - usando {selected_model} (orden alfabético)"
        else:
            selected_model = best_models[0]
            reason = f"Mejor score individual: {max_score:.2f}"
        
        # Obtener la respuesta seleccionada
        selected_response = next(r for r in individual_responses if r['model_name'] == selected_model)
        
        return {
            'answer': selected_response['answer'],
            'selected_from': selected_model,
            'models_used': list(scores.keys()),
            'selection_reason': reason,
            'metrics': selected_response['metrics'],
            'generation_time': selected_response['generation_time'],
            'all_scores': scores,
            'contexts': selected_response.get('contexts', [])
        }

