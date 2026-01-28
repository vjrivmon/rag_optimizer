"""
Context Tracker - Sistema de Seguimiento de Contexto Conversacional
===================================================================

Mantiene y extrae el tema principal de una conversación multi-turn.
Detecta proyectos DNI mencionados y preserva el contexto activo.

Características:
- Detección de proyectos DNI mencionados
- Extracción de tema conversacional principal
- Ventana deslizante de contexto (últimas 4 interacciones)
- Pesos por recencia (más reciente = más importante)
"""

from typing import List, Dict, Tuple, Optional
import re
from collections import Counter


class ContextTracker:
    """
    Rastreador de contexto conversacional que mantiene el tema activo
    """

    # Proyectos DNI con sus palabras clave
    DNI_PROJECTS = {
        'desayunos_solidarios': {
            'keywords': ['desayuno', 'desayunos', 'solidario', 'solidarios', 'personas sin hogar',
                        'sábado', 'repartir', 'comida calle', 'bocadillos', 'café'],
            'name': 'Desayunos Solidarios',
            'weight': 1.0
        },
        'charlas_abuelitos': {
            'keywords': ['abuelito', 'abuelitos', 'residencia', 'resis', 'l\'acollida', 'acollida',
                        'personas mayores', 'ancianos', 'charlas', 'conversaciones'],
            'name': 'Charlas con Abuelitos (RESIS)',
            'weight': 1.0
        },
        'refuerzo_escolar': {
            'keywords': ['refuerzo', 'escolar', 'coles', 'niños', 'niño', 'estudios',
                        'matemáticas', 'deberes', 'colegio', 'escolares'],
            'name': 'Refuerzo Escolar (COLES)',
            'weight': 1.0
        },
        'dana': {
            'keywords': ['dana', 'inundaciones', 'horta sud', 'rehabilitar', 'limpieza',
                        'reconstrucción', 'afectados'],
            'name': 'Rehabilitar Valencia (DANA)',
            'weight': 1.0
        },
        'kayak': {
            'keywords': ['kayak', 'plástico', 'plásticos', 'recogida', 'río', 'albufera',
                        'limpieza agua', 'contaminación'],
            'name': 'Recogida de Plásticos (Kayak)',
            'weight': 1.0
        },
        'general_dni': {
            'keywords': ['dni', 'damos nuestra ilusión', 'voluntario', 'voluntarios',
                        'asociación', 'apuntarse', 'participar', 'unirse'],
            'name': 'DNI (General)',
            'weight': 0.5  # Peso menor porque es muy genérico
        }
    }

    # Palabras clave de temas generales
    TOPIC_KEYWORDS = {
        'horarios': ['horario', 'horarios', 'cuándo', 'hora', 'día', 'días', 'fecha'],
        'ubicacion': ['dónde', 'donde', 'lugar', 'ubicación', 'quedamos', 'punto encuentro', 'dirección'],
        'requisitos': ['requisito', 'requisitos', 'necesito', 'edad', 'experiencia', 'obligatorio'],
        'inscripcion': ['apuntarse', 'inscribirse', 'inscripción', 'formulario', 'registro', 'unirse'],
        'funcionamiento': ['cómo funciona', 'qué hacéis', 'qué se hace', 'actividad', 'dinámica'],
        'contacto': ['contacto', 'whatsapp', 'teléfono', 'instagram', 'redes', 'email']
    }

    def __init__(self):
        """Inicializa el context tracker"""
        self.current_project = None
        self.current_topic = None
        self.project_mentions = Counter()
        self.topic_mentions = Counter()

    def detect_projects(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Detecta proyectos DNI mencionados en el texto.

        Args:
            text: Texto a analizar (pregunta o respuesta)

        Returns:
            Lista de tuplas (project_id, project_name, score)
        """
        text_lower = text.lower()
        detected = []

        for project_id, project_info in self.DNI_PROJECTS.items():
            score = 0.0
            keywords_found = 0

            for keyword in project_info['keywords']:
                if keyword in text_lower:
                    keywords_found += 1
                    # Palabras más largas = más específicas = más peso
                    score += len(keyword) / 10.0

            if keywords_found > 0:
                # Normalizar score
                normalized_score = min(score * project_info['weight'], 1.0)
                detected.append((project_id, project_info['name'], normalized_score))

        # Ordenar por score descendente
        detected.sort(key=lambda x: x[2], reverse=True)

        return detected

    def detect_topic(self, text: str) -> Optional[str]:
        """
        Detecta el tema general de la conversación.

        Args:
            text: Texto a analizar

        Returns:
            Nombre del tema detectado o None
        """
        text_lower = text.lower()
        topic_scores = {}

        for topic_name, keywords in self.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                topic_scores[topic_name] = score

        if topic_scores:
            # Retornar tema con mayor score
            return max(topic_scores.items(), key=lambda x: x[1])[0]

        return None

    def extract_context_from_history(
        self,
        messages: List,
        window_size: int = 4
    ) -> Dict[str, any]:
        """
        Extrae el contexto conversacional del historial de mensajes.

        Args:
            messages: Lista de mensajes (LangChain HumanMessage/AIMessage)
            window_size: Número de pares pregunta-respuesta a considerar

        Returns:
            Dict con información de contexto:
            - active_project: Proyecto DNI detectado activo
            - active_topic: Tema general activo
            - confidence: Confianza en el contexto (0-1)
            - summary: Resumen textual del contexto
        """
        if not messages or len(messages) < 2:
            return {
                'active_project': None,
                'active_topic': None,
                'confidence': 0.0,
                'summary': None
            }

        # Obtener últimas N interacciones (ventana deslizante)
        recent_messages = messages[-(window_size * 2):]  # * 2 porque cada interacción = pregunta + respuesta

        # Analizar cada mensaje con pesos por recencia
        project_scores = Counter()
        topic_scores = Counter()

        total_messages = len(recent_messages)
        for i, msg in enumerate(recent_messages):
            # Peso por recencia: mensajes más recientes tienen más peso
            recency_weight = (i + 1) / total_messages  # 0.25, 0.5, 0.75, 1.0 para 4 mensajes

            content = str(msg.content) if hasattr(msg, 'content') else str(msg)

            # 🆕 CRUCIAL: Distinguir entre mensajes del usuario vs asistente
            # Solo mensajes del USUARIO deben tener peso completo para detectar proyectos
            is_user_message = msg.type == 'human' if hasattr(msg, 'type') else True

            # Factor de confianza: usuario = 1.0, asistente = 0.15 (mucho menor)
            source_weight = 1.0 if is_user_message else 0.15

            # Detectar proyectos
            detected_projects = self.detect_projects(content)
            for project_id, project_name, score in detected_projects:
                # Aplicar peso por recencia Y por fuente del mensaje
                weighted_score = score * recency_weight * source_weight
                project_scores[project_id] += weighted_score

            # Detectar temas (solo de mensajes del usuario)
            if is_user_message:
                detected_topic = self.detect_topic(content)
                if detected_topic:
                    topic_scores[detected_topic] += recency_weight

        # Determinar proyecto activo
        active_project = None
        project_confidence = 0.0

        if project_scores:
            # Filtrar proyectos genéricos si hay proyectos específicos
            specific_projects = {k: v for k, v in project_scores.items() if k != 'general_dni'}

            if specific_projects:
                # Usar proyecto específico más mencionado
                active_project_id = max(specific_projects.items(), key=lambda x: x[1])[0]
                project_confidence = min(specific_projects[active_project_id], 1.0)
            else:
                # Solo hay menciones genéricas a DNI
                active_project_id = 'general_dni'
                project_confidence = min(project_scores[active_project_id] * 0.5, 0.5)  # Confianza reducida

            active_project = self.DNI_PROJECTS[active_project_id]['name']

        # Determinar tema activo
        active_topic = None
        topic_confidence = 0.0

        if topic_scores:
            active_topic = max(topic_scores.items(), key=lambda x: x[1])[0]
            topic_confidence = min(topic_scores[active_topic], 1.0)

        # Confianza general (promedio de ambas)
        overall_confidence = (project_confidence + topic_confidence) / 2.0 if topic_confidence > 0 else project_confidence

        # Generar resumen textual
        summary_parts = []
        if active_project:
            summary_parts.append(f"Proyecto: {active_project}")
        if active_topic:
            topic_readable = active_topic.replace('_', ' ').capitalize()
            summary_parts.append(f"Tema: {topic_readable}")

        summary = " | ".join(summary_parts) if summary_parts else None

        return {
            'active_project': active_project,
            'active_topic': active_topic,
            'confidence': overall_confidence,
            'summary': summary,
            'project_score': project_confidence,
            'topic_score': topic_confidence
        }

    def enrich_query_with_context(
        self,
        query: str,
        context_info: Dict[str, any]
    ) -> str:
        """
        Enriquece una query con información de contexto.

        Args:
            query: Pregunta original del usuario
            context_info: Información de contexto (de extract_context_from_history)

        Returns:
            Query enriquecida con contexto
        """
        if not context_info or context_info['confidence'] < 0.6:
            # Confianza muy baja, no añadir contexto
            return query

        enriched = query

        # Si hay proyecto activo, añadirlo explícitamente
        # 🆕 THRESHOLD AUMENTADO: Requiere project_score > 0.6 (antes 0.4)
        if context_info['active_project'] and context_info['project_score'] > 0.6:
            project_name = context_info['active_project']

            # Solo añadir si no está ya en la pregunta
            if not any(word.lower() in query.lower() for word in project_name.split()):
                enriched = f"[Contexto: {project_name}] {query}"

        return enriched

    def should_keep_context(
        self,
        new_query: str,
        context_info: Dict[str, any]
    ) -> bool:
        """
        Determina si se debe mantener el contexto actual o resetearlo.

        Args:
            new_query: Nueva pregunta del usuario
            context_info: Contexto actual

        Returns:
            True si se debe mantener, False si resetear
        """
        # Si no hay contexto, no hay nada que mantener
        if not context_info or not context_info['active_project']:
            return False

        # Detectar si la nueva query menciona el mismo proyecto
        new_projects = self.detect_projects(new_query)

        if new_projects:
            # Verificar si el proyecto detectado es el mismo
            for project_id, project_name, score in new_projects:
                if project_name == context_info['active_project']:
                    return True

        # Detectar cambio de tema explícito
        topic_change_phrases = [
            'ahora sobre', 'cambiando de tema', 'otra pregunta', 'y sobre',
            'pasemos a', 'hablemos de', 'me interesa', 'cuéntame de'
        ]

        query_lower = new_query.lower()
        if any(phrase in query_lower for phrase in topic_change_phrases):
            return False

        # Por defecto, mantener contexto si la confianza es alta
        return context_info['confidence'] > 0.5

    def get_context_summary_for_llm(
        self,
        context_info: Dict[str, any]
    ) -> str:
        """
        Genera un resumen de contexto para añadir al prompt del LLM.

        Args:
            context_info: Información de contexto

        Returns:
            String con resumen para el LLM
        """
        # 🆕 THRESHOLD AUMENTADO: Requiere confianza >= 0.6 (antes 0.3)
        if not context_info or context_info['confidence'] < 0.6:
            return ""

        parts = []

        if context_info['active_project']:
            parts.append(f"El usuario está preguntando sobre: {context_info['active_project']}")

        if context_info['active_topic']:
            topic_readable = context_info['active_topic'].replace('_', ' ')
            parts.append(f"Tema específico: {topic_readable}")

        if parts:
            summary = " | ".join(parts)
            return f"\n⚠️ CONTEXTO CONVERSACIONAL ACTIVO: {summary}\nMantén este contexto en tu respuesta.\n"

        return ""


if __name__ == "__main__":
    # Testing del context tracker
    print("=== TESTING CONTEXT TRACKER ===\n")

    tracker = ContextTracker()

    # Test 1: Detección de proyectos
    print("Test 1: Detección de proyectos")
    test_texts = [
        "¿Cómo funcionan los desayunos solidarios?",
        "¿Puedo ir a la residencia L'Acollida?",
        "Me gustaría hacer refuerzo escolar con niños",
        "¿Qué hacen en kayak para recoger plásticos?"
    ]

    for text in test_texts:
        detected = tracker.detect_projects(text)
        print(f"\nTexto: {text}")
        for project_id, name, score in detected[:2]:
            print(f"  → {name}: {score:.2f}")

    # Test 2: Simulación de conversación
    print("\n\n=== Test 2: Simulación de conversación ===\n")

    class MockMessage:
        def __init__(self, content, msg_type):
            self.content = content
            self.type = msg_type

    # Simular historial de conversación sobre desayunos
    conversation = [
        MockMessage("¿Qué es DNI?", "human"),
        MockMessage("DNI es una asociación de voluntarios...", "ai"),
        MockMessage("¿Cómo funcionan los desayunos solidarios?", "human"),
        MockMessage("Los desayunos se realizan los sábados...", "ai"),
        MockMessage("¿Cuánto dura la actividad?", "human"),
        MockMessage("Dura aproximadamente 1.5 horas...", "ai"),
        MockMessage("¿y quién compra los alimentos?", "human"),  # Query ambigua
    ]

    # Extraer contexto
    context = tracker.extract_context_from_history(conversation[:-1])  # Sin la última pregunta

    print(f"Proyecto activo: {context['active_project']}")
    print(f"Tema activo: {context['active_topic']}")
    print(f"Confianza: {context['confidence']:.2f}")
    print(f"Resumen: {context['summary']}")

    # Enriquecer última query
    last_query = conversation[-1].content
    enriched = tracker.enrich_query_with_context(last_query, context)

    print(f"\nQuery original: {last_query}")
    print(f"Query enriquecida: {enriched}")

    # Test 3: Resumen para LLM
    print("\n\n=== Test 3: Resumen para LLM ===")
    llm_summary = tracker.get_context_summary_for_llm(context)
    print(llm_summary)

    print("\n✅ Tests completados")
