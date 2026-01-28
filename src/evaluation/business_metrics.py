#!/usr/bin/env python3
"""
📊 DNI Business Metrics - Métricas de negocio específicas para DNI Valencia

MEJORA #8: Business Metrics Custom
- Métricas alineadas con objetivos de negocio DNI
- Detecta si responde información crítica del dominio
- Complementa métricas técnicas RAGAs
- Evalúa tono apropiado y no-alucinaciones

USO:
    from business_metrics import DNIBusinessMetrics

    evaluator = DNIBusinessMetrics()
    metrics = evaluator.evaluate_business_metrics(question, answer, "desayunos")
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class ActivityCategory(Enum):
    """Categorías de actividades DNI"""
    DESAYUNOS = "desayunos"
    COLES = "coles"
    RESIS = "resis"
    REUNIONES = "reuniones"
    FILOSOFIA = "filosofia"
    GENERAL = "general"


@dataclass
class CriticalInfo:
    """Información crítica por categoría"""
    required: List[str]      # Información que debe estar presente
    optional: List[str]      # Información deseable
    forbidden: List[str]     # Información que NO debe estar (alucinaciones)


class DNIBusinessMetrics:
    """
    Evaluador de métricas de negocio específicas para DNI Valencia

    Estrategia:
    1. Detectar categoría de la pregunta/respuesta
    2. Verificar información crítica requerida
    3. Evaluar tono y apropiación del dominio
    4. Detectar alucinaciones y errores
    5. Calcular métricas de negocio custom

    Beneficios:
    - Métricas alineadas con objetivos reales de DNI
    - Detección de información crítica del dominio
    - Complemento perfecto a métricas RAGAs técnicas
    """

    def __init__(self):
        """Inicializar evaluador de métricas de negocio"""
        self._init_critical_info()
        self._init_domain_patterns()
        self._init_tone_patterns()

    def _init_critical_info(self):
        """Inicializa información crítica por categoría"""

        # Información crítica por actividad
        self.critical_info = {
            ActivityCategory.DESAYUNOS: CriticalInfo(
                required=[
                    'porta de la mar', 'valencia', 'sábado', '8:00', '8 de la mañana'
                ],
                optional=[
                    'voluntarios', 'personas sin hogar', 'reparto', 'comida',
                    'equipo', 'conversación', 'encuentro'
                ],
                forbidden=[
                    'domingo', '10:00', 'pago', 'dinero', 'curso', 'certificado'
                ]
            ),

            ActivityCategory.COLES: CriticalInfo(
                required=[
                    'ceip antonio ferrandis', 'la coma', 'certificado de delitos sexuales'
                ],
                optional=[
                    '15:30', '16:30', 'niños', 'refuerzo escolar', 'ayuda escolar',
                    'gasolina', 'transporte', 'participantes'
                ],
                forbidden=[
                    'universidad', 'adultos', 'pago', 'sin certificado'
                ]
            ),

            ActivityCategory.RESIS: CriticalInfo(
                required=[
                    'la acollida', 'crevillente 22', 'miércoles', '17:30', '18:30', 'ancianos'
                ],
                optional=[
                    'conversación', 'compañía', 'juegos', 'mayores', 'tercera edad',
                    'residencia', 'contacto con mayores'
                ],
                forbidden=[
                    'niños', 'colegio', 'pago', 'deportes'
                ]
            ),

            ActivityCategory.REUNIONES: CriticalInfo(
                required=[
                    'miércoles', 'reunión semanal', 'coordinadores'
                ],
                optional=[
                    'organización', 'planificación', 'nuevas actividades', 'voluntarios',
                    'participación', 'equipo'
                ],
                forbidden=[
                    'domingo', 'vacaciones', 'pago obligatorio'
                ]
            ),

            ActivityCategory.FILOSOFIA: CriticalInfo(
                required=[
                    'para', 'mira', 'ayuda', 'damos nuestra ilusión'
                ],
                optional=[
                    'jóvenes', 'voluntariado', 'cercanía', 'caridad', 'solidaridad',
                    'servicio', 'compañerismo', 'estudiantes universitarios'
                ],
                forbidden=[
                    'empresa', 'negocio', 'lucro', 'remunerado'
                ]
            )
        }

        # Patrones de detección de categoría
        self.category_patterns = {
            ActivityCategory.DESAYUNOS: [
                r'desayuno', r'comida', r'reparto', r'mañana', r'porta de la mar'
            ],
            ActivityCategory.COLES: [
                r'coles?', r'colegio', r'ceip', r'niños?', r'refuerzo', r'escuela',
                r'antonio ferrandis', r'la coma'
            ],
            ActivityCategory.RESIS: [
                r'reis?', r'residencia', r'ancianos?', r'mayores?', r'abuelos?',
                r'acollida', r'crevillente'
            ],
            ActivityCategory.REUNIONES: [
                r'reunión', r'reuniones?', r'encuentro', r'coordinador'
            ],
            ActivityCategory.FILOSOFIA: [
                r'filosofía', r'para[-\s]?mira[-\s]?ayuda', r'dni', r'damos nuestra ilusión',
                r'valores?', r'objetivo', r'misión'
            ]
        }

    def _init_domain_patterns(self):
        """Inicializa patrones del dominio DNI"""
        self.domain_keywords = {
            'activities': [
                'desayuno', 'coles', 'resis', 'reunión', 'voluntariado'
            ],
            'locations': [
                'porta de la mar', 'valencia', 'ceip antonio ferrandis', 'la coma',
                'la acollida', 'crevillente 22'
            ],
            'times': [
                'sábado', 'miércoles', '8:00', '8 de la mañana', '15:30', '16:30',
                '17:30', '18:30'
            ],
            'people': [
                'voluntarios', 'estudiantes', 'universitarios', 'jóvenes',
                'personas sin hogar', 'niños', 'ancianos', 'mayores'
            ],
            'values': [
                'solidaridad', 'ayuda', 'cercanía', 'compañerismo', 'servicio',
                'voluntariado', 'donación', 'compromiso'
            ]
        }

        # Sinónimos y términos relacionados
        self.synonyms = {
            'desayunos': ['desayuno', 'comida', 'reparto de comida'],
            'coles': ['refuerzo escolar', 'ayuda escolar', 'tutoría', 'colegio'],
            'resis': ['visitas a residencias', 'ancianos', 'mayores', 'tercera edad'],
            'voluntarios': ['colaboradores', 'participantes', 'ayudantes'],
            'dni': ['damos nuestra ilusión', 'asociación juvenil']
        }

    def _init_tone_patterns(self):
        """Inicializa patrones para evaluar tono apropiado"""
        self.tone_indicators = {
            'appropriate': [
                r'\b(nosotros|nuestro|nuestra)\b',  # 1ª persona plural
                r'\b(puedes|te invitamos|ven|acompañanos)\b',  # Invitación amable
                r'\b(gratis|voluntario|sin coste|gratuito)\b',  # Enfatizar voluntariado
                r'\b(juntos|entre todos|comunidad)\b'  # Espíritu comunitario
            ],
            'inappropriate': [
                r'\b(se exige|obligatorio|requerido)\b',  # Demasiado exigente
                r'\b(cliente|cliente|consumidor)\b',  # Lenguaje comercial
                r'\b(producto|servicio|venta)\b',  # Lenguaje de negocio
                r'\b(contrato|pago|factura)\b'  # Lenguaje financiero
            ]
        }

    def detect_category(self, text: str) -> ActivityCategory:
        """
        Detecta la categoría principal del texto

        Args:
            text: Texto a analizar (pregunta o respuesta)

        Returns:
            Categoría detectada
        """
        text_lower = text.lower()

        # Contar matches por categoría
        category_scores = {}
        for category, patterns in self.category_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            category_scores[category] = score

        # Encontrar categoría con mayor score
        max_score = max(category_scores.values())
        if max_score == 0:
            return ActivityCategory.GENERAL

        best_category = max(category_scores.items(), key=lambda x: x[1])[0]
        return best_category

    def evaluate_business_metrics(
        self,
        question: str,
        answer: str,
        category: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Evalúa métricas de negocio específicas

        Args:
            question: Pregunta original
            answer: Respuesta generada
            category: Categoría (opcional, se detecta automáticamente)

        Returns:
            Diccionario con métricas de negocio
        """
        # Detectar categoría si no se proporciona
        if category:
            try:
                activity_category = ActivityCategory(category)
            except ValueError:
                activity_category = self.detect_category(f"{question} {answer}")
        else:
            activity_category = self.detect_category(f"{question} {answer}")

        # Si es categoría general, evaluar de forma simplificada
        if activity_category == ActivityCategory.GENERAL:
            return self._evaluate_general_metrics(question, answer)

        # Obtener información crítica para la categoría
        critical_info = self.critical_info.get(activity_category)
        if not critical_info:
            return self._evaluate_general_metrics(question, answer)

        # Evaluar métricas específicas
        metrics = {}

        # 1. Información crítica mencionada
        metrics['critical_info_coverage'] = self._calculate_critical_coverage(
            answer, critical_info.required
        )

        # 2. Información opcional mencionada
        metrics['optional_info_coverage'] = self._calculate_optional_coverage(
            answer, critical_info.optional
        )

        # 3. Detección de información prohibida (alucinaciones)
        metrics['forbidden_info_penalty'] = self._calculate_forbidden_penalty(
            answer, critical_info.forbidden
        )

        # 4. Longitud apropiada de respuesta
        metrics['length_appropriateness'] = self._calculate_length_appropriateness(answer)

        # 5. Awareness del contexto DNI
        metrics['contextual_awareness'] = self._calculate_contextual_awareness(answer)

        # 6. Tono apropiado del dominio
        metrics['tone_appropriateness'] = self._calculate_tone_appropriateness(answer)

        # 7. Presencia de palabras clave del dominio
        metrics['domain_keyword_coverage'] = self._calculate_domain_coverage(answer, activity_category)

        # 8. No alucinaciones (inverso de forbidden penalty)
        metrics['no_hallucination'] = max(0.0, 1.0 - metrics['forbidden_info_penalty'])

        # 9. Claridad y estructura
        metrics['clarity_score'] = self._calculate_clarity_score(answer)

        # 10. Score compuesto de negocio
        metrics['business_score'] = self._calculate_business_score(metrics)

        # Metadata adicional
        metrics['_metadata'] = {
            'detected_category': activity_category.value,
            'required_found': self._find_phrases(answer, critical_info.required),
            'optional_found': self._find_phrases(answer, critical_info.optional),
            'forbidden_found': self._find_phrases(answer, critical_info.forbidden)
        }

        return metrics

    def _evaluate_general_metrics(self, question: str, answer: str) -> Dict[str, float]:
        """Evalúa métricas para categoría general"""
        metrics = {
            'critical_info_coverage': 0.0,  # No aplica para general
            'optional_info_coverage': 0.0,
            'forbidden_info_penalty': 0.0,
            'length_appropriateness': self._calculate_length_appropriateness(answer),
            'contextual_awareness': self._calculate_contextual_awareness(answer),
            'tone_appropriateness': self._calculate_tone_appropriateness(answer),
            'domain_keyword_coverage': self._calculate_general_domain_coverage(answer),
            'no_hallucination': 1.0,  # Asumir que no hay alucinaciones en general
            'clarity_score': self._calculate_clarity_score(answer),
            'business_score': 0.0
        }

        # Calcular score compuesto para general
        weights = {
            'length_appropriateness': 0.2,
            'contextual_awareness': 0.3,
            'tone_appropriateness': 0.3,
            'domain_keyword_coverage': 0.2
        }

        metrics['business_score'] = sum(
            metrics[key] * weight for key, weight in weights.items()
        )

        metrics['_metadata'] = {
            'detected_category': 'general',
            'evaluation_type': 'general_metrics'
        }

        return metrics

    def _calculate_critical_coverage(self, answer: str, required_phrases: List[str]) -> float:
        """Calcula cobertura de información crítica requerida"""
        if not required_phrases:
            return 1.0

        answer_lower = answer.lower()
        found_count = 0

        for phrase in required_phrases:
            if phrase.lower() in answer_lower:
                found_count += 1

        return found_count / len(required_phrases)

    def _calculate_optional_coverage(self, answer: str, optional_phrases: List[str]) -> float:
        """Calcula cobertura de información opcional deseable"""
        if not optional_phrases:
            return 0.0

        answer_lower = answer.lower()
        found_count = 0

        for phrase in optional_phrases:
            if phrase.lower() in answer_lower:
                found_count += 1

        return found_count / len(optional_phrases)

    def _calculate_forbidden_penalty(self, answer: str, forbidden_phrases: List[str]) -> float:
        """Calcula penalización por información prohibida (alucinaciones)"""
        if not forbidden_phrases:
            return 0.0

        answer_lower = answer.lower()
        found_count = 0

        for phrase in forbidden_phrases:
            if phrase.lower() in answer_lower:
                found_count += 1

        # Penalización: cada frase prohibida reduce el score
        return min(1.0, found_count * 0.5)  # Máximo penalty de 1.0

    def _calculate_length_appropriateness(self, answer: str) -> float:
        """Calcula si la longitud de la respuesta es apropiada"""
        word_count = len(answer.split())

        # Reglas de longitud apropiada
        if word_count < 5:
            return 0.0  # Demasiado corta
        elif 5 <= word_count <= 100:
            return 1.0  # Longitud ideal
        elif 100 < word_count <= 200:
            return 0.8  # Un poco larga pero aceptable
        elif 200 < word_count <= 300:
            return 0.6  # Larga
        else:
            return 0.3  # Muy larga

    def _calculate_contextual_awareness(self, answer: str) -> float:
        """Calcula si la respuesta muestra awareness del contexto DNI"""
        answer_lower = answer.lower()

        # Indicadores de contexto DNI
        dni_indicators = [
            'dni', 'damos nuestra ilusión', 'voluntariado', 'voluntario',
            'colaborador', 'asociación', 'juvenil'
        ]

        found_indicators = sum(1 for indicator in dni_indicators if indicator in answer_lower)

        # Calcular score
        if found_indicators >= 2:
            return 1.0
        elif found_indicators == 1:
            return 0.7
        else:
            return 0.3  # Muy bajo awareness del contexto

    def _calculate_tone_appropriateness(self, answer: str) -> float:
        """Calcula si el tono es apropiado para el dominio DNI"""
        answer_lower = answer.lower()

        # Contar indicadores apropiados
        appropriate_count = 0
        for pattern in self.tone_indicators['appropriate']:
            matches = len(re.findall(pattern, answer_lower))
            appropriate_count += matches

        # Contar indicadores inapropiados
        inappropriate_count = 0
        for pattern in self.tone_indicators['inappropriate']:
            matches = len(re.findall(pattern, answer_lower))
            inappropriate_count += matches

        # Calcular score
        if inappropriate_count > 0:
            # Penalizar fuertemente tono inapropiado
            return max(0.0, 0.5 - (inappropriate_count * 0.2))
        elif appropriate_count >= 2:
            return 1.0
        elif appropriate_count == 1:
            return 0.8
        else:
            return 0.6  # Tonos neutro pero no inapropiado

    def _calculate_domain_coverage(self, answer: str, category: ActivityCategory) -> float:
        """Calcula cobertura de palabras clave del dominio específicas"""
        answer_lower = answer.lower()

        # Palabras clave específicas por categoría
        if category == ActivityCategory.DESAYUNOS:
            keywords = ['desayuno', 'sábado', 'porta de la mar', 'mañana']
        elif category == ActivityCategory.COLES:
            keywords = ['ceip', 'antonio ferrandis', 'niños', 'refuerzo']
        elif category == ActivityCategory.RESIS:
            keywords = ['acollida', 'crevillente', 'ancianos', 'mayores']
        elif category == ActivityCategory.REUNIONES:
            keywords = ['reunión', 'miércoles', 'coordinación']
        elif category == ActivityCategory.FILOSOFIA:
            keywords = ['para', 'mira', 'ayuda', 'valores']
        else:
            return 0.0

        found_keywords = sum(1 for keyword in keywords if keyword in answer_lower)
        return found_keywords / len(keywords) if keywords else 0.0

    def _calculate_general_domain_coverage(self, answer: str) -> float:
        """Calcula cobertura de palabras clave generales del dominio"""
        answer_lower = answer.lower()

        all_keywords = []
        for keywords in self.domain_keywords.values():
            all_keywords.extend(keywords)

        found_keywords = sum(1 for keyword in all_keywords if keyword in answer_lower)
        return min(1.0, found_keywords / 5)  # Normalizar a máximo 5 palabras clave

    def _calculate_clarity_score(self, answer: str) -> float:
        """Calcula la claridad y estructura de la respuesta"""
        if not answer.strip():
            return 0.0

        # Factores de claridad
        sentences = len(re.split(r'[.!?]+', answer))
        words = len(answer.split())
        avg_sentence_length = words / sentences if sentences > 0 else 0

        # Puntuación por estructura
        structure_score = 0.0

        # Buena longitud de frases (10-20 palabras)
        if 10 <= avg_sentence_length <= 20:
            structure_score += 0.4
        elif 5 <= avg_sentence_length <= 25:
            structure_score += 0.2

        # Uso de puntuación adecuada
        if re.search(r'[.!?]$', answer.strip()):
            structure_score += 0.3

        # No demasiadas frases cortas
        short_sentences = sum(1 for s in re.split(r'[.!?]+', answer) if len(s.split()) < 3)
        if short_sentences / sentences < 0.5:
            structure_score += 0.3

        return min(1.0, structure_score)

    def _calculate_business_score(self, metrics: Dict[str, float]) -> float:
        """Calcula score compuesto de negocio"""
        # Pesos para diferentes métricas
        weights = {
            'critical_info_coverage': 0.25,      # Más importante
            'no_hallucination': 0.20,           # Crítico
            'tone_appropriateness': 0.15,       # Importante
            'contextual_awareness': 0.15,       # Importante
            'length_appropriateness': 0.10,      # Menos crítico
            'clarity_score': 0.10,              # Menos crítico
            'optional_info_coverage': 0.05      # Bonus
        }

        # Calcular score ponderado
        weighted_score = 0.0
        for metric, weight in weights.items():
            if metric in metrics:
                weighted_score += metrics[metric] * weight

        return min(1.0, weighted_score)

    def _find_phrases(self, text: str, phrases: List[str]) -> List[str]:
        """Encuentra qué frases de la lista están presentes en el texto"""
        text_lower = text.lower()
        found = []

        for phrase in phrases:
            if phrase.lower() in text_lower:
                found.append(phrase)

        return found

    def batch_evaluate(
        self,
        qa_pairs: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Evalúa múltiples pares Q&A

        Args:
            qa_pairs: Lista de diccionarios con 'question' y 'answer'

        Returns:
            Resultados agregados
        """
        results = []
        category_scores = {}

        for qa_pair in qa_pairs:
            question = qa_pair.get('question', '')
            answer = qa_pair.get('answer', '')

            metrics = self.evaluate_business_metrics(question, answer)
            results.append(metrics)

            # Acumular por categoría
            category = metrics.get('_metadata', {}).get('detected_category', 'unknown')
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(metrics['business_score'])

        # Calcular estadísticas agregadas
        all_business_scores = [r['business_score'] for r in results]

        aggregated_results = {
            'total_evaluations': len(results),
            'overall_business_score': sum(all_business_scores) / len(all_business_scores) if all_business_scores else 0.0,
            'category_performance': {},
            'metric_averages': {},
            'individual_results': results
        }

        # Promedios por categoría
        for category, scores in category_scores.items():
            aggregated_results['category_performance'][category] = {
                'count': len(scores),
                'avg_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores)
            }

        # Promedios por métrica
        if results:
            all_metrics = results[0].keys()
            for metric in all_metrics:
                if metric != '_metadata' and isinstance(results[0][metric], (int, float)):
                    values = [r[metric] for r in results if metric in r]
                    aggregated_results['metric_averages'][metric] = sum(values) / len(values) if values else 0.0

        return aggregated_results

    def get_domain_info(self) -> Dict[str, Any]:
        """
        Retorna información sobre el dominio configurado
        """
        return {
            'categories': [cat.value for cat in ActivityCategory],
            'critical_info_count': len(self.critical_info),
            'domain_keywords_count': sum(len(keywords) for keywords in self.domain_keywords.values()),
            'tone_patterns_count': len(self.tone_indicators),
            'synonyms_count': len(self.synonyms)
        }

    def add_critical_info(
        self,
        category: str,
        required: List[str] = None,
        optional: List[str] = None,
        forbidden: List[str] = None
    ):
        """
        Agrega o modifica información crítica para una categoría

        Args:
            category: Categoría a modificar
            required: Información requerida (opcional)
            optional: Información opcional (opcional)
            forbidden: Información prohibida (opcional)
        """
        try:
            cat_enum = ActivityCategory(category)
            current = self.critical_info.get(cat_enum)

            if current:
                if required is not None:
                    current.required.extend(required)
                if optional is not None:
                    current.optional.extend(optional)
                if forbidden is not None:
                    current.forbidden.extend(forbidden)
                print(f"✅ Información crítica actualizada para categoría: {category}")
            else:
                # Crear nueva entrada
                self.critical_info[cat_enum] = CriticalInfo(
                    required=required or [],
                    optional=optional or [],
                    forbidden=forbidden or []
                )
                print(f"✅ Nueva categoría de información crítica creada: {category}")

        except ValueError:
            print(f"❌ Categoría inválida: {category}")


# Función de conveniencia para uso rápido
def create_dni_business_evaluator() -> DNIBusinessMetrics:
    """
    Crea un evaluador de métricas de negocio DNI

    Returns:
        Instancia de DNIBusinessMetrics
    """
    return DNIBusinessMetrics()


if __name__ == "__main__":
    # Ejemplo de uso
    print("📊 DNI Business Metrics - Ejemplo de uso\n")

    evaluator = create_dni_business_evaluator()

    # Casos de prueba
    test_cases = [
        {
            'question': '¿Dónde se realizan los desayunos?',
            'answer': 'Los desayunos se realizan en la Porta de la Mar de Valencia todos los sábados a las 8:00 de la mañana.',
            'category': 'desayunos'
        },
        {
            'question': '¿Qué necesito para participar en coles?',
            'answer': 'Para participar en coles necesitas tener el certificado de delitos sexuales. Las actividades son en el CEIP Antonio Ferrandis en La Coma.',
            'category': 'coles'
        },
        {
            'question': '¿Cuándo se visitan las residencias?',
            'answer': 'Las visitas a residencias (resis) son los miércoles a las 17:30 en La Acollida, ubicada en Crevillente 22. Allí compartimos con personas mayores.',
            'category': 'resis'
        },
        {
            'question': '¿Qué significa Para-Mira-Ayuda?',
            'answer': 'Para-Mira-Ayuda significa detenerse para ser consciente de quienes nos rodean, mirar con cariño y ofrecer ayuda generosamente. Es la filosofía de DNI.',
            'category': 'filosofia'
        }
    ]

    print("🧪 Evaluando casos de prueba:\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"{'='*60}")
        print(f"Caso {i}: {test_case['question']}")
        print(f"Respuesta: {test_case['answer']}")
        print('='*60)

        # Evaluar métricas
        metrics = evaluator.evaluate_business_metrics(
            test_case['question'],
            test_case['answer'],
            test_case.get('category')
        )

        print(f"\n📊 Resultados:")
        print(f"   Business Score: {metrics['business_score']:.3f}")
        print(f"   Critical Info Coverage: {metrics['critical_info_coverage']:.3f}")
        print(f"   No Hallucination: {metrics['no_hallucination']:.3f}")
        print(f"   Tone Appropriateness: {metrics['tone_appropriateness']:.3f}")
        print(f"   Contextual Awareness: {metrics['contextual_awareness']:.3f}")
        print(f"   Length Appropriateness: {metrics['length_appropriateness']:.3f}")

        metadata = metrics.get('_metadata', {})
        print(f"\n🔍 Detalles:")
        print(f"   Categoría detectada: {metadata.get('detected_category', 'N/A')}")
        print(f"   Info requerida encontrada: {metadata.get('required_found', [])}")
        print(f"   Info prohibida encontrada: {metadata.get('forbidden_found', [])}")

    print(f"\n✅ Información del dominio:")
    domain_info = evaluator.get_domain_info()
    for key, value in domain_info.items():
        print(f"   {key}: {value}")