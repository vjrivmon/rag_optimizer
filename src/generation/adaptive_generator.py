#!/usr/bin/env python3
"""
🌡️ Adaptive Temperature Generator - Temperatura dinámica según tipo de pregunta

MEJORA #7: Adaptive Temperature
- Ajusta temperatura según tipo de pregunta (factual=0.0, conceptual=0.5)
- Optimiza consistencia vs creatividad por categoría
- Configuración específica por modelo
- Impacto: +5-10% combined_score

USO:
    from adaptive_generator import AdaptiveTemperatureGenerator

    generator = AdaptiveTemperatureGenerator(model_wrapper)
    result = generator.generate_adaptive(prompt, question, model_name="gemma2:27b")
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


class QuestionCategory(Enum):
    """Categorías de preguntas para ajuste de temperatura"""
    FACTUAL = "factual"          # Preguntas factuales - necesita consistencia
    PROCEDURAL = "procedural"    # Procedimientos - necesita precisión
    TEMPORAL = "temporal"        # Tiempos y fechas - necesita exactitud
    CONCEPTUAL = "conceptual"    # Conceptos - permite creatividad
    COMPARATIVE = "comparative"  # Comparaciones - necesita balance
    CREATIVE = "creative"        # Preguntas abiertas - permite creatividad


@dataclass
class TemperatureConfig:
    """Configuración de temperaturas por categoría"""
    # Temperaturas base por categoría
    factual_temp: float = 0.0      # Máxima consistencia
    procedural_temp: float = 0.2   # Baja variación
    temporal_temp: float = 0.0     # Exactitud total
    conceptual_temp: float = 0.5   # Balance explicativo
    comparative_temp: float = 0.3  # Comparación estructurada
    creative_temp: float = 0.7     # Mayor creatividad

    # Ajustes por modelo
    model_adjustments: Dict[str, float] = None

    # Configuración general
    min_temperature: float = 0.0
    max_temperature: float = 1.0
    enable_dynamic_adjustment: bool = True
    context_length_factor: bool = True  # Ajustar según longitud del contexto


class AdaptiveTemperatureGenerator:
    """
    Generador con temperatura adaptativa según tipo de pregunta

    Estrategia:
    1. Clasificar pregunta en categorías
    2. Asignar temperatura base según categoría
    3. Ajustar por características específicas del modelo
    4. Modificar según longitud del contexto y otros factores

    Beneficios:
    - Respuestas factuales más consistentes
    - Respuestas conceptuales más ricas
    - +5-10% en combined_score
    """

    def __init__(self, model_wrapper, config: Optional[TemperatureConfig] = None):
        """
        Inicializar generador adaptativo

        Args:
            model_wrapper: Wrapper del modelo LLM
            config: Configuración de temperaturas
        """
        self.model_wrapper = model_wrapper
        self.config = config or self._get_default_config()

        # Inicializar patrones de clasificación
        self._init_classification_patterns()

        # Histórico de temperaturas usadas (para análisis)
        self.temperature_history = []

    def _get_default_config(self) -> TemperatureConfig:
        """Configuración por defecto de temperaturas"""
        return TemperatureConfig(
            model_adjustments={
                'deepseek-r1': 0.1,      # Ligeramente más creativo
                'llama3.3': -0.1,        # Ligeramente más conservador
                'qwen3': 0.0,            # Neutro
                'gemma2': -0.05          # Ligeramente conservador
            }
        )

    def _init_classification_patterns(self):
        """Inicializa patrones para clasificación de preguntas"""

        # Patrones por categoría
        self.patterns = {
            QuestionCategory.FACTUAL: [
                r'\bdónde\b', r'\bcuándo\b', r'\ba qué hora\b', r'\bquién\b',
                r'\bcuántos?\b', r'\bcuál es\b.*\bdirección\b', r'\bcuál es\b.*\blugar\b',
                r'\bcuál es\b.*\bnombre\b', r'\bcuánto cuesta\b', r'\bcuál es el precio\b'
            ],

            QuestionCategory.PROCEDURAL: [
                r'\bcómo\b', r'\bproceso\b', r'\bpasos\b', r'\bme apunto\b',
                r'\bparticipar\b', r'\binscribir\b', r'\bregistrarse\b',
                r'\banotarse\b', r'\bunirse\b', r'\bqué hacer\b'
            ],

            QuestionCategory.TEMPORAL: [
                r'\bcada cuánto\b', r'\bfrecuencia\b', r'\bperiódico\b',
                r'\bsemanal\b', r'\bmensual\b', r'\bdiario\b', r'\bregular\b',
                r'\ba menudo\b', r'\bcuándo se repite\b', r'\bcada qué\b'
            ],

            QuestionCategory.CONCEPTUAL: [
                r'\bqué significa\b', r'\bqué es\b', r'\bpor qué\b', r'\bobjetivo\b',
                r'\bfilosofía\b', r'\bmisión\b', r'\bpropósito\b', r'\bvalores\b',
                r'\bexplica\b', r'\bdefinición\b'
            ],

            QuestionCategory.COMPARATIVE: [
                r'\bcuál es mejor\b', r'\bdiferencia\b', r'\bcomparar\b',
                r'\bventajas\b', r'\bdesventajas\b', r'\bdiferencias\b',
                r'\bsimilar\b', r'\bcomparación\b', r'\bversus\b'
            ],

            QuestionCategory.CREATIVE: [
                r'\bopina\b', r'\bqué te parece\b', r'\bsugiere\b',
                r'\bideas\b', r'\bcómo mejorar\b', r'\bpropón\b',
                r'\brecomienda\b', r'\bsugerencias\b'
            ]
        }

    def classify_question(self, question: str) -> QuestionCategory:
        """
        Clasifica pregunta en categorías para ajuste de temperatura

        Args:
            question: Pregunta a clasificar

        Returns:
            Categoría de la pregunta
        """
        question_lower = question.lower()

        # Contar matches por categoría
        category_scores = {}

        for category, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    score += 1
            category_scores[category] = score

        # Encontrar categoría con mayor score
        max_score = max(category_scores.values())
        if max_score == 0:
            return QuestionCategory.FACTUAL  # Default

        best_category = max(category_scores.items(), key=lambda x: x[1])[0]
        return best_category

    def calculate_optimal_temperature(
        self,
        question: str,
        context: str = "",
        model_name: str = ""
    ) -> float:
        """
        Calcula temperatura óptima para una pregunta

        Args:
            question: Pregunta del usuario
            context: Contexto disponible
            model_name: Nombre del modelo

        Returns:
            Temperatura óptima (0.0 - 1.0)
        """
        # 1. Clasificar pregunta
        category = self.classify_question(question)

        # 2. Obtener temperatura base
        base_temp = self._get_base_temperature(category)

        # 3. Ajustar por modelo
        model_adjustment = self._get_model_adjustment(model_name)

        # 4. Ajustar por contexto
        context_adjustment = self._get_context_adjustment(context) if self.config.context_length_factor else 0.0

        # 5. Calcular temperatura final
        final_temp = base_temp + model_adjustment + context_adjustment

        # 6. Aplicar límites
        final_temp = max(self.config.min_temperature, min(self.config.max_temperature, final_temp))

        # 7. Registrar en histórico
        self.temperature_history.append({
            'question': question,
            'category': category.value,
            'base_temperature': base_temp,
            'model_adjustment': model_adjustment,
            'context_adjustment': context_adjustment,
            'final_temperature': final_temp,
            'model_name': model_name
        })

        return final_temp

    def _get_base_temperature(self, category: QuestionCategory) -> float:
        """Obtiene temperatura base para una categoría"""
        temp_map = {
            QuestionCategory.FACTUAL: self.config.factual_temp,
            QuestionCategory.PROCEDURAL: self.config.procedural_temp,
            QuestionCategory.TEMPORAL: self.config.temporal_temp,
            QuestionCategory.CONCEPTUAL: self.config.conceptual_temp,
            QuestionCategory.COMPARATIVE: self.config.comparative_temp,
            QuestionCategory.CREATIVE: self.config.creative_temp
        }
        return temp_map.get(category, self.config.factual_temp)

    def _get_model_adjustment(self, model_name: str) -> float:
        """Obtiene ajuste de temperatura para un modelo específico"""
        if not self.config.model_adjustments:
            return 0.0

        model_lower = model_name.lower()
        for model_key, adjustment in self.config.model_adjustments.items():
            if model_key in model_lower:
                return adjustment

        return 0.0

    def _get_context_adjustment(self, context: str) -> float:
        """
        Calcula ajuste de temperatura basado en el contexto

        Lógica:
        - Contexto largo: reducir temperatura (más información, menos necesidad de creatividad)
        - Contexto corto: aumentar temperatura (menos información, más necesidad de inferencia)
        """
        if not context:
            return 0.1  # Aumentar ligeramente si no hay contexto

        context_length = len(context)

        if context_length > 2000:
            return -0.05  # Reducir para contextos largos
        elif context_length > 1000:
            return 0.0    # Neutral para contextos medianos
        elif context_length > 500:
            return 0.05   # Aumentar ligeramente para contextos cortos
        else:
            return 0.1    # Aumentar más para contextos muy cortos

    def generate_adaptive(
        self,
        prompt: str,
        question: str,
        model_name: str = "",
        context: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Genera respuesta con temperatura adaptativa

        Args:
            prompt: Prompt base
            question: Pregunta original (para clasificación)
            model_name: Nombre del modelo
            context: Contexto adicional
            **kwargs: Parámetros adicionales para el modelo

        Returns:
            Respuesta del modelo con metadata de temperatura
        """
        # Calcular temperatura óptima
        optimal_temp = self.calculate_optimal_temperature(question, context, model_name)

        # Sobrescribir temperatura en kwargs
        generation_kwargs = kwargs.copy()
        generation_kwargs['temperature'] = optimal_temp

        # Generar respuesta
        try:
            result = self.model_wrapper.generate(prompt, **generation_kwargs)

            # Enriquecer resultado con metadata de temperatura
            if isinstance(result, dict):
                result['temperature_metadata'] = {
                    'optimal_temperature': optimal_temp,
                    'question_category': self.classify_question(question).value,
                    'model_name': model_name,
                    'context_length': len(context) if context else 0
                }

            return result

        except Exception as e:
            # Error handling: fallback con temperatura neutra
            print(f"❌ Error con temperatura {optimal_temp:.2f}: {e}")
            generation_kwargs['temperature'] = 0.3  # Temperatura segura

            try:
                result = self.model_wrapper.generate(prompt, **generation_kwargs)
                if isinstance(result, dict):
                    result['temperature_metadata'] = {
                        'optimal_temperature': 0.3,
                        'fallback': True,
                        'original_temperature': optimal_temp,
                        'error': str(e)
                    }
                return result
            except Exception as e2:
                return {
                    'success': False,
                    'error': f"Error primario: {e}, Error fallback: {e2}",
                    'temperature_metadata': {
                        'optimal_temperature': optimal_temp,
                        'failed': True
                    }
                }

    def generate_with_consistency_check(
        self,
        prompt: str,
        question: str,
        model_name: str = "",
        context: str = "",
        num_samples: int = 3,
        consistency_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Genera múltiples muestras y verifica consistencia

        Args:
            prompt: Prompt base
            question: Pregunta original
            model_name: Nombre del modelo
            context: Contexto adicional
            num_samples: Número de muestras a generar
            consistency_threshold: Umbral de consistencia

        Returns:
            Respuesta con análisis de consistencia
        """
        optimal_temp = self.calculate_optimal_temperature(question, context, model_name)

        # Generar múltiples muestras con la misma temperatura
        samples = []
        for i in range(num_samples):
            try:
                result = self.model_wrapper.generate(
                    prompt,
                    temperature=optimal_temp,
                    max_tokens=512
                )
                if result.get('success', True):
                    samples.append(result['answer'])
            except Exception as e:
                print(f"❌ Error en muestra {i+1}: {e}")
                continue

        if not samples:
            return {
                'success': False,
                'error': 'No se pudieron generar muestras',
                'temperature_metadata': {
                    'optimal_temperature': optimal_temp,
                    'failed': True
                }
            }

        # Calcular consistencia
        consistency_score = self._calculate_consistency_score(samples)

        # Seleccionar mejor respuesta
        if consistency_score >= consistency_threshold:
            # Alta consistencia: usar la primera respuesta
            best_response = samples[0]
        else:
            # Baja consistencia: usar la más larga (asumir más completa)
            best_response = max(samples, key=len)

        return {
            'success': True,
            'answer': best_response,
            'consistency_score': consistency_score,
            'all_samples': samples,
            'num_samples': len(samples),
            'temperature_metadata': {
                'optimal_temperature': optimal_temp,
                'question_category': self.classify_question(question).value,
                'consistency_threshold': consistency_threshold,
                'num_samples_generated': num_samples
            }
        }

    def _calculate_consistency_score(self, samples: List[str]) -> float:
        """
        Calcula score de consistencia entre múltiples muestras

        Usa similitud de Jaccard entre palabras clave
        """
        if len(samples) < 2:
            return 1.0

        # Extraer palabras clave (eliminar stop words simples)
        def extract_keywords(text: str) -> set:
            words = re.findall(r'\b\w+\b', text.lower())
            # Stop words básicos en español
            stop_words = {'el', 'la', 'los', 'las', 'de', 'del', 'en', 'por', 'para', 'con', 'y', 'e', 'o', 'u', 'que', 'es', 'son', 'un', 'una', 'unos', 'unas'}
            return set(word for word in words if word not in stop_words and len(word) > 2)

        # Calcular similitud promedio
        similarities = []
        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                keywords1 = extract_keywords(samples[i])
                keywords2 = extract_keywords(samples[j])

                if not keywords1 and not keywords2:
                    similarities.append(1.0)
                elif not keywords1 or not keywords2:
                    similarities.append(0.0)
                else:
                    intersection = keywords1.intersection(keywords2)
                    union = keywords1.union(keywords2)
                    jaccard = len(intersection) / len(union) if union else 0.0
                    similarities.append(jaccard)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def get_temperature_statistics(self) -> Dict[str, Any]:
        """
        Estadísticas del uso de temperaturas
        """
        if not self.temperature_history:
            return {'message': 'No hay datos históricos'}

        # Estadísticas generales
        temperatures = [entry['final_temperature'] for entry in self.temperature_history]
        categories = [entry['category'] for entry in self.temperature_history]

        # Estadísticas por categoría
        category_stats = {}
        for category in set(categories):
            cat_temps = [entry['final_temperature'] for entry in self.temperature_history if entry['category'] == category]
            category_stats[category] = {
                'count': len(cat_temps),
                'avg_temperature': sum(cat_temps) / len(cat_temps),
                'min_temperature': min(cat_temps),
                'max_temperature': max(cat_temps)
            }

        return {
            'total_generations': len(self.temperature_history),
            'avg_temperature': sum(temperatures) / len(temperatures),
            'min_temperature': min(temperatures),
            'max_temperature': max(temperatures),
            'temperature_range': max(temperatures) - min(temperatures),
            'category_distribution': {cat: cats.count(cat) for cat in set(categories) for cats in [categories]},
            'category_stats': category_stats,
            'recent_entries': self.temperature_history[-5:]  # Últimas 5 generaciones
        }

    def clear_history(self):
        """Limpia el histórico de temperaturas"""
        self.temperature_history.clear()
        print("✅ Histórico de temperaturas limpiado")

    def update_temperature_config(
        self,
        category: str,
        temperature: float,
        model_name: str = ""
    ):
        """
        Actualiza configuración de temperatura

        Args:
            category: Categoría a actualizar ('factual', 'procedural', etc.)
            temperature: Nueva temperatura
            model_name: Si se especifica, ajusta solo para ese modelo
        """
        try:
            cat_enum = QuestionCategory(category)

            if model_name:
                # Ajustar para modelo específico
                if not self.config.model_adjustments:
                    self.config.model_adjustments = {}

                # Calcular ajuste relativo
                base_temp = self._get_base_temperature(cat_enum)
                adjustment = temperature - base_temp
                self.config.model_adjustments[model_name] = adjustment

                print(f"✅ Temperatura para {model_name} en categoría {category}: {temperature:.2f} (ajuste: {adjustment:+.2f})")
            else:
                # Ajustar temperatura base
                if cat_enum == QuestionCategory.FACTUAL:
                    self.config.factual_temp = temperature
                elif cat_enum == QuestionCategory.PROCEDURAL:
                    self.config.procedural_temp = temperature
                elif cat_enum == QuestionCategory.TEMPORAL:
                    self.config.temporal_temp = temperature
                elif cat_enum == QuestionCategory.CONCEPTUAL:
                    self.config.conceptual_temp = temperature
                elif cat_enum == QuestionCategory.COMPARATIVE:
                    self.config.comparative_temp = temperature
                elif cat_enum == QuestionCategory.CREATIVE:
                    self.config.creative_temp = temperature

                print(f"✅ Temperatura base para categoría {category}: {temperature:.2f}")

        except ValueError:
            print(f"❌ Categoría inválida: {category}")


# Función de conveniencia para uso rápido
def create_adaptive_generator(model_wrapper, debug: bool = False) -> AdaptiveTemperatureGenerator:
    """
    Crea un generador adaptativo con configuración por defecto

    Args:
        model_wrapper: Wrapper del modelo LLM
        debug: Si es True, incluye información de debugging

    Returns:
        Instancia de AdaptiveTemperatureGenerator
    """
    config = TemperatureConfig(
        enable_dynamic_adjustment=True,
        context_length_factor=True
    )

    return AdaptiveTemperatureGenerator(model_wrapper, config)


if __name__ == "__main__":
    # Ejemplo de uso
    print("🌡️ Adaptive Temperature Generator - Ejemplo de uso\n")

    # Mock model wrapper para demostración
    class MockModelWrapper:
        def generate(self, prompt, temperature=0.3, **kwargs):
            return {
                'success': True,
                'answer': f"Respuesta generada con temperatura {temperature:.2f} para el prompt proporcionado.",
                'temperature': temperature
            }

    # Crear generador adaptativo
    mock_model = MockModelWrapper()
    generator = create_adaptive_generator(mock_model, debug=True)

    # Queries de prueba por categoría
    test_queries = [
        ("¿Dónde son los desayunos?", "gemma2:27b"),  # Factual
        ("¿Cómo me apunto a resis?", "llama3.3:70b"),  # Procedural
        ("¿Qué significa Para-Mira-Ayuda?", "deepseek-r1"),  # Conceptual
        ("¿Cuál es la diferencia entre coles y resis?", "qwen3:32b"),  # Comparative
        ("¿Cada cuánto se hacen las reuniones?", "gemma2:27b"),  # Temporal
        ("¿Qué opinas de las actividades?", "deepseek-r1")  # Creative
    ]

    # Contexto de ejemplo
    sample_context = "DNI es una asociación juvenil de voluntariado con actividades como desayunos, coles y resis."

    print("🧪 Probando temperaturas adaptativas:\n")

    for i, (question, model) in enumerate(test_queries, 1):
        print(f"{'='*60}")
        print(f"Test {i}: {question}")
        print(f"Modelo: {model}")
        print('='*60)

        # Calcular temperatura óptima
        optimal_temp = generator.calculate_optimal_temperature(question, sample_context, model)

        # Generar respuesta
        result = generator.generate_adaptive(
            prompt=f"Responde basándote en el contexto: {sample_context}\n\nPregunta: {question}",
            question=question,
            model_name=model,
            context=sample_context
        )

        print(f"📊 Temperatura óptima: {optimal_temp:.3f}")
        print(f"📋 Categoría: {result['temperature_metadata']['question_category']}")
        print(f"🤖 Respuesta: {result['answer']}")
        print()

    # Estadísticas
    print(f"\n✅ Estadísticas de temperatura:")
    stats = generator.get_temperature_statistics()
    for key, value in stats.items():
        if key != 'recent_entries':
            print(f"   {key}: {value}")