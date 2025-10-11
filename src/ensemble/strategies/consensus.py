#!/usr/bin/env python3
"""
🤝 Estrategia de Consensus + Fallback

Busca consenso entre modelos (respuestas similares con scores altos).
Si hay consenso, usa la mejor respuesta. Si hay divergencia, aplica fallback inteligente.
"""

from typing import Dict, List, Any
import statistics


class ConsensusStrategy:
    """Estrategia de consenso con fallback inteligente"""
    
    def __init__(self, consensus_threshold: float = 0.2):
        """
        Inicializa la estrategia.
        
        Args:
            consensus_threshold: Umbral de desviación estándar para considerar consenso.
                                Valores más bajos = mayor consenso requerido.
        """
        self.name = "consensus_fallback"
        self.description = "Busca consenso o aplica fallback inteligente"
        self.consensus_threshold = consensus_threshold
        self.high_score_threshold = 0.7  # Score mínimo para considerar "buena respuesta"
    
    def select_best_response(
        self,
        individual_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Selecciona respuesta basada en consenso o fallback.
        
        Lógica:
        1. Si hay consenso (scores similares y altos): usar la mejor
        2. Si hay divergencia pero alguna respuesta tiene score alto: usar esa
        3. Si todas tienen scores bajos: usar gemma2:27b como fallback confiable
        
        Args:
            individual_responses: Lista de respuestas generadas
        
        Returns:
            Diccionario con la respuesta seleccionada y metadata
        """
        if not individual_responses:
            raise ValueError("No hay respuestas para seleccionar")
        
        # Extraer scores
        scores = [r['metrics']['combined_score'] for r in individual_responses]
        model_names = [r['model_name'] for r in individual_responses]
        
        # Calcular estadísticas
        mean_score = statistics.mean(scores)
        if len(scores) > 1:
            stdev_score = statistics.stdev(scores)
        else:
            stdev_score = 0.0
        
        max_score = max(scores)
        min_score = min(scores)
        
        # Determinar si hay consenso
        has_consensus = stdev_score <= self.consensus_threshold
        has_high_scores = mean_score >= self.high_score_threshold
        
        # Construir mapeo modelo -> respuesta
        model_to_response = {r['model_name']: r for r in individual_responses}
        
        # CASO 1: Consenso con scores altos
        if has_consensus and has_high_scores:
            best_response = max(individual_responses, key=lambda r: r['metrics']['combined_score'])
            reason = f"Consenso alto (stdev: {stdev_score:.3f}, mean: {mean_score:.2f}) - usando mejor"
            strategy = 'consensus'
        
        # CASO 2: Divergencia pero hay al menos una respuesta excelente
        elif max_score >= 0.8:
            best_response = max(individual_responses, key=lambda r: r['metrics']['combined_score'])
            reason = f"Divergencia (stdev: {stdev_score:.3f}) pero score excelente: {max_score:.2f}"
            strategy = 'best_available'
        
        # CASO 3: Divergencia con scores medios - usar gemma2 si disponible
        elif 'gemma2:27b' in model_to_response:
            best_response = model_to_response['gemma2:27b']
            reason = f"Divergencia (stdev: {stdev_score:.3f}, mean: {mean_score:.2f}) - fallback a gemma2:27b (más confiable)"
            strategy = 'fallback_gemma2'
        
        # CASO 4: Sin gemma2, usar la mejor disponible
        else:
            best_response = max(individual_responses, key=lambda r: r['metrics']['combined_score'])
            reason = f"Divergencia sin gemma2 disponible - usando mejor score: {max_score:.2f}"
            strategy = 'fallback_best'
        
        # Calcular información adicional
        score_details = {
            model: score 
            for model, score in zip(model_names, scores)
        }
        
        return {
            'answer': best_response['answer'],
            'selected_from': best_response['model_name'],
            'models_used': model_names,
            'selection_reason': reason,
            'metrics': best_response['metrics'],
            'generation_time': best_response['generation_time'],
            'consensus_stats': {
                'mean_score': mean_score,
                'stdev_score': stdev_score,
                'max_score': max_score,
                'min_score': min_score,
                'has_consensus': has_consensus,
                'strategy_used': strategy
            },
            'all_scores': score_details,
            'contexts': best_response.get('contexts', [])
        }
    
    def analyze_consensus(self, individual_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza el nivel de consenso entre respuestas sin seleccionar una.
        
        Útil para debugging y análisis.
        """
        if not individual_responses:
            return {'error': 'No responses to analyze'}
        
        scores = [r['metrics']['combined_score'] for r in individual_responses]
        
        mean_score = statistics.mean(scores)
        stdev_score = statistics.stdev(scores) if len(scores) > 1 else 0.0
        
        return {
            'mean_score': mean_score,
            'stdev_score': stdev_score,
            'max_score': max(scores),
            'min_score': min(scores),
            'has_consensus': stdev_score <= self.consensus_threshold,
            'consensus_level': 'high' if stdev_score < 0.1 else 'medium' if stdev_score < 0.2 else 'low'
        }

