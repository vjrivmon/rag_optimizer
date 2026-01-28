#!/usr/bin/env python3
"""
⚖️ Estrategia de Weighted Voting

Combina respuestas de modelos usando pesos basados en su rendimiento histórico.
Selecciona la respuesta del modelo con mayor score ponderado.
"""

from typing import Dict, List, Any


class WeightedStrategy:
    """Estrategia de voting ponderado por rendimiento"""
    
    # Pesos basados en benchmark_ensemble 2025-10-11 19:19:14
    # Fuente: results/ensemble_20251011_191914.json
    DEFAULT_WEIGHTS = {
        'gemma2:27b': 0.9146,          # 22/26 correctas (MEJOR)
        'llama3.3:70b': 0.8879,        # 20/26 correctas
        'qwen3:32b': 0.8498,           # 17/26 correctas
        'deepseek-r1:latest': 0.6325   # 10/26 correctas
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Inicializa la estrategia con pesos específicos.
        
        Args:
            weights: Diccionario opcional de pesos por modelo.
                    Si no se proporciona, usa DEFAULT_WEIGHTS.
        """
        self.name = "weighted_voting"
        self.description = "Combina scores con pesos por rendimiento"
        self.weights = weights or self.DEFAULT_WEIGHTS
        
        # Normalizar pesos para que sumen 1.0
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {k: v/total_weight for k, v in self.weights.items()}
    
    def select_best_response(
        self,
        individual_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Selecciona la mejor respuesta usando scores ponderados.
        
        Args:
            individual_responses: Lista de respuestas generadas por cada modelo
        
        Returns:
            Diccionario con la respuesta seleccionada y metadata
        """
        if not individual_responses:
            raise ValueError("No hay respuestas para seleccionar")
        
        # Calcular scores ponderados
        weighted_scores = {}
        raw_scores = {}
        
        for response in individual_responses:
            model_name = response['model_name']
            raw_score = response['metrics']['combined_score']
            raw_scores[model_name] = raw_score
            
            # Obtener peso del modelo (default 0.1 si no está definido)
            weight = self.weights.get(model_name, 0.1)
            
            # Score ponderado
            weighted_score = raw_score * weight
            weighted_scores[model_name] = weighted_score
        
        # Seleccionar modelo con mayor score ponderado
        best_model = max(weighted_scores, key=weighted_scores.get)
        best_weighted_score = weighted_scores[best_model]
        
        # Obtener la respuesta seleccionada
        selected_response = next(r for r in individual_responses if r['model_name'] == best_model)
        
        # Calcular contribución de cada modelo al score final
        contributions = {
            model: f"{weighted_scores[model]:.3f} (peso: {self.weights.get(model, 0.1):.2f} × score: {raw_scores[model]:.3f})"
            for model in weighted_scores.keys()
        }
        
        reason = f"Mejor score ponderado: {best_weighted_score:.3f} (score raw: {raw_scores[best_model]:.3f}, peso: {self.weights.get(best_model, 0.1):.2f})"
        
        return {
            'answer': selected_response['answer'],
            'selected_from': best_model,
            'models_used': list(weighted_scores.keys()),
            'selection_reason': reason,
            'metrics': selected_response['metrics'],
            'generation_time': selected_response['generation_time'],
            'weighted_scores': weighted_scores,
            'raw_scores': raw_scores,
            'contributions': contributions,
            'contexts': selected_response.get('contexts', [])
        }
    
    def update_weights(self, new_weights: Dict[str, float]):
        """Actualiza los pesos de los modelos"""
        self.weights.update(new_weights)
        
        # Re-normalizar
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            self.weights = {k: v/total_weight for k, v in self.weights.items()}

