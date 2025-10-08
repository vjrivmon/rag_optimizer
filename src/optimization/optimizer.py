from typing import Dict, Any
from skopt import Optimizer
from skopt.space import Real, Integer, Categorical
import numpy as np

class ParameterOptimizer:
    """Optimizador Bayesiano para parámetros RAG"""

    def __init__(self, context_window: int = 2048, model_name: str = ""):

        self.context_window = context_window
        self.model_name = model_name

        # Detectar si es un modelo con thinking tags (necesita más tokens)
        self.is_thinking_model = any(keyword in model_name.lower()
                                     for keyword in ['qwen', 'deepseek', 'r1'])

        # Ajustar max_tokens según tipo de modelo
        if self.is_thinking_model:
            # Modelos thinking: necesitan 3x más tokens (70% thinking + 30% respuesta)
            max_tokens_range = Integer(1200, 2000, name='max_tokens')
            print(f"   🧠 Modelo con thinking detectado: max_tokens=[1200, 2000]")
        else:
            # Modelos normales: rango estándar
            max_tokens_range = Integer(256, 512, name='max_tokens')

        # Espacio de búsqueda
        self.param_space = [
            # Retrieval
            Integer(3, 8, name='top_k'),
            Real(0.5, 0.8, name='similarity_threshold'),

            # Generation
            Real(0.1, 0.5, name='temperature'),
            Real(0.85, 0.95, name='top_p'),
            max_tokens_range,

            # Prompting
            Categorical(['medium', 'high'], name='strictness'),
        ]

        # Optimizador
        self.optimizer = Optimizer(
            dimensions=self.param_space,
            base_estimator='GP',
            acq_func='EI',
            n_initial_points=5,  # Exploración inicial
            random_state=42
        )

        # Historial
        self.history = []
        self.best_params = None
        self.best_score = -np.inf
        self.consecutive_bad = 0

    def suggest(self) -> Dict[str, Any]:
        """Sugiere parámetros"""

        suggested = self.optimizer.ask()

        params = {
            'top_k': suggested[0],
            'similarity_threshold': suggested[1],
            'temperature': suggested[2],
            'top_p': suggested[3],
            'max_tokens': suggested[4],
            'strictness': suggested[5]
        }

        # Ajustar top_k según context_window
        if self.context_window <= 1024:
            params['top_k'] = min(params['top_k'], 4)

        return params

    def report(self, params: Dict[str, Any], score: float):
        """Reporta resultado"""

        # Convertir params a lista
        param_list = [
            params['top_k'],
            params['similarity_threshold'],
            params['temperature'],
            params['top_p'],
            params['max_tokens'],
            params['strictness']
        ]

        # Reportar (negativo porque skopt minimiza)
        self.optimizer.tell(param_list, -score)

        # Guardar historial
        self.history.append({
            'params': params.copy(),
            'score': score
        })

        # Actualizar mejor
        if score > self.best_score:
            self.best_score = score
            self.best_params = params.copy()
            self.consecutive_bad = 0
        else:
            self.consecutive_bad += 1

    def should_rollback(self) -> bool:
        """Decide si hacer rollback"""
        return self.consecutive_bad >= 3

    def get_best_params(self) -> Dict[str, Any]:
        """Retorna mejores parámetros"""
        if self.best_params:
            return self.best_params.copy()

        # Parámetros por defecto (ajustados según tipo de modelo)
        default_max_tokens = 1500 if self.is_thinking_model else 400

        return {
            'top_k': 5,
            'similarity_threshold': 0.6,
            'temperature': 0.3,
            'top_p': 0.9,
            'max_tokens': default_max_tokens,
            'strictness': 'high'
        }
